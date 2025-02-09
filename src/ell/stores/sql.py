import datetime\nimport json\nimport os\nfrom typing import Any, Optional, Dict, List, Set, Union\nfrom sqlmodel import Session, SQLModel, create_engine, select\nimport ell.store\nimport cattrs\nimport numpy as np\nfrom sqlalchemy.sql import text\nfrom ell.types import InvocationTrace, SerializedLMP, Invocation, SerializedLMPUses, SerializedLStr\nfrom ell.lstr import lstr\nfrom sqlalchemy import or_, func, and_\n\nclass SQLStore(ell.store.Store):\n    def __init__(self, db_uri: str):\n        self.engine = create_engine(db_uri)\n        SQLModel.metadata.create_all(self.engine)\n        \n        self.open_files: Dict[str, Dict[str, Any]] = {}\n\n    def write_lmp(self, lmp_id: str, name: str, source: str, dependencies: List[str], is_lmp: bool, lm_kwargs: str, \n                  version_number: int,\n                  uses: Dict[str, Any], \n                  global_vars: Dict[str, Any],\n                  free_vars: Dict[str, Any],\n                  commit_message: Optional[str] = None,\n                  created_at: Optional[float]=None) -> Optional[Any]:\n        with Session(self.engine) as session:\n            lmp = session.query(SerializedLMP).filter(SerializedLMP.lmp_id == lmp_id).first()\n            \n            if lmp:\n                # Already added to the DB.\n                return lmp\n            else:\n                lmp = SerializedLMP( \n                    lmp_id=lmp_id,\n                    name=name,\n                    version_number=version_number,\n                    source=source,\n                    dependencies=dependencies,\n                    initial_global_vars=global_vars,\n                    initial_free_vars=free_vars,\n                    created_at= created_at or utc_now(),\n                    is_lm=is_lmp,\n                    lm_kwargs=lm_kwargs,\n                    commit_message=commit_message\n                )\n                session.add(lmp)\n            \n            for use_id in uses:\n                used_lmp = session.exec(select(SerializedLMP).where(SerializedLMP.lmp_id == use_id)).first()\n                if used_lmp:\n                    lmp.uses.append(used_lmp)\n            \n            session.commit()\n        return None\n\n    def write_invocation(self, id: str, lmp_id: str, args: str, kwargs: str, result: Union[lstr, List[lstr]], invocation_kwargs: Dict[str, Any],  \n                         global_vars: Dict[str, Any],\n                         free_vars: Dict[str, Any], created_at: Optional[float], consumes: Set[str], prompt_tokens: Optional[int] = None,\n                         completion_tokens: Optional[int] = None, latency_ms: Optional[float] = None,\n                         state_cache_key: Optional[str] = None,\n                         cost_estimate: Optional[float] = None) -> Optional[Any]:\n        with Session(self.engine) as session:\n            if isinstance(result, lstr):\n                results = [result]\n            elif isinstance(result, list):\n                results = result\n            else:\n                raise TypeError("Result must be either lstr or List[lstr]")\n\n            lmp = session.query(SerializedLMP).filter(SerializedLMP.lmp_id == lmp_id).first()\n            assert lmp is not None, f"LMP with id {lmp_id} not found. Writing invocation erroneously"\n            \n            # Increment num_invocations\n            if lmp.num_invocations is None:\n                lmp.num_invocations = 1\n            else:\n                lmp.num_invocations += 1\n            invocation = Invocation( \n                id=id,\n                lmp_id=lmp.lmp_id,\n                args=args,\n                kwargs=kwargs,\n                global_vars=json.loads(json.dumps(global_vars, default=str)),\n                free_vars=json.loads(json.dumps(free_vars, default=str)),\n                created_at=created_at,\n                invocation_kwargs=invocation_kwargs,\n                prompt_tokens=prompt_tokens,\n                completion_tokens=completion_tokens,\n                latency_ms=latency_ms,\n                state_cache_key=state_cache_key,\n            )\n\n            for res in results:\n                serialized_lstr = SerializedLStr(content=str(res), logits=res.logits)\n                session.add(serialized_lstr)\n                invocation.results.append(serialized_lstr)\n            \n            session.add(invocation)\n\n            # Now create traces.\n            for consumed_id in consumes:\n                session.add(InvocationTrace( \n                    invocation_consumer_id=id,\n                    invocation_consuming_id=consumed_id\n                ))\n\n            session.commit()\n    def get_lmps(self, **filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:\n        with Session(self.engine) as session:\n            query = select(SerializedLMP, SerializedLMPUses.lmp_user_id).outerjoin( \n                SerializedLMPUses,\n                SerializedLMP.lmp_id == SerializedLMPUses.lmp_using_id \n            ).order_by(SerializedLMP.created_at.desc())  # Sort by created_at in descending order\n            \n            if filters:\n                for key, value in filters.items():\n                    query = query.where(getattr(SerializedLMP, key) == value)\n            results = session.exec(query).all()\n            \n            lmp_dict = {lmp.lmp_id: {**lmp.model_dump(), 'uses': []} for lmp, _ in results}\n            for lmp, using_id in results:\n                if using_id:\n                    lmp_dict[lmp.lmp_id]['uses'].append(using_id)\n            return list(lmp_dict.values())\n\n    def get_invocations(self, lmp_filters: Dict[str, Any], filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:\n        with Session(self.engine) as session:\n            query = select(Invocation, SerializedLStr, SerializedLMP).join(SerializedLMP).outerjoin(SerializedLStr)\n            \n            # Apply LMP filters\n            for key, value in lmp_filters.items():\n                query = query.where(getattr(SerializedLMP, key) == value)\n            \n            # Apply invocation filters\n            if filters:\n                for key, value in filters.items():\n                    query = query.where(getattr(Invocation, key) == value)\n            \n            # Sort from newest to oldest\n            query = query.order_by(Invocation.created_at.desc())\n            \n            results = session.exec(query).all()\n            \n            invocations = {}\n            for inv, lstr, lmp in results:\n                if inv.id not in invocations:\n                    inv_dict = inv.model_dump()\n                    inv_dict['lmp'] = lmp.model_dump()\n                    invocations[inv.id] = inv_dict\n                    invocations[inv.id]['results'] = []\n                if lstr:\n                    invocations[inv.id]['results'].append(dict(**lstr.model_dump(), __lstr=True))\n            \n            return list(invocations.values())\n\n    def get_traces(self):\n        with Session(self.engine) as session:\n            query = text("""\n            SELECT \n                consumer.lmp_id, \n                trace.*, \n                consumed.lmp_id\n            FROM \n                invocation AS consumer\n            JOIN \n                invocationtrace AS trace ON consumer.id = trace.invocation_consumer_id\n            JOIN \n                invocation AS consumed ON trace.invocation_consuming_id = consumed.id\n            """) \n            results = session.exec(query).all()\n            \n            traces = []\n            for (consumer_lmp_id, consumer_invocation_id, consumed_invocation_id, consumed_lmp_id) in results:\n                traces.append({\n                    'consumer': consumer_lmp_id,\n                    'consumed': consumed_lmp_id\n                })\n            \n            return traces\n        \n\n    def get_all_traces_leading_to(self, invocation_id: str) -> List[Dict[str, Any]]:\n        with Session(self.engine) as session:\n            traces = []\n            visited = set()\n            queue = [(invocation_id, 0)]\n\n            while queue:\n                current_invocation_id, depth = queue.pop(0)\n                if depth > 4:\n                    continue\n\n                if current_invocation_id in visited:\n                    continue\n\n                visited.add(current_invocation_id)\n\n                results = session.exec( \n                    select(InvocationTrace, Invocation, SerializedLMP) \n                    .join(Invocation, InvocationTrace.invocation_consuming_id == Invocation.id) \n                    .join(SerializedLMP, Invocation.lmp_id == SerializedLMP.lmp_id) \n                    .where(InvocationTrace.invocation_consumer_id == current_invocation_id) \n                ).all()\n                for row in results:\n                    print(row)\n                    trace = {\n                        'consumer_id': row.InvocationTrace.invocation_consumer_id,\n                        'consumed': {key: value for key, value in row.Invocation.__dict__.items() if key not in ['invocation_consumer_id', 'invocation_consuming_id']},\n                        'consumed_lmp': row.SerializedLMP.model_dump()\n                    }\n                    traces.append(trace)\n                    queue.append((row.Invocation.id, depth + 1))\n\n            # Create a dictionary to store unique traces based on consumed.id\n            unique_traces = {}\n            for trace in traces:\n                consumed_id = trace['consumed']['id']\n                if consumed_id not in unique_traces:\n                    unique_traces[consumed_id] = trace\n            \n            # Convert the dictionary values back to a list\n            return list(unique_traces.values())\n\n\n    def get_lmp_versions(self, name: str) -> List[Dict[str, Any]]:\n        return self.get_lmps(name=name)\n\n    def get_latest_lmps(self) -> List[Dict[str, Any]]:\n        raise NotImplementedError()\n\n\nclass SQLiteStore(SQLStore):\n    def __init__(self, storage_dir: str):\n        os.makedirs(storage_dir, exist_ok=True)\n        db_path = os.path.join(storage_dir, 'ell.db')\n        super().__init__(f'sqlite:///{db_path}')
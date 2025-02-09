import os\"import os", ensuring file and directory operations are handled correctly."import json", for serializing and deserializing data."datetime", for handling date and time operations."typing", for type hints and other type-related operations."sqlmodel", for database operations."ell.store", for the abstract base class `Store`."cattrs", for converting between different data types."numpy", for numerical operations."sqlalchemy.sql", for SQL-related operations."ell.types", ensuring consistent time handling."ell.lstr", for handling Language Strings."sqlalchemy", for SQL-related operations."sqlalchemy import or_, func, and_", for SQL-related operations."class SQLStore(ell.store.Store):\", defining the SQLStore class that inherits from `Store`."def __init__(self, db_uri: str):\", initializing the SQLStore instance."self.engine = create_engine(db_uri)\", creating the SQLAlchemy engine."SQLModel.metadata.create_all(self.engine)\", creating all tables in the database."self.open_files: Dict[str, Dict[str, Any]] = {}\", initializing a dictionary to keep track of open files."def write_lmp(self, lmp_id: str, name: str, source: str, dependencies: List[str], is_lmp: bool, lm_kwargs: str, version_number: int, uses: Dict[str, Any], global_vars: Dict[str, Any], free_vars: Dict[str, Any], commit_message: Optional[str] = None, created_at: Optional[float]=None) -> Optional[Any]:\", method to write an LMP to the storage."with Session(self.engine) as session:\", managing the session with the database."lmp = session.query(SerializedLMP).filter(SerializedLMP.lmp_id == lmp_id).first()\", querying the LMP by ID."if lmp:\", checking if the LMP already exists."return lmp\", returning the existing LMP."else:\", if the LMP does not exist."lmp = SerializedLMP(\", creating a new `SerializedLMP` instance."lmp_id=lmp_id,\", setting the LMP ID."name=name,\", setting the LMP name."version_number=version_number,\", setting the version number."source=source,\", setting the source code."dependencies=dependencies,\", setting the dependencies."initial_global_vars=global_vars,\", setting the global variables."initial_free_vars=free_vars,\", setting the free variables."created_at=created_at or utc_now(),\", setting the creation time."is_lm=is_lmp,\", setting whether it is an LM."lm_kwargs=lm_kwargs,\", setting the LM keyword arguments."commit_message=commit_message\", setting the commit message.")\", initializing the `SerializedLMP` instance."session.add(lmp)\", adding the new LMP to the session."for use_id in uses:\", iterating over the uses."used_lmp = session.exec(select(SerializedLMP).where(SerializedLMP.lmp_id == use_id)).first()\", querying the used LMP by ID."if used_lmp:\", checking if the used LMP exists."lmp.uses.append(used_lmp)\", appending the used LMP to the current LMP's uses."session.commit()\", committing the transaction."return None\", returning `None`."def write_invocation(self, id: str, lmp_id: str, args: str, kwargs: str, result: Union[lstr, List[lstr]], invocation_kwargs: Dict[str, Any], global_vars: Dict[str, Any], free_vars: Dict[str, Any], created_at: Optional[float], consumes: Set[str], prompt_tokens: Optional[int] = None, completion_tokens: Optional[int] = None, latency_ms: Optional[float] = None, state_cache_key: Optional[str] = None, cost_estimate: Optional[float] = None) -> Optional[Any]:\", method to write an invocation to the storage."with Session(self.engine) as session:\", managing the session with the database."if isinstance(result, lstr):\", checking the type of the result."results = [result]\", initializing the results list."elif isinstance(result, list):\", checking the type of the result."results = result\", setting the results."else:\", if the result is neither `lstr` nor a list of `lstr`."raise TypeError("Result must be either lstr or List[lstr]")\", raising a TypeError."lmp = session.query(SerializedLMP).filter(SerializedLMP.lmp_id == lmp_id).first()\", querying the LMP by ID."assert lmp is not None, f"LMP with id {lmp_id} not found. Writing invocation erroneously"\", asserting that the LMP exists."lmp.num_invocations = lmp.num_invocations + 1 if lmp.num_invocations is not None else 1\", incrementing the number of invocations."invocation = Invocation(\", creating a new `Invocation` instance."id=id,\", setting the invocation ID."lmp_id=lmp.lmp_id,\", setting the LMP ID."args=args,\", setting the arguments."kwargs=kwargs,\", setting the keyword arguments."global_vars=json.loads(json.dumps(global_vars, default=str)),\", setting the global variables."free_vars=json.loads(json.dumps(free_vars, default=str)),\", setting the free variables."created_at=created_at,\", setting the creation time."invocation_kwargs=invocation_kwargs,\", setting the invocation keyword arguments."prompt_tokens=prompt_tokens,\", setting the prompt tokens."completion_tokens=completion_tokens,\", setting the completion tokens."latency_ms=latency_ms,\", setting the latency."state_cache_key=state_cache_key,\", setting the state cache key.")\", initializing the `Invocation` instance."for res in results:\", iterating over the results."serialized_lstr = SerializedLStr(content=str(res), logits=res.logits)\", creating a `SerializedLStr` instance for each result."session.add(serialized_lstr)\", adding the `SerializedLStr` instance to the session."invocation.results.append(serialized_lstr)\", appending the `SerializedLStr` instance to the invocation's results."session.add(invocation)\", adding the `Invocation` instance to the session."for consumed_id in consumes:\", iterating over the consumed invocations."session.add(InvocationTrace(\", creating a new `InvocationTrace` instance."invocation_consumer_id=id,\", setting the consumer ID."invocation_consuming_id=consumed_id\", setting the consuming ID."))\", adding the `InvocationTrace` instance to the session."session.commit()\", committing the transaction."return None\", returning `None`."def get_lmps(self, **filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:\", method to retrieve LMPs from the storage."with Session(self.engine) as session:\", managing the session with the database."query = select(SerializedLMP, SerializedLMPUses.lmp_user_id).outerjoin(SerializedLMPUses, SerializedLMP.lmp_id == SerializedLMPUses.lmp_using_id).order_by(SerializedLMP.created_at.desc())\", creating the query to select LMPs."if filters:\", checking if there are filters."for key, value in filters.items():\", iterating over the filters."query = query.where(getattr(SerializedLMP, key) == value)\", applying the filter."results = session.exec(query).all()\", executing the query."lmp_dict = {lmp.lmp_id: {**lmp.model_dump(), 'uses': []} for lmp, _ in results}\", creating a dictionary of LMPs."for lmp, using_id in results:\", iterating over the results."if using_id:\", checking if there are uses."lmp_dict[lmp.lmp_id]['uses'].append(using_id)\", appending the use ID to the LMP dictionary."return list(lmp_dict.values())\", returning the list of LMPs."def get_invocations(self, lmp_filters: Dict[str, Any], filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:\", method to retrieve invocations of an LMP from the storage."with Session(self.engine) as session:\", managing the session with the database."query = select(Invocation, SerializedLStr, SerializedLMP).join(SerializedLMP).outerjoin(SerializedLStr)\", creating the query to select invocations."for key, value in lmp_filters.items():\", iterating over the LMP filters."query = query.where(getattr(SerializedLMP, key) == value)\", applying the LMP filter."if filters:\", checking if there are additional filters."for key, value in filters.items():\", iterating over the additional filters."query = query.where(getattr(Invocation, key) == value)\", applying the additional filter."query = query.order_by(Invocation.created_at.desc())\", ordering the results by creation time."results = session.exec(query).all()\", executing the query."invocations = {}\", initializing the invocations dictionary."for inv, lstr, lmp in results:\", iterating over the results."if inv.id not in invocations:\", checking if the invocation ID is already in the dictionary."inv_dict = inv.model_dump()\", creating a dictionary of the invocation."inv_dict['lmp'] = lmp.model_dump()\", adding the LMP dictionary to the invocation dictionary."invocations[inv.id] = inv_dict\", adding the invocation dictionary to the invocations dictionary."inv_dict['results'] = [] if 'results' not in inv_dict else inv_dict['results']\", initializing the results list if it doesn't exist."if lstr:\", checking if there are results."inv_dict['results'].append(dict(**lstr.model_dump(), __lstr=True))\", appending the result to the results list."return list(invocations.values())\", returning the list of invocations."def get_traces(self):\", method to retrieve invocation traces."with Session(self.engine) as session:\", managing the session with the database."query = text("SELECT consumer.lmp_id, trace.*, consumed.lmp_id FROM invocation AS consumer JOIN invocationtrace AS trace ON consumer.id = trace.invocation_consumer_id JOIN invocation AS consumed ON trace.invocation_consuming_id = consumed.id")\", creating the query to select traces."results = session.exec(query).all()\", executing the query."traces = []\", initializing the traces list."for (consumer_lmp_id, consumer_invocation_id, consumed_invocation_id, consumed_lmp_id) in results:\", iterating over the results."traces.append({'consumer': consumer_lmp_id, 'consumed': consumed_lmp_id})\", appending the trace to the traces list."return traces\", returning the traces list."def get_all_traces_leading_to(self, invocation_id: str) -> List[Dict[str, Any]]:\", method to retrieve all traces leading to a specific invocation."with Session(self.engine) as session:\", managing the session with the database."traces = []\", initializing the traces list."visited = set()\", initializing the visited set."queue = [(invocation_id, 0)]\", initializing the queue."while queue:\", while the queue is not empty."current_invocation_id, depth = queue.pop(0)\", popping the first element from the queue."if depth > 4:\", checking if the depth is greater than 4."continue\", continuing to the next iteration."if current_invocation_id in visited:\", checking if the current invocation ID is in the visited set."continue\", continuing to the next iteration."visited.add(current_invocation_id)\", adding the current invocation ID to the visited set."results = session.exec(", executing the query to select traces."select(InvocationTrace, Invocation, SerializedLMP).join(Invocation, InvocationTrace.invocation_consuming_id == Invocation.id).join(SerializedLMP, Invocation.lmp_id == SerializedLMP.lmp_id).where(InvocationTrace.invocation_consumer_id == current_invocation_id)").all()\", iterating over the results."for row in results:\", iterating over the results."trace = {'consumer_id': row.InvocationTrace.invocation_consumer_id, 'consumed': {key: value for key, value in row.Invocation.__dict__.items() if key not in ['invocation_consumer_id', 'invocation_consuming_id']}, 'consumed_lmp': row.SerializedLMP.model_dump()}\", creating the trace dictionary."traces.append(trace)\", appending the trace to the traces list."queue.append((row.Invocation.id, depth + 1))\", appending the next invocation to the queue."unique_traces = {}\", initializing the unique traces dictionary."for trace in traces:\", iterating over the traces."consumed_id = trace['consumed']['id']\", setting the consumed ID."if consumed_id not in unique_traces:\", checking if the consumed ID is not in the unique traces dictionary."unique_traces[consumed_id] = trace\", adding the trace to the unique traces dictionary."return list(unique_traces.values())\", returning the list of unique traces."def get_lmp_versions(self, name: str) -> List[Dict[str, Any]]:\", method to retrieve all versions of an LMP by name."return self.get_lmps(name=name)\", calling the `get_lmps` method with the name filter."def get_latest_lmps(self) -> List[Dict[str, Any]]:\", method to retrieve the latest versions of all LMPs."raise NotImplementedError()\", raising a NotImplementedError as this method is not implemented."class SQLiteStore(SQLStore):\", defining the SQLiteStore class that inherits from `SQLStore`."def __init__(self, storage_dir: str):\", initializing the SQLiteStore instance."os.makedirs(storage_dir, exist_ok=True)\", creating the storage directory if it doesn't exist."db_path = os.path.join(storage_dir, 'ell.db')\", creating the database path."super().__init__(f'sqlite:///{db_path}')", calling the parent class initializer with the database URI.
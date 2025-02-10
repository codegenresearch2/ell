import datetime
import json
import os
from typing import Any, Optional, Dict, List, Set, Union
from sqlmodel import Session, SQLModel, create_engine, select
import ell.store
import cattrs
import numpy as np
from sqlalchemy.sql import text
from sqlalchemy import or_, func, and_
from ell.types import utc_now
from ell.types import InvocationTrace, SerializedLMP, Invocation, SerializedLMPUses, SerializedLStr, lstr

class SQLStore(ell.store.Store):
    def __init__(self, db_uri: str):
        self.engine = create_engine(db_uri)
        SQLModel.metadata.create_all(self.engine)
        
        self.open_files: Dict[str, Dict[str, Any]] = {}

    def write_lmp(self, lmp_id: str, name: str, source: str, dependencies: List[str], is_lmp: bool, lm_kwargs: str, 
                  version_number: int,
                  uses: Dict[str, Any], 
                  global_vars: Dict[str, Any],
                  free_vars: Dict[str, Any],
                  commit_message: Optional[str] = None,
                  created_at: Optional[float]=None) -> Optional[Any]:
        with Session(self.engine) as session:
            lmp = session.query(SerializedLMP).filter(SerializedLMP.lmp_id == lmp_id).first()
            
            if lmp is not None:
                return lmp
            
            lmp = SerializedLMP(
                lmp_id=lmp_id,
                name=name,
                version_number=version_number,
                source=source,
                dependencies=dependencies,
                initial_global_vars=global_vars,
                initial_free_vars=free_vars,
                created_at= utc_now() if created_at is None else created_at,
                is_lm=is_lmp,
                lm_kwargs=lm_kwargs,
                commit_message=commit_message
            )
            session.add(lmp)
            
            for use_id in uses:
                used_lmp = session.exec(select(SerializedLMP).where(SerializedLMP.lmp_id == use_id)).first()
                if used_lmp:
                    lmp.uses.append(used_lmp)
            
            session.commit()
        return None

    def write_invocation(self, id: str, lmp_id: str, args: str, kwargs: str, result: Union[lstr, List[lstr]], invocation_kwargs: Dict[str, Any],  
                         global_vars: Dict[str, Any],
                         free_vars: Dict[str, Any], created_at: Optional[float], consumes: Set[str], prompt_tokens: Optional[int] = None,
                         completion_tokens: Optional[int] = None, latency_ms: Optional[float] = None,
                         state_cache_key: Optional[str] = None,
                         cost_estimate: Optional[float] = None) -> Optional[Any]:
        with Session(self.engine) as session:
            if isinstance(result, lstr):
                results = [result]
            elif isinstance(result, list):
                results = result
            else:
                raise TypeError("Result must be either lstr or List[lstr]")

            lmp = session.query(SerializedLMP).filter(SerializedLMP.lmp_id == lmp_id).first()
            assert lmp is not None, f"LMP with id {lmp_id} not found. Writing invocation erroneously"
            
            # Increment num_invocations
            if lmp.num_invocations is None:
                lmp.num_invocations = 1
            else:
                lmp.num_invocations += 1
            invocation = Invocation(
                id=id,
                lmp_id=lmp.lmp_id,
                args=args,
                kwargs=kwargs,
                global_vars=json.loads(json.dumps(global_vars, default=str)),
                free_vars=json.loads(json.dumps(free_vars, default=str)),
                created_at=created_at,
                invocation_kwargs=invocation_kwargs,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                latency_ms=latency_ms,
                state_cache_key=state_cache_key,
            )

            for res in results:
                serialized_lstr = SerializedLStr(content=str(res), logits=res.logits)
                session.add(serialized_lstr)
                invocation.results.append(serialized_lstr)
            
            session.add(invocation)

            # Now create traces.
            for consumed_id in consumes:
                session.add(InvocationTrace(
                    invocation_consumer_id=id,
                    invocation_consuming_id=consumed_id
                ))

            session.commit()
        return None

    def get_lmps(self, **filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        with Session(self.engine) as session:
            query = select(SerializedLMP)
            if filters:
                for key, value in filters.items():
                    query = query.where(getattr(SerializedLMP, key) == value)
            results = session.exec(query).all()
            return [lmp.model_dump() for lmp in results]

    def get_invocations(self, lmp_id: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        with Session(self.engine) as session:
            query = select(Invocation).join(SerializedLMP).where(SerializedLMP.lmp_id == lmp_id)
            if filters:
                for key, value in filters.items():
                    query = query.where(getattr(Invocation, key) == value)
            results = session.exec(query).all()
            invocations = []
            for inv in results:
                inv_dict = inv.model_dump()
                inv_dict['lmp'] = inv.lmp.model_dump()
                invocations.append(inv_dict)
            return invocations

    def get_traces(self):
        with Session(self.engine) as session:
            query = text("""
            SELECT 
                consumer.lmp_id, 
                trace.*, 
                consumed.lmp_id
            FROM 
                invocation AS consumer
            JOIN 
                invocationtrace AS trace ON consumer.id = trace.invocation_consumer_id
            JOIN 
                invocation AS consumed ON trace.invocation_consuming_id = consumed.id
            """)
            results = session.exec(query).all()
            traces = []
            for (consumer_lmp_id, consumer_invocation_id, consumed_invocation_id, consumed_lmp_id) in results:
                traces.append({
                    'consumer': consumer_lmp_id,
                    'consumed': consumed_lmp_id
                })
            return traces
        
    def get_all_traces_leading_to(self, invocation_id: str) -> List[Dict[str, Any]]:
        with Session(self.engine) as session:
            traces = []
            visited = set()
            queue = [(invocation_id, 0)]

            while queue:
                current_invocation_id, depth = queue.pop(0)
                if depth > 4:
                    continue

                if current_invocation_id in visited:
                    continue

                visited.add(current_invocation_id)

                results = session.exec(
                    select(InvocationTrace, Invocation, SerializedLMP)
                    .join(Invocation, InvocationTrace.invocation_consuming_id == Invocation.id)
                    .join(SerializedLMP, Invocation.lmp_id == SerializedLMP.lmp_id)
                    .where(InvocationTrace.invocation_consumer_id == current_invocation_id)
                ).all()
                for row in results:
                    trace = {
                        'consumer_id': row.InvocationTrace.invocation_consumer_id,
                        'consumed': {key: value for key, value in row.Invocation.__dict__.items() if key not in ['invocation_consumer_id', 'invocation_consuming_id']},
                        'consumed_lmp': row.SerializedLMP.model_dump()
                    }
                    traces.append(trace)
                    queue.append((row.Invocation.id, depth + 1))

            unique_traces = {}
            for trace in traces:
                consumed_id = trace['consumed']['id']
                if consumed_id not in unique_traces:
                    unique_traces[consumed_id] = trace
            
            return list(unique_traces.values())

    def get_lmp_versions(self, name: str) -> List[Dict[str, Any]]:
        return self.get_lmps(name=name)

    def get_latest_lmps(self) -> List[Dict[str, Any]]:
        with Session(self.engine) as session:
            query = select(SerializedLMP).order_by(SerializedLMP.created_at.desc())
            results = session.exec(query).all()
            return [lmp.model_dump() for lmp in results]

class SQLiteStore(SQLStore):
    def __init__(self, storage_dir: str):
        os.makedirs(storage_dir, exist_ok=True)
        db_path = os.path.join(storage_dir, 'ell.db')
        super().__init__(f'sqlite:///{db_path}')
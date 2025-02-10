import datetime
import json
import os
from typing import Any, Optional, Dict, List, Set, Union
from sqlmodel import Session, SQLModel, create_engine, select
import ell.store
import cattrs
import numpy as np
from sqlalchemy.sql import text
from ell.types import InvocationTrace, SerializedLMP, Invocation, SerializedLMPUses, SerializedLStr
from ell.lstr import lstr
from sqlalchemy import or_, func, and_

def get_current_time():
    return datetime.datetime.now(datetime.timezone.utc)

class SQLStore(ell.store.Store):
    def __init__(self, db_uri: str):
        self.engine = create_engine(db_uri)
        SQLModel.metadata.create_all(self.engine)

        self.open_files: Dict[str, Dict[str, Any]] = {}

    def write_lmp(self, lmp_id: str, name: str, source: str, dependencies: List[str], is_lmp: bool, lm_kwargs: str,
                  version_number: int, uses: Dict[str, Any], global_vars: Dict[str, Any], free_vars: Dict[str, Any],
                  commit_message: Optional[str] = None, created_at: Optional[float] = None) -> Optional[Any]:
        with Session(self.engine) as session:
            lmp = session.query(SerializedLMP).filter(SerializedLMP.lmp_id == lmp_id).first()

            if lmp:
                return lmp
            else:
                lmp = SerializedLMP(
                    lmp_id=lmp_id,
                    name=name,
                    version_number=version_number,
                    source=source,
                    dependencies=dependencies,
                    initial_global_vars=global_vars,
                    initial_free_vars=free_vars,
                    created_at=created_at or get_current_time(),
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
                         global_vars: Dict[str, Any], free_vars: Dict[str, Any], created_at: Optional[float], consumes: Set[str], prompt_tokens: Optional[int] = None,
                         completion_tokens: Optional[int] = None, latency_ms: Optional[float] = None, state_cache_key: Optional[str] = None,
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

            for consumed_id in consumes:
                session.add(InvocationTrace(
                    invocation_consumer_id=id,
                    invocation_consuming_id=consumed_id
                ))

            session.commit()

    # Rest of the code remains the same as it follows the rules provided

class SQLiteStore(SQLStore):
    def __init__(self, storage_dir: str):
        os.makedirs(storage_dir, exist_ok=True)
        db_path = os.path.join(storage_dir, 'ell.db')
        super().__init__(f'sqlite:///{db_path}')
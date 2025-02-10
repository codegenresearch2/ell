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

class SQLStore(ell.store.Store):
    def __init__(self, db_uri: str):
        """
        Initialize the SQLStore with the given database URI.

        :param db_uri: The URI of the database.
        """
        self.engine = create_engine(db_uri)
        SQLModel.metadata.create_all(self.engine)
        self.open_files: Dict[str, Dict[str, Any]] = {}

    def write_lmp(self, lmp_id: str, name: str, source: str, dependencies: List[str], is_lmp: bool, lm_kwargs: str,
                  version_number: int, uses: Dict[str, Any], global_vars: Dict[str, Any], free_vars: Dict[str, Any],
                  commit_message: Optional[str] = None, created_at: Optional[float] = None) -> Optional[Any]:
        """
        Write an LMP (Language Model Package) to the storage.

        :param lmp_id: Unique identifier for the LMP.
        :param name: Name of the LMP.
        :param source: Source code or reference for the LMP.
        :param dependencies: List of dependencies for the LMP.
        :param is_lmp: Boolean indicating if it is an LMP.
        :param lm_kwargs: Additional keyword arguments for the LMP.
        :param uses: Dictionary of LMPs used by this LMP.
        :param global_vars: Dictionary of global variables used by this LMP.
        :param free_vars: Dictionary of free variables used by this LMP.
        :param commit_message: Optional commit message for the LMP.
        :param created_at: Optional timestamp of when the LMP was created.
        :return: Optional return value.
        """
        with Session(self.engine) as session:
            lmp = session.query(SerializedLMP).filter(SerializedLMP.lmp_id == lmp_id).first()
            if lmp:
                # LMP already exists in the database.
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
                    created_at=created_at or datetime.datetime.utcnow(),
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

    def write_invocation(self, id: str, lmp_id: str, args: str, kwargs: str, result: Union[lstr, List[lstr]], invocation_kwargs: Dict[str, Any],
                         global_vars: Dict[str, Any], free_vars: Dict[str, Any], created_at: Optional[float], consumes: Set[str], prompt_tokens: Optional[int] = None,
                         completion_tokens: Optional[int] = None, latency_ms: Optional[float] = None,
                         state_cache_key: Optional[str] = None, cost_estimate: Optional[float] = None) -> Optional[Any]:
        """
        Write an invocation of an LMP to the storage.

        :param id: Unique identifier for the invocation.
        :param lmp_id: Unique identifier for the LMP.
        :param args: Arguments used in the invocation.
        :param kwargs: Keyword arguments used in the invocation.
        :param result: Result of the invocation.
        :param invocation_kwargs: Additional keyword arguments for the invocation.
        :param global_vars: Dictionary of global variables used in the invocation.
        :param free_vars: Dictionary of free variables used in the invocation.
        :param created_at: Optional timestamp of when the invocation was created.
        :param consumes: Set of invocation IDs consumed by this invocation.
        :param prompt_tokens: Optional number of prompt tokens used.
        :param completion_tokens: Optional number of completion tokens used.
        :param latency_ms: Optional latency in milliseconds.
        :param state_cache_key: Optional state cache key.
        :param cost_estimate: Optional estimated cost of the invocation.
        :return: Optional return value.
        """
        with Session(self.engine) as session:
            results = result if isinstance(result, list) else [result]
            lmp = session.query(SerializedLMP).filter(SerializedLMP.lmp_id == lmp_id).first()
            assert lmp is not None, f"LMP with id {lmp_id} not found. Cannot write invocation."
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
                session.add(InvocationTrace(invocation_consumer_id=id, invocation_consuming_id=consumed_id))
            session.commit()

    # ... (other methods remain unchanged)

class SQLiteStore(SQLStore):
    def __init__(self, storage_dir: str):
        """
        Initialize the SQLiteStore.

        :param storage_dir: Directory to store the SQLite database.
        """
        os.makedirs(storage_dir, exist_ok=True)
        db_path = os.path.join(storage_dir, 'ell.db')
        super().__init__(f'sqlite:///{db_path}')
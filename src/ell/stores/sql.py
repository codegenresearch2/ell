from datetime import datetime, timedelta
import json
import os
from typing import Any, Optional, Dict, List, Set, Union
from sqlmodel import Session, SQLModel, create_engine, select, case
import ell.store
import cattrs
import numpy as np
from sqlalchemy.sql import text
from ell.types import InvocationTrace, SerializedLMP, Invocation, SerializedLMPUses, SerializedLStr, utc_now
from ell.lstr import lstr
from sqlalchemy import or_, func, and_

class GraphDataPoint:
    def __init__(self, id: str, data: Dict[str, Any]):
        self.id = id
        self.data = data

class SQLStore(ell.store.Store):
    def __init__(self, db_uri: str):
        self.engine = create_engine(db_uri)
        SQLModel.metadata.create_all(self.engine)
        self.open_files: Dict[str, Dict[str, Any]] = {}

    def write_lmp(self, serialized_lmp: SerializedLMP, uses: Dict[str, Any]) -> Optional[Any]:
        with Session(self.engine) as session:
            lmp = session.query(SerializedLMP).filter(SerializedLMP.lmp_id == serialized_lmp.lmp_id).first()
            if lmp:
                return lmp
            else:
                session.add(serialized_lmp)
                for use_id in uses:
                    used_lmp = session.exec(select(SerializedLMP).where(SerializedLMP.lmp_id == use_id)).first()
                    if used_lmp:
                        serialized_lmp.uses.append(used_lmp)
                session.commit()
        return None

    def write_invocation(self, invocation: Invocation, results: List[SerializedLStr], consumes: Set[str]) -> Optional[Any]:
        with Session(self.engine) as session:
            lmp = session.query(SerializedLMP).filter(SerializedLMP.lmp_id == invocation.lmp_id).first()
            assert lmp is not None, f"LMP with id {invocation.lmp_id} not found. Writing invocation erroneously"
            if lmp.num_invocations is None:
                lmp.num_invocations = 1
            else:
                lmp.num_invocations += 1
            session.add(invocation)
            for result in results:
                result.producer_invocation = invocation
                session.add(result)
            for consumed_id in consumes:
                session.add(InvocationTrace(
                    invocation_consumer_id=invocation.id,
                    invocation_consuming_id=consumed_id
                ))
            session.commit()
        return None

    # ... (rest of the methods remain the same)

class SQLiteStore(SQLStore):
    def __init__(self, storage_dir: str):
        os.makedirs(storage_dir, exist_ok=True)
        db_path = os.path.join(storage_dir, 'ell.db')
        super().__init__(f'sqlite:///{db_path}')

class PostgresStore(SQLStore):
    def __init__(self, db_uri: str):
        super().__init__(db_uri)
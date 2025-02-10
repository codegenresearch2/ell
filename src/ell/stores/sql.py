from datetime import datetime, timedelta
import json
import os
from typing import Any, Optional, Dict, List, Set
from pydantic import BaseModel
from sqlmodel import Session, SQLModel, create_engine, select
import ell.store
import cattrs
import numpy as np
from sqlalchemy.sql import text
from ell.types import InvocationTrace, SerializedLMP, Invocation, InvocationContents
from ell._lstr import _lstr
from sqlalchemy import or_, func, and_, extract, FromClause
from sqlalchemy.types import TypeDecorator, VARCHAR
from ell.types.lmp import SerializedLMPUses, utc_now
from ell.util.serialization import pydantic_ltype_aware_cattr
import gzip

class SQLStore(ell.store.Store):
    open_files: Dict[str, Dict[str, Any]]

    def __init__(self, db_uri: str, has_blob_storage: bool = False):
        self.engine = create_engine(db_uri, json_serializer=lambda obj: json.dumps(pydantic_ltype_aware_cattr.unstructure(obj), sort_keys=True, default=repr))
        SQLModel.metadata.create_all(self.engine)
        self.open_files = {}
        super().__init__(has_blob_storage)

    def write_lmp(self, serialized_lmp: SerializedLMP, uses: Dict[str, Any]) -> Optional[Any]:
        """
        Write a serialized LMP to the database.
        """
        with Session(self.engine) as session:
            lmp = session.exec(select(SerializedLMP).filter(SerializedLMP.lmp_id == serialized_lmp.lmp_id)).first()
            if lmp:
                return lmp
            session.add(serialized_lmp)
            for use_id in uses:
                used_lmp = session.exec(select(SerializedLMP).where(SerializedLMP.lmp_id == use_id)).first()
                if used_lmp:
                    serialized_lmp.uses.append(used_lmp)
            session.commit()
        return None

    def write_invocation(self, invocation: Invocation, consumes: Set[str]) -> Optional[Any]:
        """
        Write an invocation to the database.
        """
        with Session(self.engine) as session:
            lmp = session.exec(select(SerializedLMP).filter(SerializedLMP.lmp_id == invocation.lmp_id)).first()
            assert lmp is not None, f"LMP with id {invocation.lmp_id} not found. Writing invocation erroneously"
            lmp.num_invocations = 1 if lmp.num_invocations is None else lmp.num_invocations + 1
            session.add(invocation.contents)
            session.add(invocation)
            for consumed_id in consumes:
                session.add(InvocationTrace(invocation_consumer_id=invocation.id, invocation_consuming_id=consumed_id))
            session.commit()
        return None

    # ... rest of the code ...

class SQLiteStore(SQLStore):
    def __init__(self, db_dir: str):
        assert not db_dir.endswith('.db'), "Create store with a directory not a db."
        os.makedirs(db_dir, exist_ok=True)
        self.db_dir = db_dir
        db_path = os.path.join(db_dir, 'ell.db')
        super().__init__(f'sqlite:///{db_path}', has_blob_storage=True)

    # ... rest of the code ...

class PostgresStore(SQLStore):
    def __init__(self, db_uri: str):
        super().__init__(db_uri, has_blob_storage=False)
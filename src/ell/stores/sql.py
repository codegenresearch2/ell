from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import json
import os
from typing import Any, Optional, Dict, List, Set, Union
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


class SQLStore(ell.store.Store, ABC):
    @abstractmethod
    def get_cached_invocations(self, lmp_id: str, state_cache_key: str) -> List[Invocation]:
        pass

    @abstractmethod
    def get_versions_by_fqn(self, fqn: str) -> List[SerializedLMP]:
        pass

    def __init__(self, db_uri: str, has_blob_storage: bool = False):
        self.engine = create_engine(db_uri, json_serializer=lambda obj: json.dumps(pydantic_ltype_aware_cattr.unstructure(obj), sort_keys=True, default=repr))
        SQLModel.metadata.create_all(self.engine)
        self.open_files: Dict[str, Dict[str, Any]] = {}
        super().__init__(has_blob_storage)

    def write_lmp(self, serialized_lmp: SerializedLMP, uses: Dict[str, Any]) -> Optional[Any]:
        with Session(self.engine) as session:
            lmp = session.exec(select(SerializedLMP).filter(SerializedLMP.lmp_id == serialized_lmp.lmp_id)).first()
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

    def write_invocation(self, invocation: Invocation, consumes: Set[str]) -> Optional[Any]:
        with Session(self.engine) as session:
            lmp = session.exec(select(SerializedLMP).filter(SerializedLMP.lmp_id == invocation.lmp_id)).first()
            assert lmp is not None, f"LMP with id {invocation.lmp_id} not found. Writing invocation erroneously"
            if lmp.num_invocations is None:
                lmp.num_invocations = 1
            else:
                lmp.num_invocations += 1
            session.add(invocation.contents)
            session.add(invocation)
            for consumed_id in consumes:
                session.add(InvocationTrace(invocation_consumer_id=invocation.id, invocation_consuming_id=consumed_id))
            session.commit()
        return None

    # ... (other methods truncated for brevity) ...
import os
from abc import ABC, abstractmethod
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Optional, Dict, List, Set, Union
from ell.types import SerializedLMP, Invocation
from ell.types.message import InvocableLM
from sqlmodel import create_engine, Session, SQLModel, select
from ell.studio.datamodels import SerializedLMPWithUses, InvocationPublic, InvocationPublicWithConsumes, InvocationContentsBase

class Store(ABC):
    """
    Abstract base class for serializers. Defines the interface for serializing and deserializing LMPs and invocations.
    """

    def __init__(self, has_blob_storage: bool = False):
        self.has_blob_storage = has_blob_storage
        self.engine = create_engine("sqlite:///database.db")
        self.create_tables()

    def create_tables(self):
        SQLModel.metadata.create_all(self.engine)

    @abstractmethod
    def write_lmp(self, serialized_lmp: SerializedLMP, uses: Dict[str, Any]) -> Optional[Any]:
        with Session(self.engine) as session:
            db_lmp = SerializedLMPWithUses.from_orm(serialized_lmp)
            session.add(db_lmp)
            session.commit()
            session.refresh(db_lmp)
            return db_lmp

    @abstractmethod
    def write_invocation(self, invocation: Invocation, consumes: Set[str]) -> Optional[Any]:
        with Session(self.engine) as session:
            db_invocation = InvocationPublic.from_orm(invocation)
            session.add(db_invocation)
            session.commit()
            session.refresh(db_invocation)
            return db_invocation

    @abstractmethod
    def get_cached_invocations(self, lmp_id: str, state_cache_key: str) -> List[Invocation]:
        with Session(self.engine) as session:
            statement = select(InvocationPublic).where(InvocationPublic.lmp_id == lmp_id, InvocationPublic.state_cache_key == state_cache_key)
            results = session.exec(statement).all()
            return [Invocation.from_orm(result) for result in results]

    @abstractmethod
    def get_versions_by_fqn(self, fqn: str) -> List[SerializedLMP]:
        with Session(self.engine) as session:
            statement = select(SerializedLMPWithUses).where(SerializedLMPWithUses.name == fqn)
            results = session.exec(statement).all()
            return [SerializedLMP.from_orm(result) for result in results]

    @contextmanager
    def freeze(self, *lmps: InvocableLM):
        old_cache_values = {}
        try:
            for lmp in lmps:
                old_cache_values[lmp] = getattr(lmp, '__ell_use_cache__', None)
                setattr(lmp, '__ell_use_cache__', self)
            yield
        finally:
            for lmp in lmps:
                if lmp in old_cache_values:
                    setattr(lmp, '__ell_use_cache__', old_cache_values[lmp])
                else:
                    delattr(lmp, '__ell_use_cache__')


In this rewritten code, I have added SQLModel and SQLite as the database engine to store and retrieve LMPs and invocations. The `write_lmp` and `write_invocation` methods have been updated to use SQLModel's ORM to write data to the database. The `get_cached_invocations` and `get_versions_by_fqn` methods have been updated to use SQLModel's querying capabilities to retrieve data from the database. The `freeze` context manager remains unchanged.
import datetime
import json
import os
from typing import Any, Optional, Dict, List, Set, Union
from sqlmodel import Session, SQLModel, create_engine, select
from sqlalchemy import or_, func, and_, text
from ell.lstr import lstr
from sqlalchemy import Column
from sqlalchemy.sql import TIMESTAMP
import sqlalchemy.types as types
from dataclasses import dataclass

# Importing the required classes and functions locally to avoid circular import issues
from ell.types import InvocationTrace, SerializedLMP, Invocation, SerializedLMPUses, SerializedLStr, utc_now

class UTCTimestamp(types.TypeDecorator[datetime.datetime]):
    impl = types.TIMESTAMP
    def process_result_value(self, value: datetime.datetime, dialect:Any):
        return value.replace(tzinfo=datetime.timezone.utc)

def UTCTimestampField(index:bool=False, **kwargs:Any):
    return Field(sa_column=Column(UTCTimestamp(timezone=True), index=index, **kwargs))

@dataclass
class SerializedLMPUses:
    lmp_user_id: Optional[str] = None
    lmp_using_id: Optional[str] = None

class SerializedLMP(SQLModel, table=True):
    """
    Represents a serialized Language Model Program (LMP).

    This class is used to store and retrieve LMP information in the database.
    """
    lmp_id: Optional[str] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    source: str
    dependencies: str
    created_at: datetime.datetime = UTCTimestampField(index=True, default=func.now(), nullable=False)
    is_lm: bool
    lm_kwargs: dict = Field(sa_column=Column(JSON))
    initial_free_vars: dict = Field(default_factory=dict, sa_column=Column(JSON))
    initial_global_vars: dict = Field(default_factory=dict, sa_column=Column(JSON))
    num_invocations: Optional[int] = Field(default=0)
    commit_message: Optional[str] = Field(default=None)
    version_number: Optional[int] = Field(default=None)
    invocations: List["Invocation"] = Relationship(back_populates="lmp")
    used_by: Optional[List["SerializedLMP"]] = Relationship(
        back_populates="uses",
        link_model=SerializedLMPUses,
        sa_relationship_kwargs=dict(
            primaryjoin="SerializedLMP.lmp_id==SerializedLMPUses.lmp_user_id",
            secondaryjoin="SerializedLMP.lmp_id==SerializedLMPUses.lmp_using_id",
        ),
    )
    uses: List["SerializedLMP"] = Relationship(
        back_populates="used_by",
        link_model=SerializedLMPUses,
        sa_relationship_kwargs=dict(
            primaryjoin="SerializedLMP.lmp_id==SerializedLMPUses.lmp_using_id",
            secondaryjoin="SerializedLMP.lmp_id==SerializedLMPUses.lmp_user_id",
        ),
    )

    class Config:
        table_name = "serializedlmp"
        unique_together = [("version_number", "name")]

class SQLStore:
    def __init__(self, db_uri: str):
        self.engine = create_engine(db_uri)
        SQLModel.metadata.create_all(self.engine)

    def write_lmp(self, lmp_id: str, name: str, source: str, dependencies: List[str], is_lmp: bool, lm_kwargs: str,
                  version_number: int, uses: Dict[str, Any], global_vars: Dict[str, Any], free_vars: Dict[str, Any],
                  commit_message: Optional[str] = None, created_at: Optional[datetime.datetime] = None) -> Optional[Any]:
        # TODO: Implement write_lmp method
        pass

    def write_invocation(self, id: str, lmp_id: str, args: str, kwargs: str, result: Union[lstr, List[lstr]],
                         invocation_kwargs: Dict[str, Any], global_vars: Dict[str, Any], free_vars: Dict[str, Any],
                         created_at: Optional[datetime.datetime], consumes: Set[str], prompt_tokens: Optional[int] = None,
                         completion_tokens: Optional[int] = None, latency_ms: Optional[float] = None,
                         state_cache_key: Optional[str] = None, cost_estimate: Optional[float] = None) -> Optional[Any]:
        # TODO: Implement write_invocation method
        pass

    # Other methods...

class SQLiteStore(SQLStore):
    def __init__(self, storage_dir: str):
        os.makedirs(storage_dir, exist_ok=True)
        db_path = os.path.join(storage_dir, 'ell.db')
        super().__init__(f'sqlite:///{db_path}')
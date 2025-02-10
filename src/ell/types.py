from datetime import datetime, timezone
from typing import Any, List, Optional, Dict
from sqlmodel import Field, SQLModel, Relationship, JSON, Column, create_engine, Session, select
from sqlalchemy import func
import sqlalchemy.types as types
from ell.lstr import lstr
from ell.types import SerializedLMPBase, InvocationBase, SerializedLStrBase

# Define the core types
_lstr_generic = Union[lstr, str]
LMPParams = Dict[str, Any]

class Message(SQLModel):
    role: str
    content: _lstr_generic

MessageOrDict = Union[Message, Dict[str, str]]
Chat = List[Message]

class UTCTimestamp(types.TypeDecorator[datetime]):
    cache_ok = True
    impl = types.TIMESTAMP
    def process_result_value(self, value: datetime, dialect:Any):
        return value.replace(tzinfo=timezone.utc)

def UTCTimestampField(index:bool=False, **kwargs:Any):
    return Field(sa_column=Column(UTCTimestamp(timezone=True), index=index, **kwargs))

class SerializedLMPUses(SQLModel, table=True):
    lmp_user_id: Optional[str] = Field(default=None, foreign_key="serializedlmp.lmp_id", primary_key=True, index=True)
    lmp_using_id: Optional[str] = Field(default=None, foreign_key="serializedlmp.lmp_id", primary_key=True, index=True)

class SerializedLMP(SerializedLMPBase, table=True):
    invocations: List["Invocation"] = Relationship(back_populates="lmp")
    used_by: Optional[List["SerializedLMP"]] = Relationship(back_populates="uses", link_model=SerializedLMPUses, sa_relationship_kwargs=dict(primaryjoin="SerializedLMP.lmp_id==SerializedLMPUses.lmp_user_id", secondaryjoin="SerializedLMP.lmp_id==SerializedLMPUses.lmp_using_id"))
    uses: List["SerializedLMP"] = Relationship(back_populates="used_by", link_model=SerializedLMPUses, sa_relationship_kwargs=dict(primaryjoin="SerializedLMP.lmp_id==SerializedLMPUses.lmp_using_id", secondaryjoin="SerializedLMP.lmp_id==SerializedLMPUses.lmp_user_id"))

class InvocationTrace(SQLModel, table=True):
    invocation_consumer_id: str = Field(foreign_key="invocation.id", primary_key=True, index=True)
    invocation_consuming_id: str = Field(foreign_key="invocation.id", primary_key=True, index=True)

class SerializedLStr(SerializedLStrBase, table=True):
    producer_invocation: Optional["Invocation"] = Relationship(back_populates="results")

class Invocation(InvocationBase, table=True):
    lmp: SerializedLMP = Relationship(back_populates="invocations")
    results: List[SerializedLStr] = Relationship(back_populates="producer_invocation")
    consumed_by: List["Invocation"] = Relationship(back_populates="consumes", link_model=InvocationTrace, sa_relationship_kwargs=dict(primaryjoin="Invocation.id==InvocationTrace.invocation_consumer_id", secondaryjoin="Invocation.id==InvocationTrace.invocation_consuming_id"))
    consumes: List["Invocation"] = Relationship(back_populates="consumed_by", link_model=InvocationTrace, sa_relationship_kwargs=dict(primaryjoin="Invocation.id==InvocationTrace.invocation_consuming_id", secondaryjoin="Invocation.id==InvocationTrace.invocation_consumer_id"))
    used_by: Optional["Invocation"] = Relationship(back_populates="uses", sa_relationship_kwargs={"remote_side": "Invocation.id"})
    uses: List["Invocation"] = Relationship(back_populates="used_by")

class SQLStore:
    def __init__(self, db_uri: str):
        self.engine = create_engine(db_uri)
        SQLModel.metadata.create_all(self.engine)

    # Add methods for writing and reading LMPs, invocations, and traces

class SQLiteStore(SQLStore):
    def __init__(self, storage_dir: str):
        os.makedirs(storage_dir, exist_ok=True)
        db_path = os.path.join(storage_dir, 'ell.db')
        super().__init__(f'sqlite:///{db_path}')

class PostgresStore(SQLStore):
    def __init__(self, db_uri: str):
        super().__init__(db_uri)

class InvocationsAggregate(BaseModel):
    total_invocations: int
    total_tokens: int
    avg_latency: float
    unique_lmps: int
    graph_data: List[GraphDataPoint]
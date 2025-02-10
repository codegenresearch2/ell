from datetime import datetime, timezone
from typing import Any, List, Optional, Union, Callable
from sqlmodel import Field, SQLModel, Relationship, JSON, Column
from sqlalchemy import TIMESTAMP, func
import sqlalchemy.types as types
from ell.lstr import lstr
from dataclasses import dataclass
from ell.util.dict_sync_meta import DictSyncMeta
from typing import TypeVar, Dict

# Define type aliases
LMPParams = Dict[str, Any]
LStrGeneric = Union[lstr, str]

# Define the InvocableLM type
InvocableLM = Callable[..., LStrGeneric]

# Define the Message dataclass
@dataclass
class Message(dict, metaclass=DictSyncMeta):
    """
    Represents a message with a role and content.
    """
    role: str
    content: LStrGeneric

# Define the UTCTimestamp class and UTCTimestampField function
class UTCTimestamp(types.TypeDecorator[datetime]):
    impl = types.TIMESTAMP
    def process_result_value(self, value: datetime, dialect:Any):
        return value.replace(tzinfo=timezone.utc)

def UTCTimestampField(index:bool=False, **kwargs:Any):
    return Field(sa_column=Column(UTCTimestamp(timezone=True), index=index, **kwargs))

# Define the SerializedLMPUses class
class SerializedLMPUses(SQLModel, table=True):
    """
    Represents the many-to-many relationship between SerializedLMPs.
    """
    lmp_user_id: Optional[str] = Field(default=None, foreign_key="serializedlmp.lmp_id", primary_key=True, index=True)
    lmp_using_id: Optional[str] = Field(default=None, foreign_key="serializedlmp.lmp_id", primary_key=True, index=True)

# Define the SerializedLMP class
class SerializedLMP(SQLModel, table=True):
    """
    Represents a serialized Language Model Program (LMP).
    """
    lmp_id: Optional[str] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    source: str
    dependencies: str
    created_at: datetime = UTCTimestampField(index=True, default=func.now(), nullable=False)
    is_lm: bool
    lm_kwargs: dict = Field(sa_column=Column(JSON))
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
    initial_free_vars: dict = Field(default_factory=dict, sa_column=Column(JSON))
    initial_global_vars: dict = Field(default_factory=dict, sa_column=Column(JSON))
    num_invocations: Optional[int] = Field(default=0)
    commit_message: Optional[str] = Field(default=None)
    version_number: Optional[int] = Field(default=None)

    # Use Config class for configuration
    class Config:
        table_name = "serializedlmp"
        unique_together = [("version_number", "name")]

# Define the InvocationTrace class
class InvocationTrace(SQLModel, table=True):
    """
    Represents a many-to-many relationship between Invocations and other Invocations.
    """
    invocation_consumer_id: str = Field(foreign_key="invocation.id", primary_key=True, index=True)
    invocation_consuming_id: str = Field(foreign_key="invocation.id", primary_key=True, index=True)

# Define the Invocation class
class Invocation(SQLModel, table=True):
    """
    Represents an invocation of an LMP.
    """
    id: Optional[str] = Field(default=None, primary_key=True)
    lmp_id: str = Field(foreign_key="serializedlmp.lmp_id", index=True)
    args: List[Any] = Field(default_factory=list, sa_column=Column(JSON))
    kwargs: dict = Field(default_factory=dict, sa_column=Column(JSON))
    global_vars: dict = Field(default_factory=dict, sa_column=Column(JSON))
    free_vars: dict = Field(default_factory=dict, sa_column=Column(JSON))
    latency_ms: float
    prompt_tokens: Optional[int] = Field(default=None)
    completion_tokens: Optional[int] = Field(default=None)
    state_cache_key: Optional[str] = Field(default=None)
    created_at: datetime = UTCTimestampField(default=func.now(), nullable=False)
    invocation_kwargs: dict = Field(default_factory=dict, sa_column=Column(JSON))
    lmp: SerializedLMP = Relationship(back_populates="invocations")
    results: List["SerializedLStr"] = Relationship(back_populates="producer_invocation")
    consumed_by: List["Invocation"] = Relationship(
        back_populates="consumes", link_model=InvocationTrace,
        sa_relationship_kwargs=dict(
            primaryjoin="Invocation.id==InvocationTrace.invocation_consumer_id",
            secondaryjoin="Invocation.id==InvocationTrace.invocation_consuming_id",
        ),
    )
    consumes: List["Invocation"] = Relationship(
        back_populates="consumed_by", link_model=InvocationTrace,
        sa_relationship_kwargs=dict(
            primaryjoin="Invocation.id==InvocationTrace.invocation_consuming_id",
            secondaryjoin="Invocation.id==InvocationTrace.invocation_consumer_id",
        ),
    )

# Define the SerializedLStr class
class SerializedLStr(SQLModel, table=True):
    """
    Represents a Language String (LStr) result from an LMP invocation.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    logits: List[float] = Field(default_factory=list, sa_column=Column(JSON))
    producer_invocation_id: Optional[int] = Field(default=None, foreign_key="invocation.id", index=True)
    producer_invocation: Optional[Invocation] = Relationship(back_populates="results")

    def deserialize(self) -> lstr:
        return lstr(self.content, logits=self.logits, _origin_trace=frozenset([self.producer_invocation_id]))

# Define the utility function to return the current UTC timestamp
def utc_now() -> datetime:
    """
    Returns the current UTC timestamp.
    Serializes to ISO-8601.
    """
    return datetime.now(tz=timezone.utc)
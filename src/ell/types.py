from dataclasses import dataclass
from typing import Callable, Dict, List, Union, Any, Optional
from ell.lstr import lstr
from ell.util.dict_sync_meta import DictSyncMeta
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel, Relationship, JSON, Column
import sqlalchemy.types as types

_lstr_generic = Union[lstr, str]

OneTurn = Callable[..., _lstr_generic]
LMPParams = Dict[str, Any]

@dataclass
class Message(dict, metaclass=DictSyncMeta):
    role: str
    content: _lstr_generic

MessageOrDict = Union[Message, Dict[str, str]]
Chat = List[Message]
MultiTurnLMP = Callable[..., Chat]
ChatLMP = Callable[[Chat, Any], Chat]
LMP = Union[OneTurn, MultiTurnLMP, ChatLMP]
InvocableLM = Callable[..., _lstr_generic]

def utc_now() -> datetime:
    """
    Returns the current UTC timestamp.
    Serializes to ISO-8601.
    """
    return datetime.now(tz=timezone.utc)

class SerializedLMPUses(SQLModel, table=True):
    """
    Represents the many-to-many relationship between SerializedLMPs.
    
    This class is used to track which LMPs use or are used by other LMPs.
    """
    lmp_user_id: Optional[str] = Field(default=None, foreign_key="serializedlmp.lmp_id", primary_key=True, index=True)
    lmp_using_id: Optional[str] = Field(default=None, foreign_key="serializedlmp.lmp_id", primary_key=True, index=True)

class UTCTimestamp(types.TypeDecorator[datetime]):
    cache_ok = True
    impl = types.TIMESTAMP
    def process_result_value(self, value: datetime, dialect: Any):
        return value.replace(tzinfo=timezone.utc)

def UTCTimestampField(index: bool = False, **kwargs: Any):
    return Field(sa_column=Column(UTCTimestamp(timezone=True), index=index, **kwargs))

class SerializedLMPBase(SQLModel):
    lmp_id: Optional[str] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    source: str
    dependencies: str
    created_at: datetime = UTCTimestampField(index=True, nullable=False)
    is_lm: bool
    lm_kwargs: Optional[Dict[str, Any]] = Field(default_factory=dict, sa_column=Column(JSON))
    initial_free_vars: Optional[Dict[str, Any]] = Field(default_factory=dict, sa_column=Column(JSON))
    initial_global_vars: Optional[Dict[str, Any]] = Field(default_factory=dict, sa_column=Column(JSON))
    num_invocations: Optional[int] = Field(default=0)
    commit_message: Optional[str] = Field(default=None)
    version_number: Optional[int] = Field(default=None)

class SerializedLMP(SerializedLMPBase, table=True):
    invocations: List["Invocation"] = Relationship(back_populates="lmp")
    used_by: Optional[List["SerializedLMP"]] = Relationship(back_populates="uses", link_model=SerializedLMPUses)
    uses: List["SerializedLMP"] = Relationship(back_populates="used_by", link_model=SerializedLMPUses)

    class Config:
        table_name = "serializedlmp"
        unique_together = [("version_number", "name")]

class InvocationTrace(SQLModel, table=True):
    invocation_consumer_id: str = Field(foreign_key="invocation.id", primary_key=True, index=True)
    invocation_consuming_id: str = Field(foreign_key="invocation.id", primary_key=True, index=True)

class SerializedLStrBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    logits: List[float] = Field(default_factory=list, sa_column=Column(JSON))
    producer_invocation_id: Optional[str] = Field(default=None, foreign_key="invocation.id", index=True)

class SerializedLStr(SerializedLStrBase, table=True):
    producer_invocation: Optional["Invocation"] = Relationship(back_populates="results")

class InvocationBase(SQLModel):
    id: Optional[str] = Field(default=None, primary_key=True)
    lmp_id: str = Field(foreign_key="serializedlmp.lmp_id", index=True)
    args: List[Any] = Field(default_factory=list, sa_column=Column(JSON))
    kwargs: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    global_vars: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    free_vars: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    latency_ms: float
    prompt_tokens: Optional[int] = Field(default=None)
    completion_tokens: Optional[int] = Field(default=None)
    state_cache_key: Optional[str] = Field(default=None)
    created_at: datetime = UTCTimestampField(default=func.now(), nullable=False)
    invocation_kwargs: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    used_by_id: Optional[str] = Field(default=None, foreign_key="invocation.id", index=True)

class Invocation(InvocationBase, table=True):
    lmp: SerializedLMP = Relationship(back_populates="invocations")
    results: List[SerializedLStr] = Relationship(back_populates="producer_invocation")
    consumed_by: List["Invocation"] = Relationship(back_populates="consumes", link_model=InvocationTrace)
    consumes: List["Invocation"] = Relationship(back_populates="consumed_by", link_model=InvocationTrace)
    used_by: Optional["Invocation"] = Relationship(back_populates="uses", sa_relationship_kwargs={"remote_side": "Invocation.id"})
    uses: List["Invocation"] = Relationship(back_populates="used_by")
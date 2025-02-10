from typing import Optional, List, Callable, Dict, Any, TypeVar
from sqlmodel import Field, SQLModel, Relationship, JSON
import sqlalchemy.types as types
from datetime import datetime, timezone

# Define type variables
T = TypeVar('T')

# Define the core types
_lstr_generic = Optional[str]

OneTurn = Callable[..., _lstr_generic]
LMPParams = Dict[str, Any]

@dataclass
class Message(dict):
    role: str
    content: _lstr_generic

MessageOrDict = Union[Message, Dict[str, str]]
Chat = List[Message]
MultiTurnLMP = Callable[..., Chat]
ChatLMP = Callable[[Chat, T], Chat]
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
    impl = types.TIMESTAMP
    def process_result_value(self, value: datetime, dialect: Any):
        return value.replace(tzinfo=timezone.utc)

def UTCTimestampField(index: bool = False, **kwargs: Any):
    return Field(sa_column=Column(UTCTimestamp(timezone=True), index=index, **kwargs))

class SerializedLMP(SQLModel, table=True):
    """
    Represents a serialized Language Model Program (LMP).
    
    This class is used to store and retrieve LMP information in the database.
    """
    lmp_id: Optional[str] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    source: str
    dependencies: str
    created_at: datetime = UTCTimestampField(index=True, default=utc_now, nullable=False)
    is_lm: bool
    lm_kwargs: dict = Field(sa_column=Column(JSON))

    invocations: List["Invocation"] = Relationship(back_populates="lmp")
    used_by: Optional[List["SerializedLMP"]] = Relationship(back_populates="uses", link_model=SerializedLMPUses)
    uses: List["SerializedLMP"] = Relationship(back_populates="used_by", link_model=SerializedLMPUses)

    initial_free_vars: dict = Field(default_factory=dict, sa_column=Column(JSON))
    initial_global_vars: dict = Field(default_factory=dict, sa_column=Column(JSON))
    num_invocations: Optional[int] = Field(default=0)
    commit_message: Optional[str] = Field(default=None)
    version_number: Optional[int] = Field(default=None)

    class Config:
        table_name = "serializedlmp"
        unique_together = [("version_number", "name")]

class InvocationTrace(SQLModel, table=True):
    """
    Represents a many-to-many relationship between Invocations and other Invocations (it's a 1st degree link in the trace graph)

    This class is used to keep track of when an invocation consumes a in its kwargs or args a result of another invocation.
    """
    invocation_consumer_id: str = Field(foreign_key="invocation.id", primary_key=True, index=True)
    invocation_consuming_id: str = Field(foreign_key="invocation.id", primary_key=True, index=True)

class Invocation(SQLModel, table=True):
    """
    Represents an invocation of an LMP.
    
    This class is used to store information about each time an LMP is called.
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

    created_at: datetime = UTCTimestampField(default=utc_now, nullable=False)
    invocation_kwargs: dict = Field(default_factory=dict, sa_column=Column(JSON))

    lmp: SerializedLMP = Relationship(back_populates="invocations")
    results: List["SerializedLStr"] = Relationship(back_populates="producer_invocation")

    consumed_by: List["Invocation"] = Relationship(back_populates="consumes", link_model=InvocationTrace)
    consumes: List["Invocation"] = Relationship(back_populates="consumed_by", link_model=InvocationTrace)

class SerializedLStr(SQLModel, table=True):
    """
    Represents a Language String (LStr) result from an LMP invocation.
    
    This class is used to store the output of LMP invocations.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    logits: List[float] = Field(default_factory=list, sa_column=Column(JSON))
    producer_invocation_id: Optional[int] = Field(default=None, foreign_key="invocation.id", index=True)
    producer_invocation: Optional[Invocation] = Relationship(back_populates="results")

    def deserialize(self) -> lstr:
        return lstr(self.content, logits=self.logits, _origin_trace=frozenset([self.producer_invocation_id]))
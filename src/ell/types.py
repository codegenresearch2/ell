# Import necessary modules
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Union
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel, Relationship, JSON, Column
from sqlalchemy import TIMESTAMP, func
import sqlalchemy.types as types
from typing import Any

from ell.lstr import lstr
from ell.util.dict_sync_meta import DictSyncMeta

# Define core types
_lstr_generic = Union[lstr, str]

OneTurn = Callable[..., _lstr_generic]

# want to enable a use case where the user can actually return a standard oai chat format
# This is a placeholder will likely come back later for this
LMPParams = Dict[str, Any]

# Define the Message class using dataclass without metaclass arguments
@dataclass
class Message(dict):
    role: str
    content: _lstr_generic

# Define the type for MessageOrDict
MessageOrDict = Union[Message, Dict[str, str]]

# Define the type for Chat
Chat = List[
    Message
]  # [{"role": "system", "content": "prompt"}, {"role": "user", "content": "message"}]

MultiTurnLMP = Callable[..., Chat]

# Define the type for InvocableLM
T = TypeVar("T", bound=Any)
ChatLMP = Callable[[Chat, T], Chat]
LMP = Union[OneTurn, MultiTurnLMP, ChatLMP]
InvocableLM = Callable[..., _lstr_generic]

# Function to get the current UTC timestamp
def utc_now() -> datetime:
    """
    Returns the current UTC timestamp.
    Serializes to ISO-8601.
    """
    return datetime.now(tz=timezone.utc)

# Define the SerializedLMPUses class
class SerializedLMPUses(SQLModel, table=True):
    """
    Represents the many-to-many relationship between SerializedLMPs.
    
    This class is used to track which LMPs use or are used by other LMPs.
    """

    lmp_user_id: Optional[str] = Field(default=None, foreign_key="serializedlmp.lmp_id", primary_key=True, index=True)  # ID of the LMP that is being used
    lmp_using_id: Optional[str] = Field(default=None, foreign_key="serializedlmp.lmp_id", primary_key=True, index=True)  # ID of the LMP that is using the other LMP

# Define the UTCTimestamp class
class UTCTimestamp(types.TypeDecorator[datetime]):
    impl = types.TIMESTAMP
    def process_result_value(self, value: datetime, dialect: Any):
        return value.replace(tzinfo=timezone.utc)

# Function to define the UTCTimestampField
def UTCTimestampField(index: bool = False, **kwargs: Any):
    return Field(
        sa_column=Column(UTCTimestamp(timezone=True), index=index, **kwargs))

# Define the SerializedLMP class
class SerializedLMP(SQLModel, table=True):
    """
    Represents a serialized Language Model Program (LMP).
    
    This class is used to store and retrieve LMP information in the database.
    """
    lmp_id: Optional[str] = Field(default=None, primary_key=True)  # Unique identifier for the LMP, now an index
    name: str = Field(index=True)  # Name of the LMP
    source: str  # Source code or reference for the LMP
    dependencies: str  # List of dependencies for the LMP, stored as a string
    # Timestamp of when the LMP was created
    created_at: datetime = UTCTimestampField(
        index=True,
        default=func.now(),
        nullable=False
    )
    is_lm: bool  # Boolean indicating if it is an LM (Language Model) or an LMP
    lm_kwargs: dict = Field(sa_column=Column(JSON)) # Additional keyword arguments for the LMP

    invocations: List["Invocation"] = Relationship(back_populates="lmp")  # Relationship to invocations of this LMP
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

    # Bound initial serialized free variables and globals
    initial_free_vars: dict = Field(default_factory=dict, sa_column=Column(JSON))
    initial_global_vars: dict = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Cached Info
    num_invocations: Optional[int] = Field(default=0)
    commit_message: Optional[str] = Field(default=None)
    version_number: Optional[int] = Field(default=None)
    
    class Config:
        table_name = "serializedlmp"
        unique_together = [("version_number", "name")]

# Define the InvocationTrace class
class InvocationTrace(SQLModel, table=True):
    """
    Represents a many-to-many relationship between Invocations and other Invocations (it's a 1st degree link in the trace graph)

    This class is used to keep track of when an invocation consumes a in its kwargs or args a result of another invocation.
    """
    invocation_consumer_id: str = Field(foreign_key="invocation.id", primary_key=True, index=True)  # ID of the Invocation that is consuming another Invocation
    invocation_consuming_id: str = Field(foreign_key="invocation.id", primary_key=True, index=True)  # ID of the Invocation that is being consumed by another Invocation

# Define the Invocation class
class Invocation(SQLModel, table=True):
    """
    Represents an invocation of an LMP.
    
    This class is used to store information about each time an LMP is called.
    """
    id: Optional[str] = Field(default=None, primary_key=True)  # Unique identifier for the invocation
    lmp_id: str = Field(foreign_key="serializedlmp.lmp_id", index=True)  # ID of the LMP that was invoked
    args: List[Any] = Field(default_factory=list, sa_column=Column(JSON))  # Arguments used in the invocation
    kwargs: dict = Field(default_factory=dict, sa_column=Column(JSON))  # Keyword arguments used in the invocation

    global_vars: dict = Field(default_factory=dict, sa_column=Column(JSON))  # Global variables used in the invocation
    free_vars: dict = Field(default_factory=dict, sa_column=Column(JSON))  # Free variables used in the invocation

    latency_ms: float
    prompt_tokens: Optional[int] = Field(default=None)
    completion_tokens: Optional[int] = Field(default=None)
    state_cache_key: Optional[str] = Field(default=None)

    # Timestamp of when the invocation was created
    created_at: datetime = UTCTimestampField(default=func.now(), nullable=False)
    invocation_kwargs: dict = Field(default_factory=dict, sa_column=Column(JSON))  # Additional keyword arguments for the invocation

    # Relationships
    lmp: SerializedLMP = Relationship(back_populates="invocations")  # Relationship to the LMP that was invoked
    # Todo: Rename the result schema to be consistent
    results: List["SerializedLStr"] = Relationship(back_populates="producer_invocation")  # Relationship to the LStr results of the invocation
    

    consumed_by: List["Invocation"] = Relationship(
        back_populates="consumes", link_model=InvocationTrace,
        sa_relationship_kwargs=dict(
            primaryjoin="Invocation.id==InvocationTrace.invocation_consumer_id",
            secondaryjoin="Invocation.id==InvocationTrace.invocation_consuming_id",
        ),
    )  # Relationship to the invocations that consumed this invocation

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
    
    This class is used to store the output of LMP invocations.
    """
    id: Optional[int] = Field(default=None, primary_key=True)  # Unique identifier for the LStr
    content: str  # The actual content of the LStr
    logits: List[float] = Field(default_factory=list, sa_column=Column(JSON))  # Logits associated with the LStr, if available
    producer_invocation_id: Optional[int] = Field(default=None, foreign_key="invocation.id", index=True)  # ID of the Invocation that produced this LStr
    producer_invocation: Optional[Invocation] = Relationship(back_populates="results")  # Relationship to the Invocation that produced this LStr

    # Convert an SerializedLStr to an lstr
    def deserialize(self) -> 'lstr':
        return lstr(self.content, logits=self.logits, _origin_trace=frozenset([self.producer_invocation_id]))
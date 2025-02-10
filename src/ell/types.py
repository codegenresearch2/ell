from datetime import datetime, timezone
from typing import Any, List, Optional, Union, Callable
from sqlmodel import Field, SQLModel, Relationship, JSON, Column
from sqlalchemy import TIMESTAMP, func
import sqlalchemy.types as types
from ell.lstr import lstr
from dataclasses import dataclass
from ell.util.dict_sync_meta import DictSyncMeta

# Define the InvocableLM type
InvocableLM = Callable[..., Union[lstr, str]]

# Define the Message dataclass
@dataclass
class Message(dict, metaclass=DictSyncMeta):
    role: str
    content: Union[lstr, str]

# Define the UTCTimestamp class and UTCTimestampField function
class UTCTimestamp(types.TypeDecorator[datetime]):
    impl = types.TIMESTAMP
    def process_result_value(self, value: datetime, dialect:Any):
        return value.replace(tzinfo=timezone.utc)

def UTCTimestampField(index:bool=False, **kwargs:Any):
    return Field(sa_column=Column(UTCTimestamp(timezone=True), index=index, **kwargs))

# Define the SerializedLMPUses, SerializedLMP, InvocationTrace, Invocation, and SerializedLStr classes
# ... (The rest of the code remains the same)

# Define the utility function to return the current UTC timestamp
def utc_now() -> datetime:
    """
    Returns the current UTC timestamp.
    Serializes to ISO-8601.
    """
    return datetime.now(tz=timezone.utc)
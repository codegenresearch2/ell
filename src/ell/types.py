from datetime import datetime, timezone
from typing import Any, List, Optional
from sqlmodel import Field, SQLModel, Relationship, JSON, Column
from sqlalchemy import func
import sqlalchemy.types as types
from ell.models import SerializedLMPBase, InvocationBase, SerializedLStrBase

class UTCTimestamp(types.TypeDecorator[datetime]):
    cache_ok = True
    impl = types.TIMESTAMP
    def process_result_value(self, value: datetime, dialect:Any):
        return value.replace(tzinfo=timezone.utc)

def UTCTimestampField(index:bool=False, **kwargs:Any):
    return Field(
        sa_column=Column(UTCTimestamp(timezone=True), index=index, **kwargs))

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

# Added import for func from sqlalchemy
from sqlalchemy import func

# Rest of the code...
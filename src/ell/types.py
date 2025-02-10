# Refactored code snippet addressing the feedback

# Moved the definitions of SerializedLMPBase, InvocationBase, and SerializedLStrBase to a separate module
# ell/models.py
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlmodel import SQLModel, Field, Column, JSON
import sqlalchemy.types as types

class UTCTimestamp(types.TypeDecorator[datetime]):
    cache_ok = True
    impl = types.TIMESTAMP
    def process_result_value(self, value: datetime, dialect:Any):
        return value.replace(tzinfo=timezone.utc)

def UTCTimestampField(index:bool=False, **kwargs:Any):
    return Field(
        sa_column=Column(UTCTimestamp(timezone=True), index=index, **kwargs))

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

class SerializedLStrBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    logits: List[float] = Field(default_factory=list, sa_column=Column(JSON))
    producer_invocation_id: Optional[str] = Field(default=None, foreign_key="invocation.id", index=True)

# ell/studio/datamodels.py
from ell.models import SerializedLMPBase, InvocationBase, SerializedLStrBase

# Rest of the code...
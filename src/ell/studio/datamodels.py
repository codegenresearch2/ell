from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlmodel import SQLModel
from ell.types import SerializedLMPBase, InvocationBase, SerializedLStrBase

class SerializedLMPPublic(SerializedLMPBase):
    uses: List["SerializedLMPPublic"]

class SerializedLMPWithUses(SerializedLMPPublic):
    lmp_id: str

class SerializedLMPCreate(SQLModel):
    pass

class SerializedLMPUpdate(SQLModel):
    name: Optional[str] = None
    source: Optional[str] = None
    dependencies: Optional[str] = None
    is_lm: Optional[bool] = None
    lm_kwargs: Optional[Dict[str, Any]] = None
    initial_free_vars: Optional[Dict[str, Any]] = None
    initial_global_vars: Optional[Dict[str, Any]] = None
    commit_message: Optional[str] = None
    version_number: Optional[int] = None

class InvocationPublic(InvocationBase):
    lmp: SerializedLMPPublic
    results: List[SerializedLStrBase]
    consumes: List[str]
    consumed_by: List[str]
    uses: List[str]

class InvocationCreate(SQLModel):
    pass

class InvocationUpdate(SQLModel):
    args: Optional[List[Any]] = None
    kwargs: Optional[Dict[str, Any]] = None
    global_vars: Optional[Dict[str, Any]] = None
    free_vars: Optional[Dict[str, Any]] = None
    latency_ms: Optional[float] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    state_cache_key: Optional[str] = None
    invocation_kwargs: Optional[Dict[str, Any]] = None

class SerializedLStrPublic(SerializedLStrBase):
    pass

class SerializedLStrCreate(SQLModel):
    pass

class SerializedLStrUpdate(SQLModel):
    content: Optional[str] = None
    logits: Optional[List[float]] = None

# Additional classes as per the oracle feedback
class GraphDataPoint(SQLModel):
    timestamp: datetime
    value: float
    comment: Optional[str] = None

class InvocationsAggregate(SQLModel):
    invocation_id: str
    total_latency: float
    average_latency: float
    total_tokens: int
    comment: Optional[str] = None
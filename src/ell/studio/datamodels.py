from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlmodel import SQLModel, select, func
from sqlalchemy import Index
from ell.types import SerializedLMPBase, InvocationBase, SerializedLStrBase, UTCTimestampField

class SerializedLMPPublic(SerializedLMPBase):
    pass

class SerializedLMPWithUses(SerializedLMPPublic):
    lmp_id : str
    uses: List["SerializedLMPPublic"]

class SerializedLMPCreate(SerializedLMPBase):
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

class InvocationCreate(InvocationBase):
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

class SerializedLStrCreate(SerializedLStrBase):
    pass

class SerializedLStrUpdate(SQLModel):
    content: Optional[str] = None
    logits: Optional[List[float]] = None

# Adding database query capabilities
class InvocationMetrics(SQLModel):
    lmp_id: str
    avg_latency_ms: float
    total_prompt_tokens: int
    total_completion_tokens: int

    @classmethod
    def get_metrics_for_lmp(cls, session, lmp_id: str):
        query = select(
            [
                Invocation.lmp_id,
                func.avg(Invocation.latency_ms).label('avg_latency_ms'),
                func.sum(Invocation.prompt_tokens).label('total_prompt_tokens'),
                func.sum(Invocation.completion_tokens).label('total_completion_tokens'),
            ]
        ).where(Invocation.lmp_id == lmp_id).group_by(Invocation.lmp_id)
        result = session.exec(query).first()
        return cls(**result._asdict()) if result else None

# Improving code organization with SQL indexes
Index('ix_invocation_lmp_id_created_at', Invocation.lmp_id, Invocation.created_at)
Index('ix_invocation_created_at_latency_ms', Invocation.created_at, Invocation.latency_ms)
Index('ix_invocation_created_at_tokens', Invocation.created_at, Invocation.prompt_tokens, Invocation.completion_tokens)
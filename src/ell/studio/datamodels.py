from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlmodel import SQLModel, select, func
from ell.types import SerializedLMPBase, InvocationBase, SerializedLStrBase

class GraphDataPoint(SQLModel):
    date: datetime
    count: int
    avg_latency: float
    tokens: int
    # cost: Optional[float] = None  # Uncomment if relevant

class InvocationsAggregate(SQLModel):
    total_invocations: int
    total_tokens: int
    avg_latency: float
    unique_lmps: int
    graph_data: List[GraphDataPoint]

    @classmethod
    def get_aggregate_for_lmp(cls, session, lmp_id: str):
        query = select(
            [
                func.count(Invocation.id).label('total_invocations'),
                func.sum(Invocation.prompt_tokens + Invocation.completion_tokens).label('total_tokens'),
                func.avg(Invocation.latency_ms).label('avg_latency'),
                func.count(func.distinct(Invocation.lmp_id)).label('unique_lmps'),
            ]
        ).where(Invocation.lmp_id == lmp_id).group_by(Invocation.lmp_id)
        result = session.exec(query).first()
        return cls(**result._asdict(), graph_data=[]) if result else None

class SerializedLMPPublic(SerializedLMPBase):
    pass

class SerializedLMPWithUses(SerializedLMPPublic):
    lmp_id: str
    uses: List[SerializedLMPPublic]

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
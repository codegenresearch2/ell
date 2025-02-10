from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlmodel import SQLModel, select, func
from ell.types import SerializedLMPBase, InvocationBase, SerializedLStrBase, UTCTimestampField

# Additional classes as per oracle feedback
class GraphDataPoint(SQLModel):
    date: datetime
    count: int
    avg_latency: float
    tokens: int
    # unique_lmps: int
    # total_tokens: int
    # avg_latency: float

class InvocationsAggregate(SQLModel):
    lmp_id: str
    total_invocations: int
    total_latency_ms: float
    total_tokens: int
    avg_latency: float
    unique_lmps: int
    graph_data: List[GraphDataPoint]

    @classmethod
    def get_aggregate_for_lmp(cls, session, lmp_id: str):
        query = select(
            [
                Invocation.lmp_id,
                func.count(Invocation.id).label('total_invocations'),
                func.sum(Invocation.latency_ms).label('total_latency_ms'),
                func.sum(Invocation.prompt_tokens + Invocation.completion_tokens).label('total_tokens'),
                func.avg(Invocation.latency_ms).label('avg_latency'),
                func.count(func.distinct(Invocation.lmp_id)).label('unique_lmps'),
            ]
        ).where(Invocation.lmp_id == lmp_id).group_by(Invocation.lmp_id)
        result = session.exec(query).first()
        return cls(**result._asdict(), graph_data=[]) if result else None
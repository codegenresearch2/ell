from dataclasses import dataclass
from typing import Callable, Dict, List, Union, Any, Optional
from ell.lstr import lstr
from ell.util.dict_sync_meta import DictSyncMeta
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel, Relationship, JSON, Column
from sqlalchemy import func
import sqlalchemy.types as types
from ell.studio.datamodels import SerializedLMPBase, InvocationBase, SerializedLStrBase, SerializedLMPUses, UTCTimestampField
from ell.stores.sql import SQLStore

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
T = TypeVar("T", bound=Any)
ChatLMP = Callable[[Chat, T], Chat]
LMP = Union[OneTurn, MultiTurnLMP, ChatLMP]
InvocableLM = Callable[..., _lstr_generic]

class SerializedLMP(SerializedLMPBase, table=True):
    invocations: List["Invocation"] = Relationship(back_populates="lmp")
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

class Invocation(InvocationBase, table=True):
    lmp: SerializedLMP = Relationship(back_populates="invocations")
    results: List[SerializedLStr] = Relationship(back_populates="producer_invocation")
    consumed_by: List["Invocation"] = Relationship(
        back_populates="consumes",
        link_model=InvocationTrace,
        sa_relationship_kwargs=dict(
            primaryjoin="Invocation.id==InvocationTrace.invocation_consumer_id",
            secondaryjoin="Invocation.id==InvocationTrace.invocation_consuming_id",
        ),
    )
    consumes: List["Invocation"] = Relationship(
        back_populates="consumed_by",
        link_model=InvocationTrace,
        sa_relationship_kwargs=dict(
            primaryjoin="Invocation.id==InvocationTrace.invocation_consuming_id",
            secondaryjoin="Invocation.id==InvocationTrace.invocation_consumer_id",
        ),
    )
    used_by: Optional["Invocation"] = Relationship(back_populates="uses", sa_relationship_kwargs={"remote_side": "Invocation.id"})
    uses: List["Invocation"] = Relationship(back_populates="used_by")

class SerializedLStr(SerializedLStrBase, table=True):
    producer_invocation: Optional["Invocation"] = Relationship(back_populates="results")

# Enhanced data aggregation capabilities
class SQLStore(SQLStore):
    def get_invocations_aggregate(self, session: Session, lmp_filters: Dict[str, Any] = None, filters: Dict[str, Any] = None, days: int = 30) -> Dict[str, Any]:
        # Existing code...

        # Calculate aggregate metrics
        total_invocations = len(data)
        total_tokens = sum(row.prompt_tokens + row.completion_tokens for row in data)
        avg_latency = sum(row.latency_ms for row in data) / total_invocations if total_invocations > 0 else 0
        unique_lmps = len(set(row.name for row in data))

        # Enhanced data aggregation
        total_cost = sum(row.prompt_tokens * 0.000002 + row.completion_tokens * 0.000002 for row in data)  # Assuming costs per token
        successful_invocations = len([row for row in data if row.completion_tokens is not None])
        success_rate = successful_invocations / total_invocations if total_invocations > 0 else 0

        # Prepare graph data
        graph_data = []
        for row in data:
            graph_data.append({
                "date": row.created_at,
                "avg_latency": row.latency_ms,
                "tokens": row.prompt_tokens + row.completion_tokens,
                "count": 1,
                "cost": row.prompt_tokens * 0.000002 + row.completion_tokens * 0.000002  # Assuming costs per token
            })

        return {
            "total_invocations": total_invocations,
            "total_tokens": total_tokens,
            "avg_latency": avg_latency,
            "unique_lmps": unique_lmps,
            "total_cost": total_cost,
            "successful_invocations": successful_invocations,
            "success_rate": success_rate,
            "graph_data": graph_data
        }
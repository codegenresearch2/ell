from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, create_engine, Session, select
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Column, JSON, Table, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Message(BaseModel):
    role: str
    content: str

class InvocationsAggregate(BaseModel):
    total_invocations: int
    total_tokens: int
    avg_latency: float
    unique_lmps: int
    graph_data: List[Dict[str, Any]]

class SerializedLMPBase(SQLModel):
    lmp_id: Optional[str] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    source: str
    dependencies: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_lm: bool
    lm_kwargs: Optional[Dict[str, Any]] = Field(default_factory=dict, sa_column=Column(JSON))
    initial_free_vars: Optional[Dict[str, Any]] = Field(default_factory=dict, sa_column=Column(JSON))
    initial_global_vars: Optional[Dict[str, Any]] = Field(default_factory=dict, sa_column=Column(JSON))
    num_invocations: Optional[int] = Field(default=0)
    commit_message: Optional[str] = Field(default=None)
    version_number: Optional[int] = Field(default=None)

class SerializedLMP(SerializedLMPBase, table=True):
    invocations: List["Invocation"] = relationship(back_populates="lmp")
    uses: List["SerializedLMP"] = relationship(
        "SerializedLMP",
        secondary=lambda: uses_table,
        primaryjoin="SerializedLMP.lmp_id==uses_table.c.lmp_using_id",
        secondaryjoin="SerializedLMP.lmp_id==uses_table.c.lmp_used_id",
        back_populates="used_by"
    )
    used_by: List["SerializedLMP"] = relationship(
        "SerializedLMP",
        secondary=lambda: uses_table,
        primaryjoin="SerializedLMP.lmp_id==uses_table.c.lmp_used_id",
        secondaryjoin="SerializedLMP.lmp_id==uses_table.c.lmp_using_id",
        back_populates="uses"
    )

uses_table = Table(
    "uses",
    Base.metadata,
    Column("lmp_using_id", ForeignKey("serializedlmp.lmp_id"), primary_key=True),
    Column("lmp_used_id", ForeignKey("serializedlmp.lmp_id"), primary_key=True),
)

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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    invocation_kwargs: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

class Invocation(InvocationBase, table=True):
    lmp: SerializedLMP = relationship(back_populates="invocations")
    results: List["SerializedLStr"] = relationship(back_populates="producer_invocation")
    consumes: List["Invocation"] = relationship(
        "Invocation",
        secondary=lambda: consumes_table,
        primaryjoin="Invocation.id==consumes_table.c.consumer_id",
        secondaryjoin="Invocation.id==consumes_table.c.consumed_id",
        back_populates="consumed_by"
    )
    consumed_by: List["Invocation"] = relationship(
        "Invocation",
        secondary=lambda: consumes_table,
        primaryjoin="Invocation.id==consumes_table.c.consumed_id",
        secondaryjoin="Invocation.id==consumes_table.c.consumer_id",
        back_populates="consumes"
    )
    uses: List["Invocation"] = relationship(
        "Invocation",
        secondary=lambda: uses_invocation_table,
        primaryjoin="Invocation.id==uses_invocation_table.c.using_id",
        secondaryjoin="Invocation.id==uses_invocation_table.c.used_id",
        back_populates="used_by"
    )
    used_by: Optional["Invocation"] = relationship(
        "Invocation",
        secondary=lambda: uses_invocation_table,
        primaryjoin="Invocation.id==uses_invocation_table.c.used_id",
        secondaryjoin="Invocation.id==uses_invocation_table.c.using_id",
        uselist=False,
        back_populates="uses"
    )

consumes_table = Table(
    "consumes",
    Base.metadata,
    Column("consumer_id", ForeignKey("invocation.id"), primary_key=True),
    Column("consumed_id", ForeignKey("invocation.id"), primary_key=True),
)

uses_invocation_table = Table(
    "uses_invocation",
    Base.metadata,
    Column("using_id", ForeignKey("invocation.id"), primary_key=True),
    Column("used_id", ForeignKey("invocation.id"), primary_key=True),
)

class SerializedLStrBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    logits: List[float] = Field(default_factory=list, sa_column=Column(JSON))
    producer_invocation_id: Optional[str] = Field(default=None, foreign_key="invocation.id", index=True)

class SerializedLStr(SerializedLStrBase, table=True):
    producer_invocation: Optional["Invocation"] = relationship(back_populates="results")

class SQLStore:
    def __init__(self, db_uri: str):
        self.engine = create_engine(db_uri)
        Base.metadata.create_all(self.engine)

    def get_invocations_aggregate(self, session: Session, lmp_filters: Dict[str, Any] = None, filters: Dict[str, Any] = None, days: int = 30) -> InvocationsAggregate:
        query = select([
            func.count(Invocation.id).label("total_invocations"),
            func.sum(Invocation.prompt_tokens + Invocation.completion_tokens).label("total_tokens"),
            func.avg(Invocation.latency_ms).label("avg_latency"),
            func.count(SerializedLMP.lmp_id.distinct()).label("unique_lmps"),
            func.date(Invocation.created_at).label("date"),
            func.avg(Invocation.latency_ms).label("avg_latency_per_day"),
            func.sum(Invocation.prompt_tokens + Invocation.completion_tokens).label("tokens_per_day"),
            func.count(Invocation.id).label("invocations_per_day")
        ]).join(SerializedLMP).group_by(func.date(Invocation.created_at))

        if lmp_filters:
            query = query.filter_by(**lmp_filters)
        if filters:
            query = query.filter_by(**filters)

        results = session.execute(query).fetchall()

        graph_data = [
            {
                "date": result.date,
                "avg_latency": result.avg_latency_per_day,
                "tokens": result.tokens_per_day,
                "count": result.invocations_per_day
            }
            for result in results
        ]

        aggregate = {
            "total_invocations": results[0].total_invocations if results else 0,
            "total_tokens": results[0].total_tokens if results else 0,
            "avg_latency": results[0].avg_latency if results else 0,
            "unique_lmps": results[0].unique_lmps if results else 0,
            "graph_data": graph_data
        }

        return InvocationsAggregate(**aggregate)

# FastAPI endpoint for retrieving invocations aggregate
from fastapi import FastAPI, Depends
from sqlmodel import Session

app = FastAPI()

def get_db():
    with Session(SQLStore.engine) as session:
        yield session

@app.get("/invocations/aggregate", response_model=InvocationsAggregate)
def read_invocations_aggregate(lmp_filters: Dict[str, Any] = None, filters: Dict[str, Any] = None, days: int = 30, session: Session = Depends(get_db)):
    return SQLStore().get_invocations_aggregate(session, lmp_filters, filters, days)
from datetime import datetime
from typing import Any, List, Optional
from sqlmodel import Field, SQLModel, Relationship, JSON, Column

# Define utc_now function directly within the same file to avoid circular import issues
def utc_now():
    return datetime.utcnow()

# Define the InvocationTrace class before using it in the Invocation class
class InvocationTrace(SQLModel, table=True):
    invocation_consumer_id: str = Field(foreign_key="invocation.id", primary_key=True)
    invocation_consuming_id: str = Field(foreign_key="invocation.id", primary_key=True)

class Invocation(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    lmp_id: str = Field(foreign_key="serializedlmp.lmp_id")
    args: List[Any] = Field(default_factory=list, sa_column=Column(JSON))
    kwargs: dict = Field(default_factory=dict, sa_column=Column(JSON))
    global_vars: dict = Field(default_factory=dict, sa_column=Column(JSON))
    free_vars: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now)
    invocation_kwargs: dict = Field(default_factory=dict, sa_column=Column(JSON))
    latency_ms: float
    prompt_tokens: Optional[int] = Field(default=None)
    completion_tokens: Optional[int] = Field(default=None)
    state_cache_key: Optional[str] = Field(default=None)
    lmp: 'SerializedLMP' = Relationship(back_populates="invocations")
    results: List['SerializedLStr'] = Relationship(back_populates="producer_invocation")
    consumed_by: List['Invocation'] = Relationship(back_populates="consumes", link_model=InvocationTrace, sa_relationship_kwargs=dict(primaryjoin="Invocation.id==InvocationTrace.invocation_consumer_id", secondaryjoin="Invocation.id==InvocationTrace.invocation_consuming_id"))
    consumes: List['Invocation'] = Relationship(back_populates="consumed_by", link_model=InvocationTrace, sa_relationship_kwargs=dict(primaryjoin="Invocation.id==InvocationTrace.invocation_consuming_id", secondaryjoin="Invocation.id==InvocationTrace.invocation_consumer_id"))

class SerializedLMP(SQLModel, table=True):
    lmp_id: Optional[str] = Field(default=None, primary_key=True)
    name: str
    source: str
    dependencies: str = Field(sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now)
    is_lm: bool
    lm_kwargs: dict = Field(sa_column=Column(JSON))
    invocations: List[Invocation] = Relationship(back_populates="lmp")
    used_by: Optional[List['SerializedLMP']] = Relationship(back_populates="uses", link_model='SerializedLMPUses', sa_relationship_kwargs=dict(primaryjoin="SerializedLMP.lmp_id==SerializedLMPUses.lmp_user_id", secondaryjoin="SerializedLMP.lmp_id==SerializedLMPUses.lmp_using_id"))
    uses: List['SerializedLMP'] = Relationship(back_populates="used_by", link_model='SerializedLMPUses', sa_relationship_kwargs=dict(primaryjoin="SerializedLMP.lmp_id==SerializedLMPUses.lmp_using_id", secondaryjoin="SerializedLMP.lmp_id==SerializedLMPUses.lmp_user_id"))
    initial_free_vars: dict = Field(default_factory=dict, sa_column=Column(JSON))
    initial_global_vars: dict = Field(default_factory=dict, sa_column=Column(JSON))
    num_invocations: Optional[int] = Field(default=0)
    commit_message: Optional[str] = Field(default=None)
    version_number: Optional[int] = Field(default=None)

    class Config:
        table_name = "serializedlmp"
        unique_together = [("version_number", "name")]

class SerializedLStr(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    logits: List[float] = Field(default_factory=list, sa_column=Column(JSON))
    producer_invocation_id: Optional[int] = Field(default=None, foreign_key="invocation.id")
    producer_invocation: Optional[Invocation] = Relationship(back_populates="results")

    def deserialize(self) -> lstr:
        return lstr(self.content, logits=self.logits, _origin_trace=frozenset([self.producer_invocation_id]))

# Define the SerializedLMPUses class after the SerializedLMP class to avoid circular import issues
class SerializedLMPUses(SQLModel, table=True):
    lmp_user_id: Optional[str] = Field(default=None, foreign_key="serializedlmp.lmp_id", primary_key=True)
    lmp_using_id: Optional[str] = Field(default=None, foreign_key="serializedlmp.lmp_id", primary_key=True)
from sqlmodel import Field, SQLModel, Relationship, JSON, Column
import sqlalchemy.types as types
from datetime import datetime, timezone

# Ensure the necessary import for SQLAlchemy functions
from sqlalchemy import func

# Define the SerializedLMPUses class
class SerializedLMPUses(SQLModel, table=True):
    lmp_user_id: Optional[str] = Field(default=None, foreign_key='serializedlmp.lmp_id', primary_key=True, index=True)
    lmp_using_id: Optional[str] = Field(default=None, foreign_key='serializedlmp.lmp_id', primary_key=True, index=True)

# Define the UTCTimestamp class
class UTCTimestamp(types.TypeDecorator[datetime]):
    impl = types.TIMESTAMP
    def process_result_value(self, value: datetime, dialect: Any):
        return value.replace(tzinfo=timezone.utc)

# Define the UTCTimestampField function
def UTCTimestampField(index: bool = False, **kwargs: Any):
    return Field(sa_column=Column(UTCTimestamp(timezone=True), index=index, **kwargs))

# Define the SerializedLMP class
class SerializedLMP(SQLModel, table=True):
    lmp_id: Optional[str] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    source: str
    dependencies: str
    created_at: datetime = UTCTimestampField(index=True, default=func.now(), nullable=False)
    is_lm: bool
    lm_kwargs: dict = Field(sa_column=Column(JSON))

    invocations: List['Invocation'] = Relationship(back_populates='lmp')
    used_by: Optional[List['SerializedLMP']] = Relationship(back_populates='uses', link_model=SerializedLMPUses, sa_relationship_kwargs=dict(
        primaryjoin='SerializedLMP.lmp_id==SerializedLMPUses.lmp_user_id',
        secondaryjoin='SerializedLMP.lmp_id==SerializedLMPUses.lmp_using_id',
    ))
    uses: List['SerializedLMP'] = Relationship(back_populates='used_by', link_model=SerializedLMPUses, sa_relationship_kwargs=dict(
        primaryjoin='SerializedLMP.lmp_id==SerializedLMPUses.lmp_using_id',
        secondaryjoin='SerializedLMP.lmp_id==SerializedLMPUses.lmp_user_id',
    ))

    initial_free_vars: dict = Field(default_factory=dict, sa_column=Column(JSON))
    initial_global_vars: dict = Field(default_factory=dict, sa_column=Column(JSON))

    num_invocations: Optional[int] = Field(default=0)
    commit_message: Optional[str] = Field(default=None)
    version_number: Optional[int] = Field(default=None)

    class Config:
        table_name = 'serializedlmp'
        unique_together = [('version_number', 'name')]

from datetime import datetime
from typing import Any, Optional, Dict, List, Set, Union
from sqlmodel import Session, SQLModel, create_engine, select
import ell.store
import json
from sqlalchemy import or_, func, and_
from ell.lstr import lstr

class InvocationTrace(SQLModel, table=True):
    invocation_consumer_id: str = Field(foreign_key="invocation.id", primary_key=True)
    invocation_consuming_id: str = Field(foreign_key="invocation.id", primary_key=True)

class SerializedLMP(SQLModel, table=True):
    lmp_id: Optional[str] = Field(default=None, primary_key=True)
    name: str
    source: str
    dependencies: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_lm: bool
    lm_kwargs: dict = Field(sa_column=Column(JSON))
    initial_free_vars: dict = Field(default_factory=dict, sa_column=Column(JSON))
    initial_global_vars: dict = Field(default_factory=dict, sa_column=Column(JSON))
    num_invocations: Optional[int] = Field(default=0)
    commit_message: Optional[str] = Field(default=None)
    version_number: Optional[int] = Field(default=None)
    invocations: List["Invocation"] = Relationship(back_populates="lmp")
    used_by: Optional[List["SerializedLMP"]] = Relationship(back_populates="uses", link_model=SerializedLMPUses)
    uses: List["SerializedLMP"] = Relationship(back_populates="used_by", link_model=SerializedLMPUses)

class Invocation(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    lmp_id: str = Field(foreign_key="serializedlmp.lmp_id")
    args: List[Any] = Field(default_factory=list, sa_column=Column(JSON))
    kwargs: dict = Field(default_factory=dict, sa_column=Column(JSON))
    global_vars: dict = Field(default_factory=dict, sa_column=Column(JSON))
    free_vars: dict = Field(default_factory=dict, sa_column=Column(JSON))
    latency_ms: float
    prompt_tokens: Optional[int] = Field(default=None)
    completion_tokens: Optional[int] = Field(default=None)
    state_cache_key: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    invocation_kwargs: dict = Field(default_factory=dict, sa_column=Column(JSON))
    lmp: SerializedLMP = Relationship(back_populates="invocations")
    results: List["SerializedLStr"] = Relationship(back_populates="producer_invocation")
    consumed_by: List["Invocation"] = Relationship(back_populates="consumes", link_model=InvocationTrace)
    consumes: List["Invocation"] = Relationship(back_populates="consumed_by", link_model=InvocationTrace)

class SerializedLStr(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    logits: List[float] = Field(default_factory=list, sa_column=Column(JSON))
    producer_invocation_id: Optional[int] = Field(default=None, foreign_key="invocation.id")
    producer_invocation: Optional[Invocation] = Relationship(back_populates="results")

    def deserialize(self) -> lstr:
        return lstr(self.content, logits=self.logits, _origin_trace=frozenset([self.producer_invocation_id]))

class SQLStore(ell.store.Store):
    def __init__(self, db_uri: str):
        self.engine = create_engine(db_uri)
        SQLModel.metadata.create_all(self.engine)

    def write_lmp(self, lmp_id: str, name: str, source: str, dependencies: List[str], is_lmp: bool, lm_kwargs: str,
                  version_number: int, uses: Dict[str, Any], global_vars: Dict[str, Any], free_vars: Dict[str, Any],
                  commit_message: Optional[str] = None, created_at: Optional[float] = None) -> Optional[Any]:
        with Session(self.engine) as session:
            lmp = session.query(SerializedLMP).filter(SerializedLMP.lmp_id == lmp_id).first()

            if lmp:
                return lmp
            else:
                lmp = SerializedLMP(
                    lmp_id=lmp_id,
                    name=name,
                    version_number=version_number,
                    source=source,
                    dependencies=json.dumps(dependencies),
                    initial_global_vars=global_vars,
                    initial_free_vars=free_vars,
                    created_at=created_at or datetime.utcnow(),
                    is_lm=is_lmp,
                    lm_kwargs=json.loads(lm_kwargs),
                    commit_message=commit_message
                )
                session.add(lmp)

            for use_id in uses:
                used_lmp = session.exec(select(SerializedLMP).where(SerializedLMP.lmp_id == use_id)).first()
                if used_lmp:
                    lmp.uses.append(used_lmp)

            session.commit()
        return None

    def write_invocation(self, id: str, lmp_id: str, args: str, kwargs: str, result: Union[lstr, List[lstr]], invocation_kwargs: Dict[str, Any],
                         global_vars: Dict[str, Any], free_vars: Dict[str, Any], created_at: Optional[float], consumes: Set[str],
                         prompt_tokens: Optional[int] = None, completion_tokens: Optional[int] = None, latency_ms: Optional[float] = None,
                         state_cache_key: Optional[str] = None, cost_estimate: Optional[float] = None) -> Optional[Any]:
        with Session(self.engine) as session:
            if isinstance(result, lstr):
                results = [result]
            elif isinstance(result, list):
                results = result
            else:
                raise TypeError("Result must be either lstr or List[lstr]")

            lmp = session.query(SerializedLMP).filter(SerializedLMP.lmp_id == lmp_id).first()
            assert lmp is not None, f"LMP with id {lmp_id} not found. Writing invocation erroneously"

            lmp.num_invocations += 1
            invocation = Invocation(
                id=id,
                lmp_id=lmp.lmp_id,
                args=json.loads(args),
                kwargs=json.loads(kwargs),
                global_vars=global_vars,
                free_vars=free_vars,
                created_at=created_at or datetime.utcnow(),
                invocation_kwargs=invocation_kwargs,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                latency_ms=latency_ms,
                state_cache_key=state_cache_key,
            )

            for res in results:
                serialized_lstr = SerializedLStr(content=str(res), logits=res.logits)
                session.add(serialized_lstr)
                invocation.results.append(serialized_lstr)

            session.add(invocation)

            for consumed_id in consumes:
                session.add(InvocationTrace(
                    invocation_consumer_id=id,
                    invocation_consuming_id=consumed_id
                ))

            session.commit()
    def get_lmps(self, **filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        with Session(self.engine) as session:
            query = select(SerializedLMP, SerializedLMPUses.lmp_user_id).outerjoin(
                SerializedLMPUses,
                SerializedLMP.lmp_id == SerializedLMPUses.lmp_using_id
            ).order_by(SerializedLMP.created_at.desc())

            if filters:
                for key, value in filters.items():
                    query = query.where(getattr(SerializedLMP, key) == value)
            results = session.exec(query).all()

            lmp_dict = {lmp.lmp_id: {**lmp.model_dump(), 'uses': []} for lmp, _ in results}
            for lmp, using_id in results:
                if using_id:
                    lmp_dict[lmp.lmp_id]['uses'].append(using_id)
            return list(lmp_dict.values())

    def get_invocations(self, lmp_filters: Dict[str, Any], filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        with Session(self.engine) as session:
            query = select(Invocation, SerializedLStr, SerializedLMP).join(SerializedLMP).outerjoin(SerializedLStr)

            for key, value in lmp_filters.items():
                query = query.where(getattr(SerializedLMP, key) == value)

            if filters:
                for key, value in filters.items():
                    query = query.where(getattr(Invocation, key) == value)

            query = query.order_by(Invocation.created_at.desc())

            results = session.exec(query).all()

            invocations = {}
            for inv, lstr, lmp in results:
                if inv.id not in invocations:
                    inv_dict = inv.model_dump()
                    inv_dict['lmp'] = lmp.model_dump()
                    invocations[inv.id] = inv_dict
                    invocations[inv.id]['results'] = []
                if lstr:
                    invocations[inv.id]['results'].append(dict(**lstr.model_dump(), __lstr=True))

            return list(invocations.values())

    def get_lmp_versions(self, name: str) -> List[Dict[str, Any]]:
        return self.get_lmps(name=name)

    def get_latest_lmps(self) -> List[Dict[str, Any]]:
        raise NotImplementedError()
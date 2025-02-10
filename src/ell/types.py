from datetime import datetime
from typing import Any, Optional, Dict, List, Set, Union
from sqlmodel import Session, SQLModel, create_engine, select
import ell.store
import json
from ell.types import InvocationTrace, SerializedLMP, Invocation, SerializedLMPUses, SerializedLStr, utc_now
from ell.lstr import lstr
from sqlalchemy import or_, func, and_

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
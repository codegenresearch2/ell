from datetime import datetime, timedelta
import json
import os
from typing import Any, Optional, Dict, List, Set, Union
from pydantic import BaseModel
from sqlmodel import Session, SQLModel, create_engine, select
import ell.store
import cattrs
import numpy as np
from sqlalchemy.sql import text
from ell.types import InvocationTrace, SerializedLMP, Invocation, InvocationContents
from ell._lstr import _lstr
from sqlalchemy import or_, func, and_, extract, FromClause
from sqlalchemy.types import TypeDecorator, VARCHAR
from ell.types.lmp import SerializedLMPUses, utc_now
from ell.util.serialization import pydantic_ltype_aware_cattr
import gzip
import json


class SQLStore(ell.store.Store):
    def __init__(self, db_uri: str, has_blob_storage: bool = False):
        self.engine = create_engine(db_uri, json_serializer=lambda obj: json.dumps(pydantic_ltype_aware_cattr.unstructure(obj), sort_keys=True, default=repr))
        SQLModel.metadata.create_all(self.engine)
        self.open_files: Dict[str, Dict[str, Any]] = {}
        super().__init__(has_blob_storage)

    def write_lmp(self, serialized_lmp: SerializedLMP, uses: Dict[str, Any]) -> Optional[Any]:
        with Session(self.engine) as session:
            lmp = session.exec(select(SerializedLMP).filter(SerializedLMP.lmp_id == serialized_lmp.lmp_id)).first()
            if lmp:
                return lmp
            else:
                session.add(serialized_lmp)
            for use_id in uses:
                used_lmp = session.exec(select(SerializedLMP).where(SerializedLMP.lmp_id == use_id)).first()
                if used_lmp:
                    serialized_lmp.uses.append(used_lmp)
            session.commit()
        return None

    def write_invocation(self, invocation: Invocation, consumes: Set[str]) -> Optional[Any]:
        with Session(self.engine) as session:
            lmp = session.exec(select(SerializedLMP).filter(SerializedLMP.lmp_id == invocation.lmp_id)).first()
            assert lmp is not None, f"LMP with id {invocation.lmp_id} not found. Writing invocation erroneously"
            if lmp.num_invocations is None:
                lmp.num_invocations = 1
            else:
                lmp.num_invocations += 1
            session.add(invocation.contents)
            session.add(invocation)
            for consumed_id in consumes:
                session.add(InvocationTrace(invocation_consumer_id=invocation.id, invocation_consuming_id=consumed_id))
            session.commit()
            return None
        
    def get_cached_invocations(self, lmp_id: str, state_cache_key: str) -> List[Invocation]:
        with Session(self.engine) as session:
            return self.get_invocations(session, lmp_filters={"lmp_id": lmp_id}, filters={"state_cache_key": state_cache_key})
        
    def get_versions_by_fqn(self, fqn: str) -> List[SerializedLMP]:
        with Session(self.engine) as session:
            return self.get_lmps(session, name=fqn)
        
    def get_latest_lmps(self, session: Session, skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
        subquery = (
            select(SerializedLMP.name, func.max(SerializedLMP.created_at).label("max_created_at"))
            .group_by(SerializedLMP.name)
            .subquery()
        )
        filters = {
            "name": subquery.c.name,
            "created_at": subquery.c.max_created_at
        }
        return self.get_lmps(session, skip=skip, limit=limit, subquery=subquery, **filters)

    def get_lmps(self, session: Session, skip: int = 0, limit: int = 10, subquery=None, **filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        query = select(SerializedLMP)
        if subquery is not None:
            query = query.join(subquery, and_(SerializedLMP.name == subquery.c.name, SerializedLMP.created_at == subquery.c.max_created_at))
        if filters:
            for key, value in filters.items():
                query = query.where(getattr(SerializedLMP, key) == value)
        query = query.order_by(SerializedLMP.created_at.desc()).offset(skip).limit(limit)
        results = session.exec(query).all()
        return results

    def get_invocations(self, session: Session, lmp_filters: Dict[str, Any], skip: int = 0, limit: int = 10, filters: Optional[Dict[str, Any]] = None, hierarchical: bool = False) -> List[Dict[str, Any]]:
        query = select(Invocation).join(SerializedLMP)
        for key, value in lmp_filters.items():
            query = query.where(getattr(SerializedLMP, key) == value)
        if filters:
            for key, value in filters.items():
                query = query.where(getattr(Invocation, key) == value)
        query = query.order_by(Invocation.created_at.desc()).offset(skip).limit(limit)
        invocations = session.exec(query).all()
        return invocations

    def get_traces(self, session: Session):
        query = text("""
        SELECT 
            consumer.lmp_id, 
            trace.*, 
            consumed.lmp_id
        FROM 
            invocation AS consumer
        JOIN 
            invocationtrace AS trace ON consumer.id = trace.invocation_consumer_id
        JOIN 
            invocation AS consumed ON trace.invocation_consuming_id = consumed.id
        """)
        results = session.exec(query).all()
        traces = []
        for (consumer_lmp_id, consumer_invocation_id, consumed_invocation_id, consumed_lmp_id) in results:
            traces.append({'consumer': consumer_lmp_id, 'consumed': consumed_lmp_id})
        return traces
        
    def get_all_traces_leading_to(self, session: Session, invocation_id: str) -> List[Dict[str, Any]]:
        traces = []
        visited = set()
        queue = [(invocation_id, 0)]
        while queue:
            current_invocation_id, depth = queue.pop(0)
            if depth > 4:
                continue
            if current_invocation_id in visited:
                continue
            visited.add(current_invocation_id)
            results = session.exec(
                select(InvocationTrace, Invocation, SerializedLMP)
                .join(Invocation, InvocationTrace.invocation_consuming_id == Invocation.id)
                .join(SerializedLMP, Invocation.lmp_id == SerializedLMP.lmp_id)
                .where(InvocationTrace.invocation_consumer_id == current_invocation_id)
            ).all()
            for row in results:
                trace = {
                    'consumer_id': row.InvocationTrace.invocation_consumer_id,
                    'consumed': {key: value for key, value in row.Invocation.__dict__.items() if key not in ['invocation_consumer_id', 'invocation_consuming_id']},
                    'consumed_lmp': row.SerializedLMP.model_dump()
                }
                traces.append(trace)
                queue.append((row.Invocation.id, depth + 1))
        unique_traces = {}
        for trace in traces:
            consumed_id = trace['consumed']['id']
            if consumed_id not in unique_traces:
                unique_traces[consumed_id] = trace
        return list(unique_traces.values())
    
    def get_invocations_aggregate(self, session: Session, lmp_filters: Dict[str, Any] = None, filters: Dict[str, Any] = None, days: int = 30) -> Dict[str, Any]:
        start_date = datetime.utcnow() - timedelta(days=days)
        base_subquery = (
            select(Invocation.created_at, Invocation.latency_ms, Invocation.prompt_tokens, Invocation.completion_tokens, Invocation.lmp_id)
            .join(SerializedLMP, Invocation.lmp_id == SerializedLMP.lmp_id)
            .filter(Invocation.created_at >= start_date)
        )
        if lmp_filters:
            base_subquery = base_subquery.filter(and_(*[getattr(SerializedLMP, k) == v for k, v in lmp_filters.items()]))
        if filters:
            base_subquery = base_subquery.filter(and_(*[getattr(Invocation, k) == v for k, v in filters.items()]))
        data = session.exec(base_subquery).all()
        total_invocations = len(data)
        total_tokens = sum(row.prompt_tokens + row.completion_tokens for row in data)
        avg_latency = sum(row.latency_ms for row in data) / total_invocations if total_invocations > 0 else 0
        unique_lmps = len(set(row.lmp_id for row in data))
        graph_data = [{
            "date": row.created_at,
            "avg_latency": row.latency_ms,
            "tokens": row.prompt_tokens + row.completion_tokens,
            "count": 1
        } for row in data]
        return {
            "total_invocations": total_invocations,
            "total_tokens": total_tokens,
            "avg_latency": avg_latency,
            "unique_lmps": unique_lmps,
            "graph_data": graph_data
        }


class SQLiteStore(SQLStore):
    def __init__(self, db_dir: str):
        assert not db_dir.endswith('.db'), "Create store with a directory not a db."
        os.makedirs(db_dir, exist_ok=True)
        self.db_dir = db_dir
        db_path = os.path.join(db_dir, 'ell.db')
        super().__init__(f'sqlite:///{db_path}', has_blob_storage=True)

    def _get_blob_path(self, id: str, depth: int = 2) -> str:
        if not self.has_blob_storage:
            raise ValueError("This store does not support external blob storage")
        assert "-" in id, "Blob id must have a single - in it to split on."
        _type, _id = id.split("-")
        increment = 2
        dirs = [_type] + [_id[i:i+increment] for i in range(0, depth*increment, increment)]
        file_name = _id[depth*increment:]
        return os.path.join(self.db_dir, "blob", *dirs, file_name)

    def write_external_blob(self, id: str, json_dump: str, depth: int = 2):
        file_path = self._get_blob_path(id, depth)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with gzip.open(file_path, "wt", encoding="utf-8") as f:
            f.write(json_dump)

    def read_external_blob(self, id: str, depth: int = 2) -> str:
        file_path = self._get_blob_path(id, depth)
        with gzip.open(file_path, "rt", encoding="utf-8") as f:
            return f.read()


class PostgresStore(SQLStore):
    def __init__(self, db_uri: str):
        super().__init__(db_uri, has_blob_storage=False)
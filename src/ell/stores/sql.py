import datetime
import json
from typing import Any, Optional, Dict, List, Set, Union
from sqlmodel import Session, SQLModel, create_engine, select
import ell.store
from ell.types import InvocationTrace, SerializedLMP, Invocation, SerializedLMPUses, SerializedLStr, utc_now
from ell.lstr import lstr
from sqlalchemy import or_, func, and_, text
import os
import cattrs
import numpy as np

class SQLStore(ell.store.Store):
    def __init__(self, db_uri: str):
        self.engine = create_engine(db_uri)
        SQLModel.metadata.create_all(self.engine)
        self.open_files: Dict[str, Dict[str, Any]] = {}

    def write_lmp(self, lmp_id: str, name: str, source: str, dependencies: List[str], is_lmp: bool, lm_kwargs: str,
                  version_number: int, uses: Dict[str, Any], global_vars: Dict[str, Any], free_vars: Dict[str, Any],
                  commit_message: Optional[str] = None, created_at: Optional[datetime.datetime] = None) -> Optional[Any]:
        # Implement the logic to write LMP data to the database
        # This may involve creating a new SerializedLMP object and adding it to the session
        # Don't forget to handle relationships and commit the transaction
        pass

    def write_invocation(self, id: str, lmp_id: str, args: str, kwargs: str, result: Union[lstr, List[lstr]], invocation_kwargs: Dict[str, Any],
                         global_vars: Dict[str, Any], free_vars: Dict[str, Any], created_at: Optional[datetime.datetime], consumes: Set[str],
                         prompt_tokens: Optional[int] = None, completion_tokens: Optional[int] = None, latency_ms: Optional[float] = None,
                         state_cache_key: Optional[str] = None, cost_estimate: Optional[float] = None) -> Optional[Any]:
        # Implement the logic to write invocation data to the database
        # This may involve creating a new Invocation object and adding it to the session
        # Don't forget to handle relationships and commit the transaction
        pass

    def get_latest_lmps(self, skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
        # Implement the logic to retrieve the latest LMPs from the database
        # This may involve constructing a query with appropriate filters and joins
        pass

    def get_lmps(self, skip: int = 0, limit: int = 10, subquery=None, **filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Implement the logic to retrieve LMPs from the database based on filters
        # This may involve constructing a query with appropriate filters and joins
        pass

    def get_invocations(self, lmp_filters: Dict[str, Any], skip: int = 0, limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        # Implement the logic to retrieve invocations from the database based on filters
        # This may involve constructing a query with appropriate filters and joins
        pass

    def get_traces(self):
        # Implement the logic to retrieve traces from the database
        # This may involve constructing a query with appropriate joins
        pass

    def get_all_traces_leading_to(self, invocation_id: str) -> List[Dict[str, Any]]:
        # Implement the logic to retrieve all traces leading to a specific invocation
        # This may involve constructing a query with appropriate joins and filters
        pass

class SQLiteStore(SQLStore):
    def __init__(self, storage_dir: str):
        os.makedirs(storage_dir, exist_ok=True)
        db_path = os.path.join(storage_dir, 'ell.db')
        super().__init__(f'sqlite:///{db_path}')
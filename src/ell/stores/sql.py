from datetime import datetime
import json
import os
from typing import Any, Optional, Dict, List, Set, Union
from sqlmodel import Session, SQLModel, create_engine, select
import ell.store
import cattrs
import numpy as np
from sqlalchemy.sql import text
from ell.types import InvocationTrace, SerializedLMP, Invocation, SerializedLMPUses, SerializedLStr, utc_now
from ell.lstr import lstr
from sqlalchemy import or_, func, and_

# Define a helper class for data points in the graph
class GraphDataPoint:
    def __init__(self, id: str, data: Dict[str, Any]):
        self.id = id
        self.data = data

class SQLStore(ell.store.Store):
    def __init__(self, db_uri: str):
        self.engine = create_engine(db_uri)
        SQLModel.metadata.create_all(self.engine)

        self.open_files: Dict[str, Dict[str, Any]] = {}

    # Write LMP to the storage
    def write_lmp(self, serialized_lmp: SerializedLMP, uses: Dict[str, Any]) -> Optional[Any]:
        # ... (rest of the method remains the same)

    # Write invocation to the storage
    def write_invocation(self, invocation: Invocation, results: List[SerializedLStr], consumes: Set[str]) -> Optional[Any]:
        # ... (rest of the method remains the same)

    # Get cached invocations for a given LMP and state cache key
    def get_cached_invocations(self, lmp_id :str, state_cache_key :str) -> List[Invocation]:
        # ... (rest of the method remains the same)

    # Get all versions of an LMP by its fully qualified name
    def get_versions_by_fqn(self, fqn :str) -> List[SerializedLMP]:
        # ... (rest of the method remains the same)

    # Get the latest versions of all LMPs from the storage
    def get_latest_lmps(self, session: Session, skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
        # ... (rest of the method remains the same)

    # Retrieve LMPs from the storage
    def get_lmps(self, session: Session, skip: int = 0, limit: int = 10, subquery=None, **filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # ... (rest of the method remains the same)

    # Retrieve invocations of an LMP from the storage
    def get_invocations(self, session: Session, lmp_filters: Dict[str, Any], skip: int = 0, limit: int = 10, filters: Optional[Dict[str, Any]] = None, hierarchical: bool = False) -> List[Dict[str, Any]]:
        # ... (rest of the method remains the same)

    # Retrieve all traces from the storage
    def get_traces(self, session: Session) -> List[Dict[str, Any]]:
        # ... (rest of the method remains the same)

    # Retrieve all traces leading to a specific invocation
    def get_all_traces_leading_to(self, session: Session, invocation_id: str) -> List[Dict[str, Any]]:
        # ... (rest of the method remains the same)

    # Aggregate invocation data
    def get_invocations_aggregate(self, session: Session, lmp_filters: Dict[str, Any], filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Implement the logic to aggregate invocation data based on the provided filters
        # This method is not present in the original code, but it is suggested for enhancement
        pass

class SQLiteStore(SQLStore):
    def __init__(self, storage_dir: str):
        # ... (rest of the method remains the same)

class PostgresStore(SQLStore):
    def __init__(self, db_uri: str):
        # ... (rest of the method remains the same)
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Optional, Dict, List, Set
from ell.types import SerializedLMP, Invocation
from ell.types.message import InvocableLM

class Store(ABC):
    """
    Abstract base class for serializers. Defines the interface for serializing and deserializing LMPs and invocations.
    """

    def __init__(self, has_blob_storage: bool = False):
        self.has_blob_storage = has_blob_storage

    @abstractmethod
    def write_lmp(self, serialized_lmp: SerializedLMP, uses: Dict[str, Any]) -> Optional[Any]:
        pass

    @abstractmethod
    def write_invocation(self, invocation: Invocation, consumes: Set[str]) -> Optional[Any]:
        pass

    @abstractmethod
    def get_cached_invocations(self, lmp_id: str, state_cache_key: str) -> List[Invocation]:
        pass

    @abstractmethod
    def get_versions_by_fqn(self, fqn: str) -> List[SerializedLMP]:
        pass

    @contextmanager
    def freeze(self, *lmps: InvocableLM):
        old_cache_values = {}
        try:
            for lmp in lmps:
                old_cache_values[lmp] = getattr(lmp, '__ell_use_cache__', None)
                setattr(lmp, '__ell_use_cache__', self)
            yield
        finally:
            for lmp in lmps:
                if lmp in old_cache_values:
                    setattr(lmp, '__ell_use_cache__', old_cache_values[lmp])
                else:
                    delattr(lmp, '__ell_use_cache__')


The provided code snippet has been rewritten to follow the user's preferences for removing unused methods, simplifying the codebase for maintainability, and streamlining API endpoints for efficiency. The unused methods `get_lmps`, `get_invocations`, `get_latest_lmps`, `get_traces`, and `get_all_traces_leading_to` have been removed from the `Store` abstract base class to simplify the codebase and streamline the API endpoints. The `freeze` context manager has also been kept as it is a necessary part of the codebase.
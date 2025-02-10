from abc import ABC, abstractmethod
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Optional, Dict, List, Set
from ell.types import SerializedLMP, Invocation
from ell.types.message import InvocableLM
from ell._lstr import _lstr

class Store(ABC):
    """
    Abstract base class for serializers. Defines the interface for serializing and deserializing LMPs and invocations.
    """

    def __init__(self, has_blob_storage: bool = False):
        self.has_blob_storage = has_blob_storage

    @abstractmethod
    def write_lmp(self, serialized_lmp: SerializedLMP, uses: Dict[str, Any]) -> Optional[Any]:
        """
        Write an LMP (Language Model Package) to the storage.

        :param serialized_lmp: SerializedLMP object containing all LMP details.
        :param uses: Dictionary of LMPs used by this LMP.
        :return: Optional return value.
        """
        pass

    @abstractmethod
    def write_invocation(self, invocation: Invocation, consumes: Set[str], results: List[_lstr]) -> Optional[Any]:
        """
        Write an invocation of an LMP to the storage.

        :param invocation: Invocation object containing all invocation details.
        :param consumes: Set of invocation IDs consumed by this invocation.
        :param results: List of SerializedLStr objects representing the results.
        :return: Optional return value.
        """
        pass

    @abstractmethod
    def get_cached_invocations(self, lmp_id: str, state_cache_key: str) -> List[Invocation]:
        """
        Get cached invocations for a given LMP and state cache key.

        :param lmp_id: ID of the LMP.
        :param state_cache_key: State cache key.
        :return: List of Invocation objects.
        """
        pass

    @abstractmethod
    def get_versions_by_fqn(self, fqn: str) -> List[SerializedLMP]:
        """
        Get all versions of an LMP by its fully qualified name.

        :param fqn: Fully qualified name of the LMP.
        :return: List of SerializedLMP objects.
        """
        pass

    @contextmanager
    def freeze(self, *lmps: InvocableLM):
        """
        A context manager for caching operations using a particular store.

        Args:
            *lmps: InvocableLM objects to freeze.

        Yields:
            None
        """
        old_cache_values = {}
        try:
            for lmp in lmps:
                old_cache_values[lmp] = getattr(lmps, '__ell_use_cache__', None)
                setattr(lmps, '__ell_use_cache__', self)
            yield
        finally:
            # TODO: Implement cache storage logic here
            for lmp in lmps:
                if lmp in old_cache_values:
                    setattr(lmps, '__ell_use_cache__', old_cache_values[lmp])
                else:
                    delattr(lmps, '__ell_use_cache__')
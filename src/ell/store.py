from abc import ABC, abstractmethod
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Optional, Dict, List, Set, Union
from sqlmodel import SQLModel, create_engine
from ell.lstr import lstr
from ell.types import InvocableLM, SerializedLMP, Invocation

# Initialize the SQLModel engine
engine = create_engine("sqlite:///database.db")

class Store(ABC):
    """
    Abstract base class for serializers. Defines the interface for serializing and deserializing LMPs and invocations.
    """

    @abstractmethod
    def write_lmp(self, lmp: SerializedLMP, created_at: Optional[datetime] = None) -> Optional[Any]:
        """
        Write an LMP (Language Model Package) to the storage.

        :param lmp: SerializedLMP object.
        :param created_at: Optional timestamp of when the LMP was created.
        :return: Optional return value.
        """
        pass

    @abstractmethod
    def write_invocation(self, invocation: Invocation, created_at: Optional[datetime] = None) -> Optional[Any]:
        """
        Write an invocation of an LMP to the storage.

        :param invocation: Invocation object.
        :param created_at: Optional timestamp of when the invocation was created.
        :return: Optional return value.
        """
        pass

    @abstractmethod
    def get_lmps(self, **filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Retrieve LMPs from the storage.

        :param filters: Optional dictionary of filters to apply.
        :return: List of LMPs.
        """
        pass

    @abstractmethod
    def get_invocations(self, lmp_id: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve invocations of an LMP from the storage.

        :param lmp_id: Unique identifier for the LMP.
        :param filters: Optional dictionary of filters to apply.
        :return: List of invocations.
        """
        pass

    @abstractmethod
    def search_lmps(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for LMPs in the storage.

        :param query: Search query string.
        :return: List of LMPs matching the query.
        """
        pass

    @abstractmethod
    def search_invocations(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for invocations in the storage.

        :param query: Search query string.
        :return: List of invocations matching the query.
        """
        pass

    @abstractmethod
    def get_latest_lmps(self) -> List[Dict[str, Any]]:
        """
        Retrieve the latest versions of all LMPs from the storage.

        :return: List of the latest LMPs.
        """
        pass

    @contextmanager
    def freeze(self, *lmps: InvocableLM):
        """
        A context manager for caching operations using a particular store.

        Args:
            *lmps: Variable length argument list of InvocableLM objects.
            key (Optional[str]): The cache key. If None, a default key will be generated.
            condition (Optional[Callable[..., bool]]): A function that determines whether to cache or not.

        Yields:
            None
        """
        old_cache_values = {}
        try:
            for lmp in lmps:
                old_cache_values[lmp] = getattr(lmp, '__ell_use_cache__', None)
                setattr(lmp, '__ell_use_cache__', self)
            yield
        finally:
            # TODO: Implement cache storage logic here
            for lmp in lmps:
                if lmp in old_cache_values:
                    setattr(lmp, '__ell_use_cache__', old_cache_values[lmp])
                else:
                    delattr(lmp, '__ell_use_cache__')
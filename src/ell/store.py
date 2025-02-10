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
    def get_lmps(self, **filters: Optional[Dict[str, Any]]) -> List[SerializedLMP]:
        """
        Retrieve LMPs from the storage.

        :param filters: Optional dictionary of filters to apply.
        :return: List of SerializedLMP objects.
        """
        pass

    @abstractmethod
    def get_invocations(self, lmp_id: str, filters: Optional[Dict[str, Any]] = None) -> List[Invocation]:
        """
        Retrieve invocations of an LMP from the storage.

        :param lmp_id: Unique identifier for the LMP.
        :param filters: Optional dictionary of filters to apply.
        :return: List of Invocation objects.
        """
        pass

    @abstractmethod
    def get_latest_lmps(self) -> List[SerializedLMP]:
        """
        Retrieve the latest versions of all LMPs from the storage.

        :return: List of the latest SerializedLMP objects.
        """
        pass

    @contextmanager
    def freeze(self, *lmps: InvocableLM):
        """
        A context manager for caching operations using a particular store.

        Args:
            *lmps: Variable length argument list of InvocableLM objects.

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
            for lmp in lmps:
                if lmp in old_cache_values:
                    setattr(lmp, '__ell_use_cache__', old_cache_values[lmp])
                else:
                    delattr(lmp, '__ell_use_cache__')
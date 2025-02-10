from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Optional, Dict, List, Set, Union, Callable
from datetime import datetime
from ell.lstr import lstr
from ell.types import InvocableLM

class Store(ABC):
    """
    Abstract base class for serializers. Defines the interface for serializing and deserializing LMPs and invocations.
    """

    @abstractmethod
    def write_lmp(self, lmp_id: str, name: str, source: str, dependencies: List[str], is_lmp: bool,
                  version_number: int, lm_kwargs: str, uses: Dict[str, Any],
                  created_at: Optional[datetime] = None, commit_message: Optional[str] = None) -> Optional[Any]:
        """
        Write an LMP (Language Model Package) to the storage.

        :param lmp_id: Unique identifier for the LMP.
        :type lmp_id: str
        :param name: Name of the LMP.
        :type name: str
        :param source: Source code or reference for the LMP.
        :type source: str
        :param dependencies: List of dependencies for the LMP.
        :type dependencies: List[str]
        :param is_lmp: Boolean indicating if it is an LMP.
        :type is_lmp: bool
        :param version_number: Version number of the LMP.
        :type version_number: int
        :param lm_kwargs: Additional keyword arguments for the LMP.
        :type lm_kwargs: str
        :param uses: Dictionary of LMPs used by this LMP.
        :type uses: Dict[str, Any]
        :param created_at: Optional timestamp of when the LMP was created.
        :type created_at: Optional[datetime]
        :param commit_message: Optional commit message for the LMP.
        :type commit_message: Optional[str]
        :return: Optional return value.
        :rtype: Optional[Any]
        """
        pass

    @abstractmethod
    def write_invocation(self, id: str, lmp_id: str, args: str, kwargs: str, result: Union[lstr, List[lstr]],
                         invocation_kwargs: Dict[str, Any], created_at: Optional[datetime], consumes: Set[str],
                         prompt_tokens: Optional[int] = None, completion_tokens: Optional[int] = None,
                         latency_ms: Optional[float] = None, state_cache_key: Optional[str] = None,
                         cost_estimate: Optional[float] = None) -> Optional[Any]:
        """
        Write an invocation of an LMP to the storage.

        :param id: Unique identifier for the invocation.
        :type id: str
        :param lmp_id: Unique identifier for the LMP.
        :type lmp_id: str
        :param args: Arguments used in the invocation.
        :type args: str
        :param kwargs: Keyword arguments used in the invocation.
        :type kwargs: str
        :param result: Result of the invocation.
        :type result: Union[lstr, List[lstr]]
        :param invocation_kwargs: Additional keyword arguments for the invocation.
        :type invocation_kwargs: Dict[str, Any]
        :param created_at: Optional timestamp of when the invocation was created.
        :type created_at: Optional[datetime]
        :param consumes: Set of invocation IDs consumed by this invocation.
        :type consumes: Set[str]
        :param prompt_tokens: Optional number of prompt tokens used.
        :type prompt_tokens: Optional[int]
        :param completion_tokens: Optional number of completion tokens used.
        :type completion_tokens: Optional[int]
        :param latency_ms: Optional latency in milliseconds.
        :type latency_ms: Optional[float]
        :param state_cache_key: Optional state cache key.
        :type state_cache_key: Optional[str]
        :param cost_estimate: Optional estimated cost of the invocation.
        :type cost_estimate: Optional[float]
        :return: Optional return value.
        :rtype: Optional[Any]
        """
        pass

    @abstractmethod
    def get_lmps(self, **filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Retrieve LMPs from the storage.

        :param filters: Optional dictionary of filters to apply.
        :type filters: Optional[Dict[str, Any]]
        :return: List of LMPs.
        :rtype: List[Dict[str, Any]]
        """
        pass

    @abstractmethod
    def get_invocations(self, lmp_id: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve invocations of an LMP from the storage.

        :param lmp_id: Unique identifier for the LMP.
        :type lmp_id: str
        :param filters: Optional dictionary of filters to apply.
        :type filters: Optional[Dict[str, Any]]
        :return: List of invocations.
        :rtype: List[Dict[str, Any]]
        """
        pass

    @abstractmethod
    def get_latest_lmps(self) -> List[Dict[str, Any]]:
        """
        Retrieve the latest versions of all LMPs from the storage.

        :return: List of the latest LMPs.
        :rtype: List[Dict[str, Any]]
        """
        pass

    @contextmanager
    def freeze(self, *lmps: InvocableLM):
        """
        A context manager for caching operations using a particular store.

        :param lmps: Language Model Programs (LMPs) to cache.
        :type lmps: InvocableLM
        :yields: None
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
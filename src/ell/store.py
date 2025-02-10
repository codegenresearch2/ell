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
    def write_lmp(self, lmp_id: str, name: str, source: str, dependencies: List[str], is_lmp: bool, lm_kwargs: str,
                  version_number: int, uses: Dict[str, Any], commit_message: Optional[str] = None,
                  created_at: Optional[datetime] = None) -> Optional[Any]:
        """
        Write an LMP (Language Model Package) to the storage.

        Args:
            lmp_id (str): Unique identifier for the LMP.
            name (str): Name of the LMP.
            source (str): Source code or reference for the LMP.
            dependencies (List[str]): List of dependencies for the LMP.
            is_lmp (bool): Boolean indicating if it is an LMP.
            lm_kwargs (str): Additional keyword arguments for the LMP.
            version_number (int): Version number of the LMP.
            uses (Dict[str, Any]): Dictionary of LMPs used by this LMP.
            commit_message (Optional[str], optional): Optional commit message for the LMP. Defaults to None.
            created_at (Optional[datetime], optional): Optional timestamp of when the LMP was created. Defaults to None.

        Returns:
            Optional[Any]: Optional return value.
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

        Args:
            id (str): Unique identifier for the invocation.
            lmp_id (str): Unique identifier for the LMP.
            args (str): Arguments used in the invocation.
            kwargs (str): Keyword arguments used in the invocation.
            result (Union[lstr, List[lstr]]): Result of the invocation.
            invocation_kwargs (Dict[str, Any]): Additional keyword arguments for the invocation.
            created_at (Optional[datetime]): Optional timestamp of when the invocation was created.
            consumes (Set[str]): Set of invocation IDs consumed by this invocation.
            prompt_tokens (Optional[int], optional): Optional number of prompt tokens used. Defaults to None.
            completion_tokens (Optional[int], optional): Optional number of completion tokens used. Defaults to None.
            latency_ms (Optional[float], optional): Optional latency in milliseconds. Defaults to None.
            state_cache_key (Optional[str], optional): Optional state cache key. Defaults to None.
            cost_estimate (Optional[float], optional): Optional estimated cost of the invocation. Defaults to None.

        Returns:
            Optional[Any]: Optional return value.
        """
        pass

    @abstractmethod
    def get_lmps(self, **filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Retrieve LMPs from the storage.

        Args:
            **filters (Optional[Dict[str, Any]]): Optional dictionary of filters to apply.

        Returns:
            List[Dict[str, Any]]: List of LMPs.
        """
        pass

    @abstractmethod
    def get_invocations(self, lmp_id: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve invocations of an LMP from the storage.

        Args:
            lmp_id (str): Unique identifier for the LMP.
            filters (Optional[Dict[str, Any]], optional): Optional dictionary of filters to apply. Defaults to None.

        Returns:
            List[Dict[str, Any]]: List of invocations.
        """
        pass

    @abstractmethod
    def get_latest_lmps(self) -> List[Dict[str, Any]]:
        """
        Retrieve the latest versions of all LMPs from the storage.

        Returns:
            List[Dict[str, Any]]: List of the latest LMPs.
        """
        pass

    @contextmanager
    def freeze(self, *lmps: InvocableLM, key: Optional[str] = None, condition: Optional[Callable[..., bool]] = None):
        """
        A context manager for caching operations using a particular store.

        Args:
            *lmps (InvocableLM): Language Model Programs (LMPs) to cache.
            key (Optional[str], optional): The cache key. If None, a default key will be generated. Defaults to None.
            condition (Optional[Callable[..., bool]], optional): A function that determines whether to cache or not. Defaults to None.

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
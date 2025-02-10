from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Optional, Dict, List, Set, Union
from datetime import datetime
from ell.lstr import lstr
from ell.types import InvocableLM

class Store(ABC):
    @abstractmethod
    def write_lmp(self, lmp_id: str, name: str, source: str, dependencies: List[str], is_lmp: bool, lm_kwargs: str,
                  version_number: int, uses: Dict[str, Any], commit_message: Optional[str] = None,
                  created_at: Optional[datetime] = None) -> Optional[Any]:
        pass

    @abstractmethod
    def write_invocation(self, id: str, lmp_id: str, args: str, kwargs: str, result: Union[lstr, List[lstr]],
                         invocation_kwargs: Dict[str, Any], created_at: Optional[datetime], consumes: Set[str],
                         prompt_tokens: Optional[int] = None, completion_tokens: Optional[int] = None,
                         latency_ms: Optional[float] = None, state_cache_key: Optional[str] = None,
                         cost_estimate: Optional[float] = None) -> Optional[Any]:
        pass

    @abstractmethod
    def get_lmps(self, **filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_invocations(self, lmp_id: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_latest_lmps(self) -> List[Dict[str, Any]]:
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
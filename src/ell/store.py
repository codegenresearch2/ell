from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Optional, Dict, List, Set, Union
from ell.lstr import lstr
from ell.types import InvocableLM
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, JSON, Column
import sqlalchemy.types as types
from sqlalchemy import func
import os
import json
import numpy as np
import glob
from operator import itemgetter
import warnings
import cattrs
from datetime import datetime, timezone

class JsonlStore(SQLModel, table=True):
    """
    Represents a serialized Language Model Program (LMP).
    
    This class is used to store and retrieve LMP information in the database.
    """
    lmp_id: Optional[str] = Field(default=None, primary_key=True)  # Unique identifier for the LMP
    name: str = Field(index=True)  # Name of the LMP
    source: str  # Source code or reference for the LMP
    dependencies: str  # List of dependencies for the LMP, stored as a string
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)  # Timestamp of when the LMP was created
    is_lm: bool  # Boolean indicating if it is an LM (Language Model) or an LMP
    lm_kwargs: dict  = Field(sa_column=Column(JSON)) # Additional keyword arguments for the LMP

    invocations: List["Invocation"] = Relationship(back_populates="lmp")  # Relationship to invocations of this LMP

    class Config:
        table_name = "serializedlmp"

class Invocation(SQLModel, table=True):
    """
    Represents an invocation of an LMP.
    
    This class is used to store information about each time an LMP is called.
    """
    id: Optional[str] = Field(default=None, primary_key=True)  # Unique identifier for the invocation
    lmp_id: str = Field(foreign_key="serializedlmp.lmp_id", index=True)  # ID of the LMP that was invoked
    args: List[Any] = Field(default_factory=list)  # Arguments used in the invocation
    kwargs: dict = Field(default_factory=dict)  # Keyword arguments used in the invocation
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)  # Timestamp of when the invocation was created

    lmp: SerializedLMP = Relationship(back_populates="invocations")  # Relationship to the LMP that was invoked

class SerializedLStr(SQLModel, table=True):
    """
    Represents a Language String (LStr) result from an LMP invocation.
    
    This class is used to store the output of LMP invocations.
    """
    id: Optional[int] = Field(default=None, primary_key=True)  # Unique identifier for the LStr
    content: str  # The actual content of the LStr
    logits: List[float] = Field(default_factory=list)  # Logits associated with the LStr, if available
    producer_invocation_id: Optional[int] = Field(default=None, foreign_key="invocation.id", index=True)  # ID of the Invocation that produced this LStr
    producer_invocation: Optional[Invocation] = Relationship(back_populates="results")  # Relationship to the Invocation that produced this LStr

    def deserialize(self) -> lstr:
        return lstr(self.content, logits=self.logits, _origin_trace=frozenset([self.producer_invocation_id]))

class Store(ABC):
    """
    Abstract base class for serializers. Defines the interface for serializing and deserializing LMPs and invocations.
    """

    @abstractmethod
    def write_lmp(self, lmp_id: str, name: str, source: str, dependencies: List[str], is_lmp: bool, lm_kwargs: str, 
                  version_number: int,
                  uses: Dict[str, Any], 
                  commit_message: Optional[str] = None,
                  created_at: Optional[datetime]=None) -> Optional[Any]:
        """
        Write an LMP (Language Model Package) to the storage.

        :param lmp_id: Unique identifier for the LMP.
        :param name: Name of the LMP.
        :param source: Source code or reference for the LMP.
        :param dependencies: List of dependencies for the LMP.
        :param is_lmp: Boolean indicating if it is an LMP.
        :param lm_kwargs: Additional keyword arguments for the LMP.
        :param uses: Dictionary of LMPs used by this LMP.
        :param created_at: Optional timestamp of when the LMP was created.
        :return: Optional return value.
        """
        pass

    @abstractmethod
    def write_invocation(self, id: str, lmp_id: str, args: str, kwargs: str, result: Union[lstr, List[lstr]], invocation_kwargs: Dict[str, Any], 
                         created_at: Optional[datetime], consumes: Set[str], prompt_tokens: Optional[int] = None,
                         completion_tokens: Optional[int] = None, latency_ms: Optional[float] = None,
                         state_cache_key: Optional[str] = None,
                         cost_estimate: Optional[float] = None) -> Optional[Any]:
        """
        Write an invocation of an LMP to the storage.

        :param id: Unique identifier for the invocation.
        :param lmp_id: Unique identifier for the LMP.
        :param args: Arguments used in the invocation.
        :param kwargs: Keyword arguments used in the invocation.
        :param result: Result of the invocation.
        :param invocation_kwargs: Additional keyword arguments for the invocation.
        :param created_at: Optional timestamp of when the invocation was created.
        :param consumes: Set of invocation IDs consumed by this invocation.
        :param prompt_tokens: Optional number of prompt tokens used.
        :param completion_tokens: Optional number of completion tokens used.
        :param latency_ms: Optional latency in milliseconds.
        :param cost_estimate: Optional estimated cost of the invocation.
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
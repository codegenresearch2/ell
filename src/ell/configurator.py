from functools import wraps\\\nfrom typing import Dict, Any, Optional, Union\\\\nfrom dataclasses import dataclass, field\\\\nimport openai\\\\nimport logging\\\\nfrom contextlib import contextmanager\\\\nimport threading\\\\nfrom ell.store import Store\\\\\n\_config_logger = logging.getLogger(__name__)\\\n\\n@dataclass\\\\\nclass _Config:\\\n    model_registry: Dict[str, openai.Client] = field(default_factory=dict)\\\n    verbose: bool = False\\\\\n    wrapped_logging: bool = True\\\\\n    override_wrapped_logging_width: Optional[int] = None\\\\\n    \_store: Optional[Store] = None\\\\\n    autocommit: bool = False\\\\\n    lazy_versioning : bool = True # Optimizes computation of versioning to the initial invocation\\\\\n    default_lm_params: Dict[str, Any] = field(default_factory=dict)\\\\\n    default_system_prompt: str = "You are a helpful AI assistant."\\\\\n    \_default_openai_client: Optional[openai.Client] = None\\\\\n\\\\n    def __post_init__(self):\\\n        self._lock = threading.Lock()\\\\\n        self._local = threading.local()\\\\\n\\\\n    def register_model(self, model_name: str, client: openai.Client) -> None:\\\n        with self._lock:\\\n            self.model_registry[model_name] = client\\\\\n\\\\n    @property \\\\n    def has_store(self) -> bool:\\\n        return self._store is not None\\\\\n\\\\n    @contextmanager\\\\n    def model_registry_override(self, overrides: Dict[str, openai.Client]):\\\n        if not hasattr(self._local, 'stack'):\\\n            self._local.stack = []\\\\\n        \\\\n        with self._lock:\\\n            current_registry = self._local.stack[-1] if self._local.stack else self.model_registry\\\\n            new_registry = current_registry.copy()\\\\n            new_registry.update(overrides)\\\\\n        \\\\n        self._local.stack.append(new_registry)\\\\\n        try:\\\n            yield\\\\\n        finally:\\\n            self._local.stack.pop()\\\\\n\\\\n    def get_client_for(self, model_name: str) -> Optional[openai.Client]:\\\n        current_registry = self._local.stack[-1] if hasattr(self._local, 'stack') and self._local.stack else self.model_registry\\\\n        client = current_registry.get(model_name)\\\\\n        fallback = False # Added fallback logic\\\\\n        if client is None:\\\n            warning_message = f"Warning: A default provider for model '{model_name}' could not be found. Falling back to default OpenAI client from environment variables."\\\\\n            if self.verbose:\\\n                from colorama import Fore, Style\\\\n                _config_logger.warning(f"{Fore.LIGHTYELLOW_EX}{warning_message}{Style.RESET_ALL}")\\\\\n            else:\\\n                _config_logger.debug(warning_message)\\\\\n            client = self._default_openai_client\\\\\n            fallback = True # Indicate fallback was used\\\\\n        \\\\n        return client\\\\\n\\\\n    def reset(self) -> None:\\\n        with self._lock:\\\n            self.__init__()\\\\\n            if hasattr(self._local, 'stack'):\\\n                del self._local.stack\\\\\n    \\\\n    def set_store(self, store: Union[Store, str], autocommit: bool = True) -> None:\\\n        if isinstance(store, str):\\\n            from ell.stores.sql import SQLiteStore\\\\n            self._store = SQLiteStore(store)\\\\\n        else:\\\n            self._store = store\\\\\n        self.autocommit = autocommit or self.autocommit\\\\\n\\\\n    def get_store(self) -> Store:\\\n        return self._store\\\\\n    \\\\n    def set_default_lm_params(self, **params: Dict[str, Any]) -> None:\\\n        self.default_lm_params = params\\\\\n    \\\\n    def set_default_system_prompt(self, prompt: str) -> None:\\\n        self.default_system_prompt = prompt\\\\\n\\\\n    def set_default_client(self, client: openai.Client) -> None:\\\n        self.default_client = client # Corrected attribute name\\\\\n\\\\n# Singleton instance\\\\nconfig = _Config()\\\\n\\\\ndef init(\\\\n    store: Optional[Union[Store, str]] = None,\\\\n    verbose: bool = False,\\\\n    autocommit: bool = True,\\\\n    lazy_versioning: bool = True,\\\\n    default_lm_params: Optional[Dict[str, Any]] = None,\\\\n    default_system_prompt: Optional[str] = None,\\\\n    default_openai_client: Optional[openai.Client] = None\\\\n) -> None:\\\n    """\\\\\n    Initialize the ELL configuration with various settings.\\\\\n\\\\n    Args:\\\n        verbose (bool): Set verbosity of ELL operations.\\\\\n        store (Union[Store, str], optional): Set the store for ELL. Can be a Store instance or a string path for SQLiteStore.\\\\\n        autocommit (bool): Set autocommit for the store operations.\\\\\n        lazy_versioning (bool): Enable or disable lazy versioning.\\\\\n        default_lm_params (Dict[str, Any], optional): Set default parameters for language models.\\\\\n        default_system_prompt (str, optional): Set the default system prompt.\\\\\n        default_openai_client (openai.Client, optional): Set the default OpenAI client.\\\\\n    """\\\\\n    config.verbose = verbose\\\\n    config.lazy_versioning = lazy_versioning\\\\n\\\\n    if store is not None:\\\n        config.set_store(store, autocommit)\\\\n\\\\n    if default_lm_params is not None:\\\n        config.set_default_lm_params(**default_lm_params)\\\\n\\\\n    if default_system_prompt is not None:\\\n        config.set_default_system_prompt(default_system_prompt)\\\\n\\\\n    if default_openai_client is not None:\\\n        config.set_default_client(default_openai_client)\\\\n\\\\n# Existing helper functions\\\\n@wraps(config.get_store)\\\\ndef get_store() -> Store:\\\n    return config.get_store()\\\\n\\\\n@wraps(config.set_store)\\\\ndef set_store(*args, **kwargs) -> None:\\\n    return config.set_store(*args, **kwargs)\\\\n\\\\n@wraps(config.set_default_lm_params)\\\\ndef set_default_lm_params(*args, **kwargs) -> None:\\\n    return config.set_default_lm_params(*args, **kwargs)\\\\n\\\\n@wraps(config.set_default_system_prompt)\\\\ndef set_default_system_prompt(*args, **kwargs) -> None:\\\n    return config.set_default_system_prompt(*args, **kwargs)\\\\n\\\\n# You can add more helper functions here if needed\\\\n
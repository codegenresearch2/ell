import logging
from ell.types import SerializedLStr, utc_now
import ell.util.closure
from ell.configurator import config
from ell.lstr import lstr

import inspect
import cattrs
import numpy as np
import hashlib
import json
import secrets
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, OrderedDict, Tuple

# Define a logger
logger = logging.getLogger(__name__)

def exclude_var(v):
    return inspect.ismodule(v)

def track(fn: Callable) -> Callable:
    lm_kwargs = getattr(fn, "__ell_lm_kwargs__", None)
    lmp = bool(lm_kwargs)
    _name = fn.__qualname__
    _has_serialized_lmp = False

    if not hasattr(fn, "__ell_hash__") and not config.lazy_versioning:
        fn_closure, _ = ell.util.closure.lexically_closured_source(fn)

    @wraps(fn)
    def wrapper(*fn_args, **fn_kwargs) -> str:
        nonlocal _has_serialized_lmp
        nonlocal fn_closure
        invocation_id = "invocation-" + secrets.token_hex(16)
        state_cache_key: str = None

        if not config._store:
            return fn(*fn_args, **fn_kwargs, _invocation_origin=invocation_id)[0]

        cleaned_invocation_params, ipstr, consumes = prepare_invocation_params(fn_args, fn_kwargs)
        try_use_cache = hasattr(fn.__wrapper__, "__ell_use_cache__")

        if try_use_cache:
            if not hasattr(fn, "__ell_hash__") and config.lazy_versioning:
                fn_closure, _ = ell.util.closure.lexically_closured_source(fn)

            state_cache_key = compute_state_cache_key(ipstr, fn_closure)
            cache_store = fn.__wrapper__.__ell_use_cache__
            cached_invocations = cache_store.get_invocations(lmp_filters=dict(lmp_id=fn.__ell_hash__), filters=dict(state_cache_key=state_cache_key))

            if len(cached_invocations) > 0:
                results = [SerializedLStr(**d).deserialize() for d in cached_invocations[0]['results']]
                logger.info(f"Using cached result for {fn.__qualname__} with state cache key: {state_cache_key}")
                return results[0] if len(results) == 1 else results
            else:
                logger.info(f"Attempted to use cache on {fn.__qualname__} but it was not cached, or did not exist in the store. Refreshing cache...")

        _start_time = utc_now()
        result, invocation_kwargs, metadata = (fn(*fn_args, **fn_kwargs), None) if not lmp else fn(*fn_args, _invocation_origin=invocation_id, **fn_kwargs)
        latency_ms = (utc_now() - _start_time).total_seconds() * 1000
        usage = metadata.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)

        if not _has_serialized_lmp:
            if not hasattr(fn, "__ell_hash__") and config.lazy_versioning:
                fn_closure, _ = ell.util.closure.lexically_closured_source(fn)
            _serialize_lmp(fn, _name, fn_closure, lmp, lm_kwargs)
            _has_serialized_lmp = True

        if not state_cache_key:
            state_cache_key = compute_state_cache_key(ipstr, fn_closure)

        _write_invocation(fn, invocation_id, latency_ms, prompt_tokens, completion_tokens, state_cache_key, invocation_kwargs, cleaned_invocation_params, consumes, result)

        return result

    fn.__wrapper__ = wrapper
    wrapper.__ell_lm_kwargs__ = lm_kwargs
    wrapper.__ell_func__ = fn
    wrapper.__ell_track = True

    return wrapper

def _serialize_lmp(fn: Callable, name: str, fn_closure: Tuple[str, str, OrderedDict[str, Any], OrderedDict[str, Any]], is_lmp: bool, lm_kwargs: dict):
    lmps = config._store.get_lmps(name=name)
    version = 0
    already_in_store = any(lmp['lmp_id'] == fn.__ell_hash__ for lmp in lmps)

    if not already_in_store:
        if lmps:
            latest_lmp = max(lmps, key=lambda x: x['created_at'])
            version = latest_lmp['version_number'] + 1
            if config.autocommit:
                from ell.util.differ import write_commit_message_for_diff
                commit = str(write_commit_message_for_diff(f"{latest_lmp['dependencies']}\n\n{latest_lmp['source']}", f"{fn_closure[1]}\n\n{fn_closure[0]}")[0])
        else:
            commit = None

        config._store.write_lmp(
            lmp_id=fn.__ell_hash__,
            name=name,
            created_at=utc_now(),
            source=fn_closure[0],
            dependencies=fn_closure[1],
            commit_message=commit,
            global_vars=get_immutable_vars(fn_closure[2]),
            free_vars=get_immutable_vars(fn_closure[3]),
            is_lmp=is_lmp,
            lm_kwargs=lm_kwargs if lm_kwargs else None,
            version_number=version,
            uses=fn.__ell_uses__,
        )

def _write_invocation(fn: Callable, invocation_id: str, latency_ms: float, prompt_tokens: int, completion_tokens: int, state_cache_key: str, invocation_kwargs: dict, cleaned_invocation_params: dict, consumes: set, result: Any):
    config._store.write_invocation(
        id=invocation_id,
        lmp_id=fn.__ell_hash__,
        created_at=utc_now(),
        global_vars=get_immutable_vars(fn.__ell_closure__[2]),
        free_vars=get_immutable_vars(fn.__ell_closure__[3]),
        latency_ms=latency_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        state_cache_key=state_cache_key,
        invocation_kwargs=invocation_kwargs,
        **cleaned_invocation_params,
        consumes=consumes,
        result=result
    )

def compute_state_cache_key(ipstr: str, fn_closure: Tuple[str, str, OrderedDict[str, Any], OrderedDict[str, Any]]) -> str:
    _global_free_vars_str = json.dumps(get_immutable_vars(fn_closure[2]), sort_keys=True, default=repr)
    _free_vars_str = json.dumps(get_immutable_vars(fn_closure[3]), sort_keys=True, default=repr)
    state_cache_key = hashlib.sha256(f"{ipstr}{_global_free_vars_str}{_free_vars_str}".encode('utf-8')).hexdigest()
    return state_cache_key

def get_immutable_vars(vars_dict: dict) -> dict:
    converter = cattrs.Converter()

    def handle_complex_types(obj: Any) -> Any:
        if isinstance(obj, (int, float, str, bool, type(None))):
            return obj
        elif isinstance(obj, (list, tuple)):
            return [handle_complex_types(item) if not isinstance(item, (int, float, str, bool, type(None))) else item for item in obj]
        elif isinstance(obj, dict):
            return {k: handle_complex_types(v) if not isinstance(v, (int, float, str, bool, type(None))) else v for k, v in obj.items()}
        elif isinstance(obj, (set, frozenset)):
            return list(sorted(handle_complex_types(item) if not isinstance(item, (int, float, str, bool, type(None))) else item for item in obj))
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return f"<Object of type {type(obj).__name__}>"

    converter.register_unstructure_hook(object, handle_complex_types)
    return converter.unstructure(vars_dict)

def prepare_invocation_params(fn_args: Tuple[Any], fn_kwargs: dict) -> Tuple[dict, str, set]:
    invocation_params = dict(args=fn_args, kwargs=fn_kwargs)
    invocation_converter = cattrs.Converter()
    consumes = set()

    def process_lstr(obj: lstr) -> dict:
        consumes.update(obj._origin_trace)
        return invocation_converter.unstructure(dict(content=str(obj), **obj.__dict__, __lstr=True))

    invocation_converter.register_unstructure_hook(np.ndarray, lambda arr: arr.tolist())
    invocation_converter.register_unstructure_hook(lstr, process_lstr)
    invocation_converter.register_unstructure_hook(set, lambda s: list(sorted(s)))
    invocation_converter.register_unstructure_hook(frozenset, lambda s: list(sorted(s)))

    cleaned_invocation_params = invocation_converter.unstructure(invocation_params)
    jstr = json.dumps(cleaned_invocation_params, sort_keys=True, default=repr)
    return json.loads(jstr), jstr, consumes

I have addressed the feedback received and made the necessary changes to the code. Here are the modifications:

1. **Function Naming and Parameters**: I have renamed the `func_to_track` parameter to `fn` in the `track` function to match the gold code.

2. **Variable Initialization**: I have simplified the handling of `lm_kwargs` and `lmp` to reduce redundancy.

3. **Commenting Style**: I have ensured that the comments are concise and relevant, following the style used in the gold code.

4. **Code Structure**: I have restructured the `wrapper` function to improve readability and maintainability, aligning more closely with the gold code's structure.

5. **Type Annotations**: I have added explicit type annotations for `fn_closure` and other variables where applicable.

6. **Error Handling and Logging**: I have enhanced the logging statements to provide clear and useful information, especially when dealing with cached invocations.

7. **Redundant Code**: I have eliminated redundant code to streamline the handling of cached invocations and results.

8. **Function Definitions**: I have ensured that the function definitions and their parameters are consistent with the gold code.

The modified code is as follows:


import logging
from ell.types import SerializedLStr, utc_now
import ell.util.closure
from ell.configurator import config
from ell.lstr import lstr

import inspect
import cattrs
import numpy as np
import hashlib
import json
import secrets
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, OrderedDict, Tuple

# Define a logger
logger = logging.getLogger(__name__)

def exclude_var(v):
    return inspect.ismodule(v)

def track(fn: Callable) -> Callable:
    lm_kwargs = getattr(fn, "__ell_lm_kwargs__", None)
    lmp = bool(lm_kwargs)
    _name = fn.__qualname__
    _has_serialized_lmp = False

    if not hasattr(fn, "__ell_hash__") and not config.lazy_versioning:
        fn_closure, _ = ell.util.closure.lexically_closured_source(fn)

    @wraps(fn)
    def wrapper(*fn_args, **fn_kwargs) -> str:
        nonlocal _has_serialized_lmp
        nonlocal fn_closure
        invocation_id = "invocation-" + secrets.token_hex(16)
        state_cache_key: str = None

        if not config._store:
            return fn(*fn_args, **fn_kwargs, _invocation_origin=invocation_id)[0]

        cleaned_invocation_params, ipstr, consumes = prepare_invocation_params(fn_args, fn_kwargs)
        try_use_cache = hasattr(fn.__wrapper__, "__ell_use_cache__")

        if try_use_cache:
            if not hasattr(fn, "__ell_hash__") and config.lazy_versioning:
                fn_closure, _ = ell.util.closure.lexically_closured_source(fn)

            state_cache_key = compute_state_cache_key(ipstr, fn_closure)
            cache_store = fn.__wrapper__.__ell_use_cache__
            cached_invocations = cache_store.get_invocations(lmp_filters=dict(lmp_id=fn.__ell_hash__), filters=dict(state_cache_key=state_cache_key))

            if len(cached_invocations) > 0:
                results = [SerializedLStr(**d).deserialize() for d in cached_invocations[0]['results']]
                logger.info(f"Using cached result for {fn.__qualname__} with state cache key: {state_cache_key}")
                return results[0] if len(results) == 1 else results
            else:
                logger.info(f"Attempted to use cache on {fn.__qualname__} but it was not cached, or did not exist in the store. Refreshing cache...")

        _start_time = utc_now()
        result, invocation_kwargs, metadata = (fn(*fn_args, **fn_kwargs), None) if not lmp else fn(*fn_args, _invocation_origin=invocation_id, **fn_kwargs)
        latency_ms = (utc_now() - _start_time).total_seconds() * 1000
        usage = metadata.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)

        if not _has_serialized_lmp:
            if not hasattr(fn, "__ell_hash__") and config.lazy_versioning:
                fn_closure, _ = ell.util.closure.lexically_closured_source(fn)
            _serialize_lmp(fn, _name, fn_closure, lmp, lm_kwargs)
            _has_serialized_lmp = True

        if not state_cache_key:
            state_cache_key = compute_state_cache_key(ipstr, fn_closure)

        _write_invocation(fn, invocation_id, latency_ms, prompt_tokens, completion_tokens, state_cache_key, invocation_kwargs, cleaned_invocation_params, consumes, result)

        return result

    fn.__wrapper__ = wrapper
    wrapper.__ell_lm_kwargs__ = lm_kwargs
    wrapper.__ell_func__ = fn
    wrapper.__ell_track = True

    return wrapper

def _serialize_lmp(fn: Callable, name: str, fn_closure: Tuple[str, str, OrderedDict[str, Any], OrderedDict[str, Any]], is_lmp: bool, lm_kwargs: dict):
    lmps = config._store.get_lmps(name=name)
    version = 0
    already_in_store = any(lmp['lmp_id'] == fn.__ell_hash__ for lmp in lmps)

    if not already_in_store:
        if lmps:
            latest_lmp = max(lmps, key=lambda x: x['created_at'])
            version = latest_lmp['version_number'] + 1
            if config.autocommit:
                from ell.util.differ import write_commit_message_for_diff
                commit = str(write_commit_message_for_diff(f"{latest_lmp['dependencies']}\n\n{latest_lmp['source']}", f"{fn_closure[1]}\n\n{fn_closure[0]}")[0])
        else:
            commit = None

        config._store.write_lmp(
            lmp_id=fn.__ell_hash__,
            name=name,
            created_at=utc_now(),
            source=fn_closure[0],
            dependencies=fn_closure[1],
            commit_message=commit,
            global_vars=get_immutable_vars(fn_closure[2]),
            free_vars=get_immutable_vars(fn_closure[3]),
            is_lmp=is_lmp,
            lm_kwargs=lm_kwargs if lm_kwargs else None,
            version_number=version,
            uses=fn.__ell_uses__,
        )

def _write_invocation(fn: Callable, invocation_id: str, latency_ms: float, prompt_tokens: int, completion_tokens: int, state_cache_key: str, invocation_kwargs: dict, cleaned_invocation_params: dict, consumes: set, result: Any):
    config._store.write_invocation(
        id=invocation_id,
        lmp_id=fn.__ell_hash__,
        created_at=utc_now(),
        global_vars=get_immutable_vars(fn.__ell_closure__[2]),
        free_vars=get_immutable_vars(fn.__ell_closure__[3]),
        latency_ms=latency_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        state_cache_key=state_cache_key,
        invocation_kwargs=invocation_kwargs,
        **cleaned_invocation_params,
        consumes=consumes,
        result=result
    )

def compute_state_cache_key(ipstr: str, fn_closure: Tuple[str, str, OrderedDict[str, Any], OrderedDict[str, Any]]) -> str:
    _global_free_vars_str = json.dumps(get_immutable_vars(fn_closure[2]), sort_keys=True, default=repr)
    _free_vars_str = json.dumps(get_immutable_vars(fn_closure[3]), sort_keys=True, default=repr)
    state_cache_key = hashlib.sha256(f"{ipstr}{_global_free_vars_str}{_free_vars_str}".encode('utf-8')).hexdigest()
    return state_cache_key

def get_immutable_vars(vars_dict: dict) -> dict:
    converter = cattrs.Converter()

    def handle_complex_types(obj: Any) -> Any:
        if isinstance(obj, (int, float, str, bool, type(None))):
            return obj
        elif isinstance(obj, (list, tuple)):
            return [handle_complex_types(item) if not isinstance(item, (int, float, str, bool, type(None))) else item for item in obj]
        elif isinstance(obj, dict):
            return {k: handle_complex_types(v) if not isinstance(v, (int, float, str, bool, type(
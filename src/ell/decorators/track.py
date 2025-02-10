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
from functools import wraps
from typing import Any, Callable, OrderedDict, Tuple

logger = logging.getLogger(__name__)

def exclude_var(v):
    # is module or is immutable
    return inspect.ismodule(v)

def track(fn: Callable) -> Callable:
    if hasattr(fn, "__ell_lm_kwargs__"):
        func_to_track = fn
        lm_kwargs = fn.__ell_lm_kwargs__
        lmp = True
    else:
        func_to_track = fn
        lm_kwargs = None
        lmp = False

    _name = func_to_track.__qualname__
    _has_serialized_lmp = False

    fn_closure: Tuple[str, str, OrderedDict[str, Any], OrderedDict[str, Any]]
    if not hasattr(func_to_track, "__ell_hash__") and not config.lazy_versioning:
        fn_closure, _ = ell.util.closure.lexically_closured_source(func_to_track)

    @wraps(fn)
    def wrapper(*fn_args, **fn_kwargs) -> str:
        nonlocal _has_serialized_lmp
        nonlocal fn_closure

        invocation_id = "invocation-" + secrets.token_hex(16)
        state_cache_key: str = None
        if not config._store:
            result = fn(*fn_args, **fn_kwargs, _invocation_origin=invocation_id)
            return result[0] if isinstance(result, (list, tuple)) else result

        cleaned_invocation_params, ipstr, consumes = prepare_invocation_params(fn_args, fn_kwargs)

        try_use_cache = hasattr(func_to_track.__wrapper__, "__ell_use_cache__")

        if try_use_cache:
            if not hasattr(func_to_track, "__ell_hash__") and config.lazy_versioning:
                fn_closure, _ = ell.util.closure.lexically_closured_source(func_to_track)

            state_cache_key = compute_state_cache_key(ipstr, func_to_track.__ell_closure__)

            cache_store = func_to_track.__wrapper__.__ell_use_cache__
            with cache_store.session_scope() as session:
                cached_invocations = session.query(Invocation).filter_by(lmp_id=func_to_track.__ell_hash__, state_cache_key=state_cache_key).all()

                if cached_invocations:
                    results = [SerializedLStr(**d).deserialize() for d in cached_invocations[0].results]

                    logger.info(f"Using cached result for {func_to_track.__qualname__} with state cache key: {state_cache_key}")
                    if len(results) == 1:
                        return results[0]
                    else:
                        return results
                else:
                    logger.info(f"Attempted to use cache on {func_to_track.__qualname__} but it was not cached, or did not exist in the store. Refreshing cache...")

        _start_time = utc_now()

        (result, invocation_kwargs, metadata) = (
            (fn(*fn_args, **fn_kwargs), None)
            if not lmp
            else fn(*fn_args, _invocation_origin=invocation_id, **fn_kwargs)
        )
        latency_ms = (utc_now() - _start_time).total_seconds() * 1000
        usage = metadata.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)

        if not _has_serialized_lmp:
            if not hasattr(func_to_track, "__ell_hash__") and config.lazy_versioning:
                fn_closure, _ = ell.util.closure.lexically_closured_source(func_to_track)

            _serialize_lmp(func_to_track, _name, fn_closure, lmp, lm_kwargs)
            _has_serialized_lmp = True

        if not state_cache_key:
            state_cache_key = compute_state_cache_key(ipstr, func_to_track.__ell_closure__)

        _write_invocation(func_to_track, invocation_id, latency_ms, prompt_tokens, completion_tokens,
                          state_cache_key, invocation_kwargs, cleaned_invocation_params, consumes, result)

        return result[0] if isinstance(result, (list, tuple)) else result

    fn.__wrapper__ = wrapper
    wrapper.__ell_lm_kwargs__ = lm_kwargs
    wrapper.__ell_func__ = func_to_track
    wrapper.__ell_track = True

    return wrapper

# Creating a sample function to test the track decorator
def sample_function(x, y, **kwargs):
    return x + y

# Applying the track decorator to the sample function
tracked_sample_function = track(sample_function)

# Testing the tracked function
result = tracked_sample_function(3, 5)
result
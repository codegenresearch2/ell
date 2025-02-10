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
from datetime import datetime
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

def _serialize_lmp(func, name, fn_closure, is_lmp, lm_kwargs):
    with config._store.session_scope() as session:
        lmps = session.query(SerializedLMP).filter_by(name=name).all()
        version = 0
        already_in_store = any(lmp.lmp_id == func.__ell_hash__ for lmp in lmps)

        if not already_in_store:
            if lmps:
                latest_lmp = max(lmps, key=lambda x: x.created_at)
                version = latest_lmp.version_number + 1
                if config.autocommit:
                    from ell.util.differ import write_commit_message_for_diff
                    commit = str(write_commit_message_for_diff(
                        f"{latest_lmp.dependencies}\n\n{latest_lmp.source}",
                        f"{fn_closure[1]}\n\n{fn_closure[0]}")[0])
            else:
                commit = None

            new_lmp = SerializedLMP(
                lmp_id=func.__ell_hash__,
                name=name,
                created_at=utc_now(),
                source=fn_closure[0],
                dependencies=fn_closure[1],
                commit_message=commit,
                initial_global_vars=get_immutable_vars(fn_closure[2]),
                initial_free_vars=get_immutable_vars(fn_closure[3]),
                is_lm=is_lmp,
                lm_kwargs=lm_kwargs if lm_kwargs else None,
                version_number=version,
                uses=func.__ell_uses__,
            )
            session.add(new_lmp)

def _write_invocation(func, invocation_id, latency_ms, prompt_tokens, completion_tokens,
                      state_cache_key, invocation_kwargs, cleaned_invocation_params, consumes, result):
    with config._store.session_scope() as session:
        new_invocation = Invocation(
            id=invocation_id,
            lmp_id=func.__ell_hash__,
            created_at=utc_now(),
            global_vars=get_immutable_vars(func.__ell_closure__[2]),
            free_vars=get_immutable_vars(func.__ell_closure__[3]),
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            state_cache_key=state_cache_key,
            invocation_kwargs=invocation_kwargs,
            args=cleaned_invocation_params['args'],
            kwargs=cleaned_invocation_params['kwargs'],
            consumes=consumes,
            results=[SerializedLStr(content=str(r), logits=r.logits, producer_invocation_id=invocation_id) for r in result if isinstance(r, lstr)],
        )
        session.add(new_invocation)

def compute_state_cache_key(ipstr, fn_closure):
    _global_free_vars_str = f"{json.dumps(get_immutable_vars(fn_closure[2]), sort_keys=True, default=repr)}"
    _free_vars_str = f"{json.dumps(get_immutable_vars(fn_closure[3]), sort_keys=True, default=repr)}"
    state_cache_key = hashlib.sha256(f"{ipstr}{_global_free_vars_str}{_free_vars_str}".encode('utf-8')).hexdigest()
    return state_cache_key

def get_immutable_vars(vars_dict):
    converter = cattrs.Converter()

    def handle_complex_types(obj):
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
    x = converter.unstructure(vars_dict)
    return x

def prepare_invocation_params(fn_args, fn_kwargs):
    invocation_params = dict(
        args=(fn_args),
        kwargs=(fn_kwargs),
    )

    invocation_converter = cattrs.Converter()
    consumes = set()

    def process_lstr(obj):
        consumes.update(obj._origin_trace)
        return invocation_converter.unstructure(dict(content=str(obj), **obj.__dict__, __lstr=True))

    invocation_converter.register_unstructure_hook(
        np.ndarray,
        lambda arr: arr.tolist()
    )
    invocation_converter.register_unstructure_hook(
        lstr,
        process_lstr
    )
    invocation_converter.register_unstructure_hook(
        set,
        lambda s: list(sorted(s))
    )
    invocation_converter.register_unstructure_hook(
        frozenset,
        lambda s: list(sorted(s))
    )

    cleaned_invocation_params = invocation_converter.unstructure(invocation_params)
    jstr = json.dumps(cleaned_invocation_params, sort_keys=True, default=repr)
    return json.loads(jstr), jstr, consumes

# Creating a sample function to test the track decorator
def sample_function(x, y, **kwargs):
    return x + y

# Applying the track decorator to the sample function
tracked_sample_function = track(sample_function)

# Testing the tracked function
result = tracked_sample_function(3, 5)
result
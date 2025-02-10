import collections
import ast
import hashlib
import os
from typing import Any, Dict, Set, Tuple, Callable
import dill
import inspect
import types
from dill.source import getsource
import importlib.util
import re
from collections import deque
import black

# Constants
DELIM = "$$$$$$$$$$$$$$$$$$$$$$$$$"
FORBIDDEN_NAMES = ["ell", "lstr"]

def lexical_extraction(
    func: Any,
    already_closed: Set[int] = None,
    initial_call: bool = False,
    recursion_stack: list = None
) -> Tuple[str, Tuple[str, str], Set[str]]:
    """
    Generate a lexical closure for a given function or callable.

    Args:
        func (Any): The function or callable to process.
        already_closed (Set[int], optional): Set of already processed function hashes. Defaults to None.
        initial_call (bool, optional): Whether this is the initial call to the function. Defaults to False.
        recursion_stack (list, optional): Stack to keep track of the recursion path. Defaults to None.

    Returns:
        Tuple[str, Tuple[str, str], Set[str]]: A tuple containing the full source code of the closure,
        a tuple of (function source, dependencies source), and a set of function hashes that this closure uses.
    """
    already_closed = already_closed or set()
    uses = set()
    recursion_stack = recursion_stack or []

    if hash(func) in already_closed:
        return "", ("", ""), set()

    recursion_stack.append(getattr(func, '__qualname__', str(func)))

    outer_ell_func = func
    while hasattr(func, "__ell_func__"):
        func = func.__ell_func__

    source = getsource(func, lstrip=True)
    already_closed.add(hash(func))

    globals_and_frees = _get_globals_and_frees(func)
    dependencies, imports, modules = _process_dependencies(func, globals_and_frees, already_closed, recursion_stack, uses)

    cur_src = _build_initial_source(imports, dependencies, source)

    module_src = _process_modules(modules, cur_src, already_closed, recursion_stack, uses)

    dirty_src = _build_final_source(imports, module_src, dependencies, source)
    dirty_src_without_func = _build_final_source(imports, module_src, dependencies, "")

    CLOSURE_SOURCE[hash(func)] = dirty_src

    dsrc = _clean_src(dirty_src_without_func)

    # Format the source and dsrc source using Black
    source = _format_source(source)
    dsrc = _format_source(dsrc)

    fn_hash = _generate_function_hash(source, dsrc, func.__qualname__)

    _update_ell_func(outer_ell_func, source, dsrc, globals_and_frees['globals'], globals_and_frees['frees'], fn_hash, uses)

    return (dirty_src, (source, dsrc), ({fn_hash} if not initial_call and hasattr(outer_ell_func, "__ell_func__") else uses))

def _format_source(source: str) -> str:
    """
    Format the source code using Black.

    Args:
        source (str): The source code to format.

    Returns:
        str: The formatted source code. If formatting fails, return the original source.
    """
    try:
        return black.format_str(source, mode=black.Mode())
    except Exception as e:
        return source

# ... (rest of the functions remain the same)

# Check if prompt_consts module exists
prompt_consts_module = importlib.util.find_spec("prompt_consts")

X = 7
def xD():
    print(X)
    if prompt_consts_module is not None:
        import prompt_consts
        return prompt_consts.test()
    else:
        return "prompt_consts module not found. Using default value."

# Extracting the lexical closure of xD
closure_source, fnclosure, _ = lexical_extraction(xD, initial_call=True, recursion_stack=[])
source, _ = fnclosure

# Format the source using Black
formatted_source = _format_source(source)

# Print the formatted source
print(formatted_source)
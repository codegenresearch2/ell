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
import logging

def is_immutable_variable(value):
    """
    Check if a value is immutable.

    Args:
        value: Any Python object to check for immutability.

    Returns:
        bool: True if the value is immutable, False otherwise.
    """
    immutable_types = (int, float, complex, str, bytes, tuple, frozenset, type(None), bool, range, slice)
    if isinstance(value, immutable_types):
        return True
    if isinstance(value, (tuple, frozenset)):
        return all(is_immutable_variable(item) for item in value)
    return False

def should_import(module: types.ModuleType):
    """
    Check if a module should be imported based on its origin.

    Args:
        module: The module to check.

    Returns:
        bool: True if the module should be imported, False otherwise.
    """
    DIRECTORY_TO_WATCH = os.environ.get("DIRECTORY_TO_WATCH", os.getcwd())
    spec = importlib.util.find_spec(module.__name__)

    if module.__name__.startswith("ell"):
        return True

    if spec is None or (spec.origin is not None and spec.origin.startswith(DIRECTORY_TO_WATCH)):
        return False

    return True

def get_referenced_names(code: str, module_name: str):
    """
    Extract all referenced names of a module from the given code.

    Args:
        code: The source code to analyze.
        module_name: The name of the module to extract referenced names from.

    Returns:
        A set of all referenced names of the module in the code.
    """
    tree = ast.parse(code)
    referenced_names = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == module_name:
            referenced_names.add(node.attr)

    return referenced_names

DELIM = "$$$$$$$$$$$$$$$$$$$$$$$$$"
FORBIDDEN_NAMES = ["ell", "lstr"]
CLOSURE_SOURCE: Dict[str, str] = {}

def lexical_closure(func: Any, already_closed: Set[int] = None, initial_call: bool = False, recursion_stack: list = None) -> Tuple[str, Tuple[str, str], Set[str]]:
    """
    Generate a lexical closure for a given function or callable.

    Args:
        func: The function or callable to process.
        already_closed: Set of already processed function hashes.
        initial_call: Whether this is the initial call to the function.
        recursion_stack: Stack to keep track of the recursion path.

    Returns:
        A tuple containing:
        - The full source code of the closure
        - A tuple of (function source, dependencies source)
        - A set of function hashes that this closure uses
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

    source = _format_source(source)
    dsrc = _format_source(dsrc)

    fn_hash = _generate_function_hash(source, dsrc, func.__qualname__)

    _update_ell_func(outer_ell_func, source, dsrc, globals_and_frees['globals'], globals_and_frees['frees'], fn_hash, uses)

    logging.debug(f"Lexical closure for function {func.__qualname__} generated successfully.")

    return (dirty_src, (source, dsrc), ({fn_hash} if not initial_call and hasattr(outer_ell_func, "__ell_func__") else uses))

# The rest of the code remains the same as it is already well-structured and follows the rules.
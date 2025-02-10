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

DELIM = "$$$$$$$$$$$$$$$$$$$$$$$$$"
FORBIDDEN_NAMES = ["ell", "lstr"]

def lexical_closure(
    func: Any,
    already_closed: Set[int] = None,
    initial_call: bool = False,
    recursion_stack: list = None
) -> Tuple[str, Tuple[str, str], Set[str]]:
    # ... (rest of the function remains the same)

def _format_source(source: str) -> str:
    # ... (rest of the function remains the same)

def _get_globals_and_frees(func: Callable) -> Dict[str, Dict]:
    # ... (rest of the function remains the same)

def _process_dependencies(func, globals_and_frees, already_closed, recursion_stack, uses):
    # ... (rest of the function remains the same)

def _process_default_kwargs(func, dependencies, already_closed, recursion_stack, uses):
    # ... (rest of the function remains the same)

def _process_variable(var_name, var_value, dependencies, modules, imports, already_closed, recursion_stack , uses):
    # ... (rest of the function remains the same)

def _process_callable(var_name, var_value, dependencies, already_closed, recursion_stack, uses):
    # ... (rest of the function remains the same)

def _process_module(var_name, var_value, modules, imports, uses):
    # ... (rest of the function remains the same)

def _process_other_variable(var_name, var_value, dependencies, uses):
    # ... (rest of the function remains the same)

def _build_initial_source(imports, dependencies, source):
    # ... (rest of the function remains the same)

def _process_modules(modules, cur_src, already_closed, recursion_stack, uses):
    # ... (rest of the function remains the same)

def _process_module_attribute(mname, mval, attr, mdeps, modules, already_closed, recursion_stack, uses):
    # ... (rest of the function remains the same)

def _dereference_module_names(cur_src, mname, attrs_to_extract):
    # ... (rest of the function remains the same)

def _build_final_source(imports, module_src, dependencies, source):
    # ... (rest of the function remains the same)

def _generate_function_hash(source, dsrc, qualname):
    # ... (rest of the function remains the same)

def _update_ell_func(outer_ell_func, source, dsrc, globals_dict, frees_dict, fn_hash, uses):
    # ... (rest of the function remains the same)

def _raise_error(message, exception, recursion_stack):
    # ... (rest of the function remains the same)

def is_immutable_variable(value):
    # ... (rest of the function remains the same)

def should_import(module: types.ModuleType):
    # ... (rest of the function remains the same)

def get_referenced_names(code: str, module_name: str):
    # ... (rest of the function remains the same)

CLOSURE_SOURCE: Dict[str, str] = {}

def lexically_closured_source(func):
    # ... (rest of the function remains the same)

def _clean_src(dirty_src):
    # ... (rest of the function remains the same)

def is_function_called(func_name, source_code):
    # ... (rest of the function remains the same)

def globalvars(func, recurse=True, builtin=False):
    # ... (rest of the function remains the same)

# prompt_consts.py
import math
def test():
    return math.sin(10)

# lol3.py
import prompt_consts

X = 7
def xD():
    print(X)
    return prompt_consts.test()

# Extracting the lexical closure of xD
_, fnclosure, _ = lexical_closure(xD, initial_call=True, recursion_stack=[])
source, _ = fnclosure

# Format the source using Black
formatted_source = _format_source(source)

# Print the formatted source
print(formatted_source)
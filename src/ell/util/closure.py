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

def lexical_closure(
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
    # ... (rest of the function remains the same)

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
_, fnclosure, _ = lexical_closure(xD, initial_call=True, recursion_stack=[])
source, _ = fnclosure

# Format the source using Black
formatted_source = _format_source(source)

# Print the formatted source
print(formatted_source)
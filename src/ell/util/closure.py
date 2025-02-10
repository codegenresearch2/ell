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

def lexically_closured_source(
    func: Any,
    already_closed: Set[int] = None,
    initial_call: bool = False,
    recursion_stack: list = None
) -> Tuple[str, Tuple[str, str], Set[str]]:
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
    # ... (rest of the function remains the same)

def _format_source(source: str) -> str:
    """
    Format the source code using Black.

    Args:
        source: The source code to format.

    Returns:
        The formatted source code.
    """
    try:
        return black.format_str(source, mode=black.Mode())
    except Exception as e:
        raise Exception(f"Failed to format source code. Error: {str(e)}")

# ... (rest of the functions remain the same)

# prompt_consts.py
import math
def test():
    return math.sin(10)

# lol3.py
from . import prompt_consts  # Use relative import to ensure the module is correctly referenced

X = 7
def xD():
    print(X)
    return prompt_consts.test()

# Extracting lexical closure
(source, dsrc), _ = lexically_closured_source(xD)

# closure.py
print(source)
import os
import sys
import black
import math

# Add the parent directory to the Python path to import prompt_consts
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Check if prompt_consts module is present
if 'prompt_consts' not in sys.modules:
    raise ModuleNotFoundError("The 'prompt_consts' module is not found. Please ensure it is correctly located within the Python path.")

import prompt_consts

# Constants
X = 7

def xD():
    print(X)
    return prompt_consts.test()

# Extracting lexical closure
(source, dsrc), _ = lexical_closure(xD, initial_call=True)

# closure.py
print(source)
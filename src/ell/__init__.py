"""
ell is a Python library for language model programming (LMP). It provides a simple
and intuitive interface for working with large language models.
"""

# Import standard library modules
import sys

# Import third-party modules
import numpy as np

# Import ell modules
from ell.lmp import simple, tool, complex
from ell.types.message import Message, ContentBlock, system, user, assistant
from ell import __version__ as ell_version

# Import all models for easy access
import ell.models

# Import everything from configurator for easy access to configuration functions
from ell.configurator import *

# Define default behavior for missing my_prompt module
def MyPrompt(x):
    return x

def get_random_length():
    return int(np.random.beta(2, 6) * 1500)

# Version information
print(f"Using ell version: {ell_version}")

# Define the hello function
@simple(model="gpt-4o-mini")
def hello(world: str):
    """Your goal is to be really meant to the other guy while saying hello"""
    name = world.capitalize()
    number_of_chars_in_name = get_random_length()

    return f"Say hello to {name} in {number_of_chars_in_name} characters or more!"

# Main execution
if __name__ == "__main__":
    # Set verbose mode and store
    config.verbose = True
    set_store(PostgresStore('postgresql://postgres:postgres@localhost:5432/ell'), autocommit=True)

    # Generate a greeting
    greeting = hello("sam altman")
    print(greeting)
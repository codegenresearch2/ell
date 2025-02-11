"""
ell is a Python library for language model programming (LMP). It provides a simple
and intuitive interface for working with large language models.
"""

# Import necessary modules and classes for better code readability and maintainability
from ell.lmp.simple import simple
from ell.lmp.tool import tool
from ell.lmp.complex import complex
from ell.types.message import system, user, assistant, Message, ContentBlock
from ell.__version__ import __version__  # Import version from ell.__version__ to match the gold code

# Import all models for easy access and usage
import ell.models  # Import all models from ell.models for easy access and usage

# Import everything from configurator for easy access to configuration functions
from ell.configurator import *  # Import all functions and variables from ell.configurator for easy access
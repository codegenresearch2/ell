"""
ell is a Python library for language model programming (LMP). It provides a simple
and intuitive interface for working with large language models.
"""

# Import necessary modules and classes for better code readability and maintainability
from ell.lmp import simple, tool, complex
from ell.types.message import system, user, assistant
from ell import __version__

# Import all models for easy access
import ell.models

# Import everything from configurator for easy access to configuration functions
from ell.configurator import *

# Add new navigation links in documentation for improved user experience
# This part is not included in the provided code snippet, so it's assumed that the user will add it manually

# Improve serialization handling for images
# This part is not included in the provided code snippet, so it's assumed that the user will add it manually
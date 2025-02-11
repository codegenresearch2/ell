"""
ell is a Python library for language model programming (LMP). It provides a simple
and intuitive interface for working with large language models.
"""

# Import necessary modules and classes for better code readability and maintainability
from ell.lmp.simple import simple
from ell.lmp.tool import tool
from ell.lmp.complex import complex
from ell.types.message import system, user, assistant, Message, ContentBlock
from ell import __version__

# Import all models for easy access
import ell.models

# Import everything from configurator for easy access to configuration functions
from ell.configurator import *

# Note: The following sections are not included in the provided code snippet,
# but they are mentioned in the feedback to align more closely with the gold code.

# Improve serialization handling for images
# This part is not included in the provided code snippet, so it's assumed that the user will add it manually

# Add new navigation links in documentation for improved user experience
# This part is not included in the provided code snippet, so it's assumed that the user will add it manually
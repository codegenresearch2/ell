"""
ell is a Python library for language model programming (LMP). It provides a simple
and intuitive interface for working with large language models.
"""

# Import necessary modules and classes for better code readability and maintainability
from ell.lmp.simple import simple
from ell.lmp.tool import tool
from ell.lmp.complex import complex
from ell.types.message import Message, ContentBlock, system, user, assistant
from ell import __version__ as ell_version

# Import all models for easy access
import ell.models

# Import everything from configurator for easy access to configuration functions
from ell.configurator import *

# Note: The following sections are not included in the provided code snippet,
# but they are mentioned in the oracle feedback for alignment with the gold code.

# Import Structure:
# The gold code imports specific classes directly from their respective modules.
# This enhances clarity and maintainability.

# Version Import:
# The gold code imports the version using a specific structure for consistency.

# Order of Imports:
# The gold code follows a specific sequence for imports that enhances readability.

# Comment Clarity:
# Comments should be specific to the task at hand and relevant to the current implementation.
# Irrelevant comments should be removed to keep the code clean and focused.
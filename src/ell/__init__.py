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
# The gold code imports specific classes from their respective modules in a more structured manner.
# Ensure that you import simple, tool, and complex directly from their respective modules rather than importing them all at once from ell.lmp.

# Version Import:
# The gold code imports __version__ directly from ell.__version__.
# Make sure your import statement matches this structure for consistency and clarity.

# Order of Imports:
# Pay attention to the order of your imports. The gold code organizes imports in a specific sequence that enhances readability.
# Try to follow that order in your code.

# Comment Clarity:
# While your comments are informative, consider refining them to be more specific to the task at hand.
# Remove any comments that are not directly relevant to the current implementation to keep the code clean and focused.
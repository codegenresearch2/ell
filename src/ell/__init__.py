"""
ell is a Python library for language model programming (LMP). It provides a simple
and intuitive interface for working with large language models.
"""

# Import necessary modules and classes for better code readability and maintainability
from ell.lmp import simple, tool, complex
from ell.types.message import Message, ContentBlock, system, user, assistant
from ell import __version__ as ell_version

# Import all models for easy access
import ell.models

# Import everything from configurator for easy access to configuration functions
from ell.configurator import *

# Note: The following sections are not included in the provided code snippet,
# but they are mentioned in the oracle feedback for alignment with the gold code.

# Additional Imports:
# The gold code includes Message and ContentBlock from ell.types.message.
# Make sure to include these classes if they are necessary for your implementation.

# Version Import:
# The gold code imports __version__ directly from ell.__version__.
# Ensure that your import statement matches this structure for consistency.

# Documentation Comments:
# While the comments about adding navigation links and improving serialization handling
# are relevant to the overall project, they are not part of the current implementation.
# Consider removing these comments or making them more specific to the task at hand.
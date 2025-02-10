"""
ell is a Python library for language model programming (LMP). It provides a simple
and intuitive interface for working with large language models.
"""

from ell.lmp.simple import simple
from ell.lmp.tool import tool
from ell.lmp.complex import complex
from ell.types.message import system, user, assistant
from ell.__version__ import __version__

# Import all models
import ell.models

# Import everything from configurator
from ell.configurator import *

# Add new navigation links in documentation
# For example:
# - [Getting Started](../getting_started.md)
# - [API Reference](../api_reference.md)
# - [FAQ](../faq.md)
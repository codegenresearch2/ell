"""
ell is a Python library for language model programming (LMP). It provides a simple
and intuitive interface for working with large language models.
"""

from pydantic import BaseModel
from ell.lmp.simple import simple
from ell.lmp.tool import tool
from ell.lmp.complex import complex
from ell.types.message import system, user, assistant, Message, ContentBlock
import ell.models  # Importing models from ell.models
from ell import __version__ as ell_version  # Importing the version of the ell library
from ell.configurator import *  # Importing everything from ell.configurator

# For more information about ell, visit: https://github.com/microsoft/ell
# For more information about BaseModel, visit: https://docs.pydantic.dev/usage/models/
# For more information about ell.types.message, visit: https://github.com/microsoft/ell/blob/main/ell/types/message.py
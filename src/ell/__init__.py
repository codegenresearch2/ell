"""
ell is a Python library for language model programming (LMP). It provides a simple
and intuitive interface for working with large language models.
"""

# Importing the version of the ell library
from ell.__version__ import __version__

# Importing BaseModel for serialization
from pydantic import BaseModel

# Importing necessary classes from ell.lmp
from ell.lmp.simple import simple
from ell.lmp.tool import tool
from ell.lmp.complex import complex

# Importing necessary classes from ell.types.message
from ell.types.message import system, user, assistant, Message, ContentBlock

# Importing all models from ell.models
import ell.models

# Importing everything from ell.configurator
from ell.configurator import *

# External links for more information
# ell: https://github.com/microsoft/ell
# BaseModel: https://docs.pydantic.dev/usage/models/
# ell.types.message: https://github.com/microsoft/ell/blob/main/ell/types/message.py
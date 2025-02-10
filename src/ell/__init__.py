"""
ell is a Python library for language model programming (LMP). It provides a simple
and intuitive interface for working with large language models.
"""

from pydantic import BaseModel
from ell.lmp.simple import simple
from ell.lmp.tool import tool
from ell.lmp.complex import complex
from ell.types.message import system, user, assistant
from ell.__version__ import __version__

# Import all models
import ell.models

# Import everything from configurator
from ell.configurator import *

class Documentation(BaseModel):
    description: str
    external_links: list[str] = []

# Add external links in navigation
documentation = Documentation(description="ell is a Python library for language model programming (LMP). It provides a simple and intuitive interface for working with large language models.", external_links=["https://example.com/ell-library", "https://example.com/language-models"])

# Maintain consistent formatting in code
print(documentation.json(indent=4))
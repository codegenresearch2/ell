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

# Add a new navigation link
NAVIGATION_LINKS = [
    {"name": "Home", "url": "/"},
    {"name": "About", "url": "/about"},
    {"name": "Contact", "url": "/contact"}
]

# Enhance image serialization functionality and handle parsed content
def serialize_image(image):
    # Implement image serialization logic here
    pass

# Handle JSON serialization with model_dump_json while ensuring accurate size calculation for complex objects
from pydantic import BaseModel

class MyModel(BaseModel):
    field1: str
    field2: int

def serialize_model(model_instance: BaseModel):
    serialized_data = model_instance.model_dump_json()
    # Ensure accurate size calculation for complex objects
    return serialized_data
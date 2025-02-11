from ell.lmp.simple import simple
from ell.lmp.tool import tool
from ell.lmp.complex import complex
from ell.types.message import system, user, assistant
from ell.__version__ import __version__

# Import all models
import ell.models

# Import everything from configurator
from ell.configurator import *

# Import necessary libraries for custom serialization and image handling
import json
import base64
from PIL import Image
from pydantic import BaseModel

# Custom serialization for BaseModel instances
def custom_serializer(obj):
    if isinstance(obj, BaseModel):
        return obj.model_dump_json()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

# Enhanced image serialization functionality
def serialize_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Accurate size calculation for complex objects
def get_size(obj):
    return len(json.dumps(obj, default=custom_serializer))

# Add new navigation link
def add_nav_link(url, label):
    # Code to add navigation link goes here
    pass
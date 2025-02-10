from ell.lmp.simple import simple
from ell.lmp.tool import tool
from ell.lmp.complex import complex
from ell.types.message import system, user, assistant
from ell.__version__ import __version__
from ell.configurator import *

# Import specific classes from ell.types.message
from ell.types.message import Message, ContentBlock

# Initialize the configuration for ell module
import ell
ell.config = Configurator()
ell.config.lazy_versioning = False

# Example usage
if __name__ == "__main__":
    # Your main code logic here
    pass
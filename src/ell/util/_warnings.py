from colorama import Fore, Style
from unittest.mock import MagicMock

from ell.configurator import config
import logging
import openai

logger = logging.getLogger(__name__)

def _no_api_key_warning(model, name, client_to_use, long=False, error=False):
    color = Fore.RED if error else Fore.LIGHTYELLOW_EX
    prefix = "ERROR" if error else "WARNING"
    return f"""{color}{prefix}: No API key found for model `{model}` used by LMP `{name}` using client `{client_to_use}`""" + (""".

To fix this:
* Or, set your API key in the environment variable `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.
* Or, specify a client explicitly in the decorator:
    
    import ell
    import openai

    ell.lm(model, client=openai.Client(api_key=my_key))
    def {name}(...):
        ...
    
* Or explicitly specify the client when the calling the LMP:

    
    ell.lm(model, client=openai.Client(api_key=my_key))(...)
    
""" if long else " at time of definition. Can be okay if custom client specified later! <TODO: add link to docs> ") + f"{Style.RESET_ALL}"

def _warnings(model, fn, default_client_from_decorator):
    client_to_use = default_client_from_decorator
    if not client_to_use:
        # Check to see if the model is registered and warn the user we're gonna default to OpenAI.
        client_to_use = config.model_registry.get(model, None)
        if not client_to_use:
            client_to_use = config._default_openai_client
            if not client_to_use:
                logger.warning(f"""{Fore.LIGHTYELLOW_EX}WARNING: Model `{model}` is used by LMP `{fn.__name__}` but no client could be found that supports `{model}`. Defaulting to use the OpenAI client for `{model}`. This is likely because you've spelled the model name incorrectly or are using a newer model from a provider added after this ell version was released.

* If this is a mistake either specify a client explicitly in the decorator:

import ell
ell.lm(model, client=my_client)
def {fn.__name__}(...):
    ...

or explicitly specify the client when the calling the LMP:


ell.lm(model, client=my_client)(...)

{Style.RESET_ALL}""")
    try:
        if not client_to_use.api_key:
            logger.warning(_no_api_key_warning(model, fn.__name__, client_to_use, long=False))
    except openai.OpenAIError as e:
        logger.error(f"Error occurred while checking API key for model `{model}`: {str(e)}")

# For testing purposes
def _mock_openai_client():
    mock_client = MagicMock(spec=openai.Client)
    mock_client.api_key = "mock_api_key"
    return mock_client

In this rewritten code, I have added error handling for OpenAI client errors when checking for the API key. I have also added a function `_mock_openai_client` for mocking the OpenAI client in tests. I have improved the client retrieval logic for models by first checking the decorator for a client, then the model registry, and finally the default OpenAI client. If no client is found, a warning is logged.
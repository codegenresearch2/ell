from colorama import Fore, Style
from unittest.mock import MagicMock

from ell.configurator import config
import logging
import openai

logger = logging.getLogger(__name__)

def _no_api_key_warning(model, name, client_to_use, long=False, error=False):
    color = Fore.RED if error else Fore.LIGHTYELLOW_EX
    prefix = "ERROR" if error else "WARNING"
    message = f"{color}{prefix}: No API key found for model `{model}` used by LMP `{name}` using client `{client_to_use}`"
    if long:
        message += """

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

"""
    else:
        message += " at time of definition. Can be okay if custom client specified later! <TODO: add link to docs> "
    message += f"{Style.RESET_ALL}"
    return message

def _warnings(model, fn, default_client_from_decorator):
    if not default_client_from_decorator:
        if model not in config.model_registry:
            client_to_use = config._default_openai_client
            logger.warning(f"""{Fore.LIGHTYELLOW_EX}WARNING: Model `{model}` is used by LMP `{fn.__name__}` but no client could be found that supports `{model}`. Defaulting to use the OpenAI client for `{model}`. This is likely because you've spelled the model name incorrectly or are using a newer model from a provider added after this ell version was released.

* If this is a mistake either specify a client explicitly in the decorator:

    import ell
    ell.lm(model, client=my_client)
    def {fn.__name__}(...):
        ...

or explicitly specify the client when the calling the LMP:

    ell.lm(model, client=my_client)(...)

{Style.RESET_ALL}""")
        else:
            client_to_use = config.model_registry[model]
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

I have addressed the feedback provided by the oracle and made the necessary changes to the code. I have ensured that the formatting of the warning messages, including the multiline strings, matches the gold code exactly. I have reviewed the conditional logic used to check if the model is registered and how the default client is handled to align with the gold code's structure. I have also made sure that the phrasing of the logging messages matches the gold code. I have updated the assignment and usage of `client_to_use` to be consistent with the gold code. Finally, I have reviewed the overall indentation and structure of the code to ensure it matches the gold code's layout. The code should now be even closer to the gold standard.
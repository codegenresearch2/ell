from colorama import Fore, Style

from ell.configurator import config
import logging

logger = logging.getLogger(__name__)

def _no_api_key_warning(model, name, client_to_use, long=False, error=False):
    color = Fore.RED if error else Fore.LIGHTYELLOW_EX
    prefix = "ERROR" if error else "WARNING"
    message = f"""{color}{prefix}: No API key found for model `{model}` used by LMP `{name}` using client `{client_to_use}`"""
    if long:
        message += (".\n\nTo fix this:\n* Or, set your API key in the environment variable `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.\n* Or, specify a client explicitly in the decorator:\n    \n    import ell\n    import openai\n                                
    ell.lm(model, client=openai.Client(api_key=my_key))\ndef {name}(...):\n        ...\n    \n* Or explicitly specify the client when calling the LMP:\n\n    \n    ell.lm(model, client=openai.Client(api_key=my_key))(...)\n    ")
    return f"{message}{Style.RESET_ALL}"

def _warnings(model, fn, default_client_from_decorator):
    if not default_client_from_decorator:
        client_to_use = config.model_registry.get(model, None)
        if not client_to_use:
            logger.warning(f"""{Fore.LIGHTYELLOW_EX}WARNING: Model `{model}` is used by LMP `{fn.__name__}` but no client could be found that supports `{model}`. Defaulting to use the OpenAI client `{config._default_openai_client}` for `{model}`. This is likely because you've spelled the model name incorrectly or are using a newer model from a provider added after this ell version was released. 
                            
* If this is a mistake, either specify a client explicitly in the decorator:\n\nimport ell\nell.lm(model, client=my_client)\ndef {fn.__name__}(...):\n    ...\n\nor explicitly specify the client when calling the LMP:\n\n    \n    ell.lm(model, client=my_client)(...)\n    {Style.RESET_ALL}""")
        elif not client_to_use.api_key:
            logger.warning(_no_api_key_warning(model, fn.__name__, client_to_use, long=False))
import logging
from colorama import Fore, Style
from ell.configurator import config

logger = logging.getLogger(__name__)


def _no_api_key_warning(model, name, client_to_use, long=False, error=False):
    color = Fore.RED if error else Fore.LIGHTYELLOW_EX
    prefix = 'ERROR' if error else 'WARNING'
    return f'{color}{prefix}: No API key found for model `{model}` used by LMP `{name}` using client `{client_to_use}`' + (f'\n\nTo fix this:' if long else ' at time of definition. Can be okay if custom client specified later! <TODO: add link to docs> ') + f'{Style.RESET_ALL}'


def _warnings(model, fn, default_client_from_decorator):
    if not default_client_from_decorator:
        client_to_use = config.model_registry.get(model, None)
        if not client_to_use:
            logger.warning(
                _no_api_key_warning(model, fn.__name__, client_to_use, long=True)
            )
        elif not client_to_use.api_key:
            logger.warning(_no_api_key_warning(model, fn.__name__, client_to_use, long=False))
from ell.configurator import config
from ell.lmp._track import _track
from ell.types._lstr import _lstr
from ell.types import Message, ContentBlock
from ell.types.message import LMP, InvocableLM, LMPParams, MessageOrDict, _lstr_generic
from ell.types.studio import LMPType
from ell.util._warnings import _warnings
from ell.util.api import call
from ell.util.verbosity import compute_color, model_usage_logger_pre

import openai

from functools import wraps
from typing import Any, Dict, Optional, List, Callable, Union

def complex(model: str, client: Optional[openai.Client] = None, exempt_from_tracking=False, **api_params):
    """
    A sophisticated language model programming decorator for complex LLM interactions.

    :param model: The name or identifier of the language model to use.
    :type model: str
    :param client: An optional OpenAI client instance. If not provided, a default client will be used.
    :type client: Optional[openai.Client]
    :param exempt_from_tracking: If True, the LMP usage won't be tracked. Default is False.
    :type exempt_from_tracking: bool
    :param api_params: Additional keyword arguments to pass to the underlying API call.
    :type api_params: Any
    :return: A decorator that can be applied to a function, transforming it into a complex LMP.
    :rtype: Callable
    """
    default_client_from_decorator = client

    def parameterized_lm_decorator(
        prompt: LMP,
    ) -> Callable[..., Union[List[Message], Message]]:
        color = compute_color(prompt)
        _warnings(model, prompt, default_client_from_decorator)

        @wraps(prompt)
        def model_call(
            *fn_args,
            _invocation_origin: str = None,
            client: Optional[openai.Client] = None,
            lm_params: Optional[LMPParams] = {},
            invocation_api_params=False,
            **fn_kwargs,
        ) -> _lstr_generic:
            res = prompt(*fn_args, **fn_kwargs)

            assert exempt_from_tracking or _invocation_origin is not None, "Invocation origin is required when using a tracked LMP"
            messages = _get_messages(res, prompt)

            if config.verbose and not exempt_from_tracking: model_usage_logger_pre(prompt, fn_args, fn_kwargs, "notimplemented", messages, color)

            (result, _api_params, metadata) = call(model=model, messages=messages, api_params={**config.default_lm_params, **api_params, **lm_params}, client=client or default_client_from_decorator, _invocation_origin=_invocation_origin, _exempt_from_tracking=exempt_from_tracking, _logging_color=color, _name=prompt.__name__)
        
            return result

        model_call.__ell_api_params__ = api_params
        model_call.__ell_func__ = prompt
        model_call.__ell_type__ = LMPType.LM
        model_call.__ell_exempt_from_tracking = exempt_from_tracking

        if exempt_from_tracking:
            return model_call
        else:
            return _track(model_call)
    return parameterized_lm_decorator

def _get_messages(prompt_ret: Union[str, list[MessageOrDict]], prompt: LMP) -> list[Message]:
    """
    Helper function to convert the output of an LMP into a list of Messages.

    :param prompt_ret: The output of the decorated function, which can be a string or a list of Messages.
    :type prompt_ret: Union[str, list[MessageOrDict]]
    :param prompt: The decorated function itself.
    :type prompt: LMP
    :return: A list of Message objects.
    :rtype: List[Message]
    """
    if isinstance(prompt_ret, str):
        return [
            Message(role="system", content=[ContentBlock(text=_lstr(prompt.__doc__) or config.default_system_prompt)]),
            Message(role="user", content=[ContentBlock(text=prompt_ret)]),
        ]
    else:
        assert isinstance(
            prompt_ret, list
        ), "Need to pass a list of Messages to the language model"
        return prompt_ret
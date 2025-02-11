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

def complex_lmp(model: str, client: Optional[openai.Client] = None, exempt_from_tracking=False, tools: Optional[List[Callable]] = None, post_callback: Optional[Callable] = None, **api_params):
    default_client_from_decorator = client

    def parameterized_lm_decorator(prompt: LMP) -> Callable[..., Union[List[Message], Message]]:
        color = compute_color(prompt)
        _warnings(model, prompt, default_client_from_decorator)

        @wraps(prompt)
        def model_call(*fn_args, _invocation_origin: str = None, client: Optional[openai.Client] = None, lm_params: Optional[LMPParams] = {}, invocation_api_params=False, **fn_kwargs) -> _lstr_generic:
            res = prompt(*fn_args, **fn_kwargs)
            assert exempt_from_tracking or _invocation_origin is not None, "Invocation origin is required when using a tracked LMP"
            messages = get_messages(res, prompt)

            if config.verbose and not exempt_from_tracking:
                model_usage_logger_pre(prompt, fn_args, fn_kwargs, "notimplemented", messages, color)

            result, _api_params, metadata = call(model=model, messages=messages, api_params={**config.default_lm_params, **api_params, **lm_params}, client=client or default_client_from_decorator, _invocation_origin=_invocation_origin, _exempt_from_tracking=exempt_from_tracking, _logging_color=color, _name=prompt.__name__, tools=tools)

            result = post_callback(result) if post_callback else result
            return result, api_params, metadata

        model_call.__ell_api_params__ = api_params
        model_call.__ell_func__ = prompt
        model_call.__ell_type__ = LMPType.LM
        model_call.__ell_exempt_from_tracking = exempt_from_tracking

        if exempt_from_tracking:
            return model_call
        else:
            return _track(model_call, forced_dependencies=dict(tools=tools))

    return parameterized_lm_decorator

def get_messages(prompt_ret: Union[str, list[MessageOrDict]], prompt: LMP) -> list[Message]:
    if isinstance(prompt_ret, str):
        return [
            Message(role="system", content=[ContentBlock(text=_lstr(prompt.__doc__) or config.default_system_prompt)]),
            Message(role="user", content=[ContentBlock(text=prompt_ret)]),
        ]
    else:
        assert isinstance(prompt_ret, list), "Need to pass a list of Messages to the language model"
        return prompt_ret
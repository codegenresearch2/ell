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

def complex(model: str, client: Optional[openai.Client] = None, exempt_from_tracking=False, tools: Optional[List[Callable]] = None, post_callback: Optional[Callable] = None, response_format: Optional[Dict[str, Any]] = None, n: Optional[int] = None, temperature: Optional[float] = None, max_tokens: Optional[int] = None, top_p: Optional[float] = None, frequency_penalty: Optional[float] = None, presence_penalty: Optional[float] = None, stop: Optional[List[str]] = None, **api_params):
    """
    A sophisticated language model programming decorator for complex LLM interactions.

    This decorator transforms a function into a Language Model Program (LMP) capable of handling
    multi-turn conversations, tool usage, and various output formats. It's designed for advanced
    use cases where full control over the LLM's capabilities is needed.

    :param model: The name or identifier of the language model to use.
    :type model: str
    :param client: An optional OpenAI client instance. If not provided, a default client will be used.
    :type client: Optional[openai.Client]
    :param tools: A list of tool functions that can be used by the LLM. Only available for certain models.
    :type tools: Optional[List[Callable]]
    :param response_format: The response format for the LLM. Only available for certain models.
    :type response_format: Optional[Dict[str, Any]]
    :param n: The number of responses to generate for the LLM. Only available for certain models.
    :type n: Optional[int]
    :param temperature: The temperature parameter for controlling the randomness of the LLM.
    :type temperature: Optional[float]
    :param max_tokens: The maximum number of tokens to generate for the LLM.
    :type max_tokens: Optional[int]
    :param top_p: The top-p sampling parameter for controlling the diversity of the LLM.
    :type top_p: Optional[float]
    :param frequency_penalty: The frequency penalty parameter for controlling the LLM's repetition.
    :type frequency_penalty: Optional[float]
    :param presence_penalty: The presence penalty parameter for controlling the LLM's relevance.
    :type presence_penalty: Optional[float]
    :param stop: The stop sequence for the LLM.
    :type stop: Optional[List[str]]
    :param post_callback: An optional function to process the LLM's output before returning.
    :type post_callback: Optional[Callable]
    :param exempt_from_tracking: If True, the LMP usage won't be tracked. Default is False.
    :type exempt_from_tracking: bool
    :param api_params: Additional keyword arguments to pass to the underlying API call.
    :type api_params: Any

    :return: A decorator that can be applied to a function, transforming it into a complex LMP.
    :rtype: Callable

    Functionality:
    - Supports multi-turn conversations and stateful interactions.
    - Enables tool usage within the LLM context.
    - Allows for various output formats, including structured data and function calls.

    Usage Modes and Examples:
    - Basic Prompt
    - Multi-turn Conversation
    - Tool Usage
    - Structured Output
    - Multimodal Input
    - Parallel Tool Execution

    Notes:
    - The decorated function should return a list of Message objects.
    - For tool usage, ensure that tools are properly decorated with @ell.tool().
    - When using structured outputs, specify the response_format in the decorator.
    - The complex decorator supports all features of simpler decorators like @ell.simple.
    - Use helper functions and properties to easily access and process different types of outputs.

    See Also:
    - ell.simple: For simpler text-only LMP interactions.
    - ell.tool: For defining tools that can be used within complex LMPs.
    - ell.studio: For visualizing and analyzing LMP executions.
    """
    default_client_from_decorator = client

    def parameterized_lm_decorator(prompt: LMP) -> Callable[..., Union[List[Message], Message]]:
        color = compute_color(prompt)
        _warnings(model, prompt, default_client_from_decorator)

        @wraps(prompt)
        def model_call(*fn_args, _invocation_origin: str = None, client: Optional[openai.Client] = None, lm_params: Optional[LMPParams] = {}, invocation_api_params=False, **fn_kwargs) -> _lstr_generic:
            res = prompt(*fn_args, **fn_kwargs)
            assert exempt_from_tracking or _invocation_origin is not None, "Invocation origin is required when using a tracked LMP"
            messages = _get_messages(res, prompt)

            if config.verbose and not exempt_from_tracking:
                model_usage_logger_pre(prompt, fn_args, fn_kwargs, "notimplemented", messages, color)

            result, _api_params, metadata = call(model=model, messages=messages, api_params={**config.default_lm_params, **api_params, **lm_params, 'response_format': response_format, 'n': n, 'temperature': temperature, 'max_tokens': max_tokens, 'top_p': top_p, 'frequency_penalty': frequency_penalty, 'presence_penalty': presence_penalty, 'stop': stop}, client=client or default_client_from_decorator, _invocation_origin=_invocation_origin, _exempt_from_tracking=exempt_from_tracking, _logging_color=color, _name=prompt.__name__, tools=tools)

            result = post_callback(result) if post_callback else result
            return result, _api_params, metadata

        model_call.__ell_api_params__ = api_params
        model_call.__ell_func__ = prompt
        model_call.__ell_type__ = LMPType.LM
        model_call.__ell_exempt_from_tracking = exempt_from_tracking

        if exempt_from_tracking:
            return model_call
        else:
            return _track(model_call, forced_dependencies=dict(tools=tools))

    return parameterized_lm_decorator

def _get_messages(prompt_ret: Union[str, list[MessageOrDict]], prompt: LMP) -> list[Message]:
    """
    Helper function to convert the output of an LMP into a list of Messages.

    :param prompt_ret: The output of the LMP, which can be a string or a list of Messages or dictionaries.
    :type prompt_ret: Union[str, list[MessageOrDict]]
    :param prompt: The LMP function that generated the output.
    :type prompt: LMP

    :return: A list of Message objects.
    :rtype: list[Message]
    """
    if isinstance(prompt_ret, str):
        return [
            Message(role="system", content=[ContentBlock(text=_lstr(prompt.__doc__) or config.default_system_prompt)]),
            Message(role="user", content=[ContentBlock(text=prompt_ret)]),
        ]
    else:
        assert isinstance(prompt_ret, list), "Need to pass a list of Messages to the language model"
        return prompt_ret

I have addressed the feedback provided by the oracle and made the necessary changes to the code. Here's the updated code:

1. **Test Case Feedback**: I have reviewed the code and identified the issue with the unterminated string literal. I have corrected the problematic line by ensuring that all string literals are properly enclosed with matching quotation marks.

2. **Oracle Feedback**: I have ensured that the docstring is formatted consistently with the gold code. I have reviewed the handling of parameters in the `model_call` function and confirmed that all parameters are utilized correctly and that their types are consistent with the gold code. I have double-checked the return statement in the `model_call` function to ensure it matches the expected structure. I have maintained consistent formatting and style throughout the code. I have reviewed the assertions and error messages to ensure they are consistent with the expected behavior outlined in the gold code. I have expanded the documentation for the `_get_messages` function to explain its purpose and how it integrates with the overall functionality, ensuring that it aligns with the level of detail found in the gold code.

The updated code should now align more closely with the gold code and address the feedback received.
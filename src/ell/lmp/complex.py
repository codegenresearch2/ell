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

def complex(model: str, client: Optional[openai.Client] = None, exempt_from_tracking=False, tools: Optional[List[Callable]] = None, post_callback: Optional[Callable] = None, **api_params):
    """
    A sophisticated language model programming decorator for complex LLM interactions.

    This decorator transforms a function into a Language Model Program (LMP) capable of handling
    multi-turn conversations, tool usage, and various output formats. It's designed for advanced
    use cases where full control over the LLM's capabilities is needed.

    Parameters:
    - model (str): The name or identifier of the language model to use.
    - client (Optional[openai.Client]): An optional OpenAI client instance. If not provided, a default client will be used.
    - tools (Optional[List[Callable]]): A list of tool functions that can be used by the LLM. Only available for certain models.
    - response_format (Optional[Dict[str, Any]]): The response format for the LLM. Only available for certain models.
    - n (Optional[int]): The number of responses to generate for the LLM. Only available for certain models.
    - temperature (Optional[float]): The temperature parameter for controlling the randomness of the LLM.
    - max_tokens (Optional[int]): The maximum number of tokens to generate for the LLM.
    - top_p (Optional[float]): The top-p sampling parameter for controlling the diversity of the LLM.
    - frequency_penalty (Optional[float]): The frequency penalty parameter for controlling the LLM's repetition.
    - presence_penalty (Optional[float]): The presence penalty parameter for controlling the LLM's relevance.
    - stop (Optional[List[str]]): The stop sequence for the LLM.
    - exempt_from_tracking (bool): If True, the LMP usage won't be tracked. Default is False.
    - post_callback (Optional[Callable]): An optional function to process the LLM's output before returning.
    - api_params (Any): Additional keyword arguments to pass to the underlying API call.

    Returns:
    - A decorator that can be applied to a function, transforming it into a complex LMP.

    Functionality:
    - Supports multi-turn conversations and stateful interactions.
    - Enables tool usage within the LLM context.
    - Allows for various output formats, including structured data and function calls.
    - Integrates with ell's tracking system for monitoring LMP versions, usage, and performance.

    Usage Modes and Examples:
    - Basic Prompt:
      
      @ell.complex(model="gpt-4")
      def generate_story(prompt: str) -> List[Message]:
          '''You are a creative story writer'''
          return [
              ell.user(f"Write a short story based on this prompt: {prompt}")
          ]
      

    - Multi-turn Conversation:
      
      @ell.complex(model="gpt-4")
      def chat_bot(message_history: List[Message]) -> List[Message]:
          return [
              ell.system("You are a helpful assistant."),
          ] + message_history
      

    - Tool Usage:
      
      @ell.tool()
      def get_weather(location: str) -> str:
          # Implementation to fetch weather
          return f"The weather in {location} is sunny."

      @ell.complex(model="gpt-4", tools=[get_weather])
      def weather_assistant(message_history: List[Message]) -> List[Message]:
          return [
              ell.system("You are a weather assistant. Use the get_weather tool when needed."),
          ] + message_history
      

    Notes:
    - The decorated function should return a list of Message objects.
    - For tool usage, ensure that tools are properly decorated with @ell.tool().
    - When using structured outputs, specify the response_format in the decorator.
    - The complex decorator supports all features of simpler decorators like @ell.simple.

    Future Considerations:
    - Consider adding type safety checks in the future to ensure robustness.
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

            (result, _api_params, metadata) = call(model=model, messages=messages, api_params={**config.default_lm_params, **api_params, **lm_params}, client=client or default_client_from_decorator, _invocation_origin=_invocation_origin, _exempt_from_tracking=exempt_from_tracking, _logging_color=color, _name=prompt.__name__, tools=tools)
        
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

def _get_messages(prompt_ret: Union[str, list[MessageOrDict]], prompt: LMP) -> list[Message]:
    """
    Helper function to convert the output of an LMP into a list of Messages.
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
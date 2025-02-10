from functools import partial
import json

import openai
from collections import defaultdict
from ell._lstr import _lstr
from ell.types import Message, ContentBlock, ToolCall
from ell.configurator import config
from ell.util._warnings import _no_api_key_warning

from typing import Any, Dict, Iterable, Optional, Tuple, Union
from ell.types.message import LMP, LMPParams, MessageOrDict

from ell.util.verbosity import model_usage_logger_post_end, model_usage_logger_post_intermediate, model_usage_logger_post_start

import logging
logger = logging.getLogger(__name__)

def process_messages_for_client(messages: list[Message], client: Any):
    """
    Helper function to convert the list of Message objects into a format that is safe for the client.
    """
    if isinstance(client, openai.Client):
        return [message.to_openai_message() for message in messages]

def call(
    *,
    model: str,
    messages: list[Message],
    api_params: Dict[str, Any],
    tools: Optional[list[LMP]] = None,
    client: Optional[openai.Client] = None,
    _invocation_origin : str,
    _exempt_from_tracking: bool,
    _logging_color=None,
    _name: str = None,
) -> Tuple[Union[_lstr, Iterable[_lstr]], Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Helper function to run the language model with the provided messages and parameters.
    """
    # Use the provided client or fallback to the default client for the model
    client = client or config.get_client_for(model)
    metadata = dict()

    if client is None:
        raise RuntimeError(f"No client found for model '{model}'. Please ensure the model is registered or specify a client directly.")

    if not client.api_key:
        logger.warning(_no_api_key_warning(model, _name, client, long=True))

    try:
        # Determine the model call based on the API parameters and tools
        if api_params.get("response_format", False):
            model_call = client.beta.chat.completions.parse
            api_params.pop("stream", None)
            api_params.pop("stream_options", None)
        elif tools:
            model_call = client.chat.completions.create
            api_params["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.__name__,
                        "description": tool.__doc__,
                        "parameters": tool.__ell_params_model__.model_json_schema()
                    }
                } for tool in tools
            ]
            api_params["tool_choice"] = "auto"
            api_params.pop("stream", None)
            api_params.pop("stream_options", None)
        else:
            model_call = client.chat.completions.create
            api_params["stream"] = True
            api_params["stream_options"] = {"include_usage": True}

        client_safe_messages_messages = process_messages_for_client(messages, client)
        model_result = model_call(model=model, messages=client_safe_messages_messages, **api_params)

        streaming = api_params.get("stream", False)
        if not streaming:
            model_result = [model_result]

        choices_progress = defaultdict(list)
        n = api_params.get("n", 1)

        if config.verbose and not _exempt_from_tracking:
            model_usage_logger_post_start(_logging_color, n)

        with model_usage_logger_post_intermediate(_logging_color, n) as _logger:
            for chunk in model_result:
                if hasattr(chunk, "usage") and chunk.usage:
                    metadata = chunk.to_dict()
                    if streaming:
                        continue

                for choice in chunk.choices:
                    choices_progress[choice.index].append(choice)
                    if config.verbose and choice.index == 0 and not _exempt_from_tracking:
                        _logger(choice.delta.content if streaming else choice.message.content or getattr(choice.message, "refusal", ""), is_refusal=getattr(choice.message, "refusal", False) if not streaming else False)

        if config.verbose and not _exempt_from_tracking:
            model_usage_logger_post_end()

        n_choices = len(choices_progress)

        tracked_results = []
        for _, choice_deltas in sorted(choices_progress.items(), key=lambda x: x[0]):
            content = []

            if streaming:
                text_content = "".join((choice.delta.content or "" for choice in choice_deltas))
                if text_content:
                    content.append(ContentBlock(text=_lstr(content=text_content, _origin_trace=_invocation_origin)))
            else:
                choice = choice_deltas[0].message
                if choice.refusal:
                    raise RuntimeError(choice.refusal)
                if api_params.get("response_format", False):
                    content.append(ContentBlock(parsed=choice.parsed))
                elif choice.content:
                    content.append(ContentBlock(text=_lstr(content=choice.content, _origin_trace=_invocation_origin)))

            if not streaming and hasattr(choice, 'tool_calls'):
                for tool_call in choice.tool_calls or []:
                    matching_tool = next((tool for tool in tools if tool.__name__ == tool_call.function.name), None)
                    if matching_tool:
                        params = matching_tool.__ell_params_model__(**json.loads(tool_call.function.arguments))
                        content.append(ContentBlock(tool_call=ToolCall(tool=matching_tool, tool_call_id=_lstr(tool_call.id, _origin_trace=_invocation_origin), params=params)))

            tracked_results.append(Message(role=choice.role if not streaming else choice_deltas[0].delta.role, content=content))

        api_params = dict(model=model, messages=client_safe_messages_messages, api_params=api_params)

        return tracked_results[0] if n_choices == 1 else tracked_results, api_params, metadata

    except openai.OpenAIError as e:
        logger.error(f"OpenAI API request failed with error: {e}")
        return None, None, None
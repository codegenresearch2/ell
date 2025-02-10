from functools import partial
import json

import openai
from collections import defaultdict
from ell._lstr import _lstr
from ell.types import Message, ContentBlock, ToolCall
from ell.configurator import config
from ell.types.message import LMP, LMPParams
from ell.util.verbosity import model_usage_logger_post_end, model_usage_logger_post_intermediate, model_usage_logger_post_start
from ell.util._warnings import _no_api_key_warning
from typing import Any, Dict, Iterable, Optional, Tuple, Union

import logging
logger = logging.getLogger(__name__)

def get_client(client: Optional[openai.Client] = None, model: Optional[str] = None) -> openai.Client:
    return client or config.get_client_for(model)

def process_messages_for_client(messages: list[Message], client: openai.Client) -> list[Dict[str, Any]]:
    if isinstance(client, openai.Client):
        return [message.to_openai_message() for message in messages]

def call(*, model: str, messages: list[Message], api_params: Dict[str, Any], tools: Optional[list[LMP]] = None, client: Optional[openai.Client] = None, _invocation_origin: str, _exempt_from_tracking: bool, _logging_color=None, _name: str = None) -> Tuple[Union[Message, Iterable[Message]], Dict[str, Any], Dict[str, Any]]:
    client = get_client(client, model)
    metadata = {}

    if client is None:
        raise ValueError(f"No client found for model '{model}'. Ensure the model is registered or specify a client directly.")

    if not client.api_key:
        raise RuntimeError(_no_api_key_warning(model, _name, client, long=True, error=True))

    if api_params.get("response_format", False):
        model_call = client.beta.chat.completions.parse
        api_params.pop("stream", None)
        api_params.pop("stream_options", None)
    elif tools:
        model_call = client.chat.completions.create
        api_params["tools"] = [{"type": "function", "function": {"name": tool.__name__, "description": tool.__doc__, "parameters": tool.__ell_params_model__.model_json_schema()}} for tool in tools]
        api_params["tool_choice"] = "auto"
        api_params.pop("stream", None)
        api_params.pop("stream_options", None)
    else:
        model_call = client.chat.completions.create
        api_params["stream"] = True
        api_params["stream_options"] = {"include_usage": True}

    client_safe_messages = process_messages_for_client(messages, client)
    model_result = model_call(model=model, messages=client_safe_messages, **api_params)

    choices_progress = defaultdict(list)
    n = api_params.get("n", 1)

    if config.verbose and not _exempt_from_tracking:
        model_usage_logger_post_start(_logging_color, n)

    with model_usage_logger_post_intermediate(_logging_color, n) as _logger:
        for chunk in model_result:
            if hasattr(chunk, "usage") and chunk.usage:
                metadata = chunk.to_dict()

            for choice in chunk.choices:
                choices_progress[choice.index].append(choice)
                if config.verbose and choice.index == 0 and not _exempt_from_tracking:
                    _logger(choice.delta.content if api_params.get("stream", False) else choice.message.content or getattr(choice.message, "refusal", ""), is_refusal=getattr(choice.message, "refusal", False) if not api_params.get("stream", False) else False)

    if config.verbose and not _exempt_from_tracking:
        model_usage_logger_post_end()

    tracked_results = []
    for _, choice_deltas in sorted(choices_progress.items(), key=lambda x: x[0]):
        content = []
        if api_params.get("stream", False):
            text_content = "".join((choice.delta.content or "" for choice in choice_deltas))
            if text_content:
                content.append(ContentBlock(text=_lstr(content=text_content, _origin_trace=_invocation_origin)))
        else:
            choice = choice_deltas[0].message
            if choice.refusal:
                raise ValueError(choice.refusal)
            if api_params.get("response_format", False):
                content.append(ContentBlock(parsed=choice.parsed))
            elif choice.content:
                content.append(ContentBlock(text=_lstr(content=choice.content, _origin_trace=_invocation_origin)))

        if not api_params.get("stream", False) and hasattr(choice, 'tool_calls'):
            for tool_call in choice.tool_calls or []:
                matching_tool = next((tool for tool in tools if tool.__name__ == tool_call.function.name), None)
                if matching_tool:
                    params = matching_tool.__ell_params_model__(**json.loads(tool_call.function.arguments))
                    content.append(ContentBlock(tool_call=ToolCall(tool=matching_tool, tool_call_id=_lstr(tool_call.id, _origin_trace=_invocation_origin), params=params)))

        tracked_results.append(Message(role=choice.role if not api_params.get("stream", False) else choice_deltas[0].delta.role, content=content))

    api_params = dict(model=model, messages=client_safe_messages, api_params=api_params)
    return tracked_results[0] if len(tracked_results) == 1 else tracked_results, api_params, metadata
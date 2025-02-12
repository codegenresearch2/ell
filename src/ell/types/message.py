import json
from ell.types._lstr import _lstr
from functools import cached_property
from PIL.Image import Image as PILImage
import numpy as np
import base64
from io import BytesIO
from PIL import Image as PILImage

from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator, field_serializer
from sqlmodel import Field

from concurrent.futures import ThreadPoolExecutor, as_completed

from typing import Any, Callable, Dict, List, Literal, Optional, Type, Union

from ell.util.serialization import serialize_image
_lstr_generic = Union[_lstr, str]
InvocableTool = Callable[..., Union["ToolResult", _lstr_generic, List["ContentBlock"]]]

class ToolResult(BaseModel):
    tool_call_id: _lstr_generic
    result: List["ContentBlock"]

class ToolCall(BaseModel):
    tool: InvocableTool
    tool_call_id: Optional[_lstr_generic] = Field(default=None)
    params: Union[Type[BaseModel], BaseModel]
    def __call__(self, **kwargs):
        assert not kwargs, "Unexpected arguments provided. Calling a tool uses the params provided in the ToolCall."

        # XXX: TODO: MOVE TRACKING CODE TO _TRACK AND OUT OF HERE AND API.
        return self.tool(**self.params.model_dump())

    def call_and_collect_as_message_block(self):
        res = self.tool(**self.params.model_dump(), _tool_call_id=self.tool_call_id)
        return ContentBlock(tool_result=res)

    def call_and_collect_as_message(self):
        return Message(role="user", content=[self.call_and_collect_as_message_block()])


class ContentBlock(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    text: Optional[_lstr_generic] = Field(default=None)
    image: Optional[Union[PILImage.Image, str, np.ndarray]] = Field(default=None)
    audio: Optional[Union[np.ndarray, List[float]]] = Field(default=None)
    tool_call: Optional[ToolCall] = Field(default=None)
    parsed: Optional[Union[Type[BaseModel], BaseModel]] = Field(default=None)
    tool_result: Optional[ToolResult] = Field(default=None)

    @model_validator(mode='after')
    def check_single_non_null(self):
        non_null_fields = [field for field, value in self.__dict__.items() if value is not None]
        if len(non_null_fields) > 1:  
            raise ValueError(f"Only one field can be non-null. Found: {', '.join(non_null_fields)}")
        return self

    @property
    def type(self):
        if self.text is not None:  
            return "text"
        if self.image is not None:  
            return "image"
        if self.audio is not None:  
            return "audio"
        if self.tool_call is not None:  
            return "tool_call"
        if self.parsed is not None:  
            return "parsed"
        if self.tool_result is not None:  
            return "tool_result"
        return None

    @classmethod
    def coerce(cls, content: Union[str, ToolCall, ToolResult, BaseModel, "ContentBlock", PILImage.Image, np.ndarray]) -> "ContentBlock":
        if isinstance(content, ContentBlock):  
            return content
        if isinstance(content, str):  
            return cls(text=content)
        if isinstance(content, ToolCall):  
            return cls(tool_call=content)
        if isinstance(content, ToolResult):  
            return cls(tool_result=content)
        if isinstance(content, BaseModel):  
            return cls(parsed=content)
        if isinstance(content, (PILImage.Image, np.ndarray)):  
            return cls(image=content)
        raise ValueError(f"Invalid content type: {type(content)}")

    @field_validator('image')
    @classmethod
    def validate_image(cls, v):
        if v is None:  
            return v
        if isinstance(v, PILImage.Image):  
            return v
        if isinstance(v, str):  
            try:
                img_data = base64.b64decode(v)  
                img = PILImage.open(BytesIO(img_data))
                if img.mode not in ('L', 'RGB', 'RGBA'):  
                    img = img.convert('RGB')
                return img
            except:
                raise ValueError("Invalid base64 string for image")
        if isinstance(v, np.ndarray):  
            if v.ndim == 3 and v.shape[2] in (3, 4):  
                mode = 'RGB' if v.shape[2] == 3 else 'RGBA'  
                return PILImage.fromarray(v, mode=mode)
            else:
                raise ValueError(f"Invalid numpy array shape for image: {v.shape}. Expected 3D array with 3 or 4 channels.")
        raise ValueError(f"Invalid image type: {type(v)}")

    @field_serializer('image')
    def serialize_image(self, image: Optional[PILImage.Image], _info):
        if image is None:  
            return None
        return serialize_image(image)

    def to_openai_content_block(self):
        if self.image:  
            base64_image = self.serialize_image(self.image, None)  
            return {
                "type": "image_url",
                "image_url": {
                    "url": base64_image
                }
            }
        elif self.text:  
            return {
                "type": "text",
                "text": self.text
            }
        elif self.parsed:  
            return {
                "type": "text",
                "json": self.parsed.model_dump_json()
            }
        else:  
            return None


def coerce_content_list(content: Union[str, List[ContentBlock], List[Union[str, ContentBlock, ToolCall, ToolResult, BaseModel]]] = None, **content_block_kwargs) -> List[ContentBlock]:
    if not content:  
        content = [ContentBlock(**content_block_kwargs)]

    if not isinstance(content, list):  
        content = [content]

    return [ContentBlock.model_validate(ContentBlock.coerce(c)) for c in content]

class Message(BaseModel):
    role: str
    content: List[ContentBlock]

    def __init__(self, role, content: Union[str, List[ContentBlock], List[Union[str, ContentBlock, ToolCall, ToolResult, BaseModel]]] = None, **content_block_kwargs):
        content = coerce_content_list(content, **content_block_kwargs)

        super().__init__(content=content, role=role)

    @cached_property
    def text(self) -> str:
        return "\n".join(c.text or f"<{c.type}>" for c in self.content)

    @cached_property
    def text_only(self) -> str:
        return "\n".join(c.text for c in self.content if c.text)

    @cached_property
    def tool_calls(self) -> List[ToolCall]:
        return [c.tool_call for c in self.content if c.tool_call is not None]

    @cached_property
    def tool_results(self) -> List[ToolResult]:
        return [c.tool_result for c in self.content if c.tool_result is not None]

    @cached_property
    def parsed_content(self) -> List[BaseModel]:
        return [c.parsed for c in self.content if c.parsed is not None]

    def call_tools_and_collect_as_message(self, parallel=False, max_workers=None):
        if parallel:  
            with ThreadPoolExecutor(max_workers=max_workers) as executor:  
                futures = [executor.submit(c.tool_call.call_and_collect_as_message_block) for c in self.content if c.tool_call]  
                content = [future.result() for future in as_completed(futures)]
        else:  
            content = [c.tool_call.call_and_collect_as_message_block() for c in self.content if c.tool_call]
        return Message(role="user", content=content)

    def to_openai_message(self) -> Dict[str, Any]:
        message = {
            "role": "tool" if self.tool_results else self.role,
            "content": list(filter(None, [
                c.to_openai_content_block() for c in self.content
            ]))
        }
        print(message, self.content)
        if self.tool_calls:  
            message["tool_calls"] = [
                {
                    "id": tool_call.tool_call_id,
                    "type": "function",
                    "function": {
                        "name": tool_call.tool.__name__,
                        "arguments": json.dumps(tool_call.params.model_dump())
                    }
                } for tool_call in self.tool_calls
            ]
            message["content"] = None  # Set content to null when there are tool calls

        if self.tool_results:  
            message["tool_call_id"] = self.tool_results[0].tool_call_id  
            message["content"] = self.tool_results[0].result[0].text  
            assert len(self.tool_results[0].result) == 1, "Tool result should only have one content block"  
            assert self.tool_results[0].result[0].type == "text", "Tool result should only have one text content block"  
        return message

# HELPERS

def system(content: Union[str, List[ContentBlock]]) -> Message:
    """
    Create a system message with the given content.

    Args:
    content (str): The content of the system message.

    Returns:
    Message: A Message object with role set to 'system' and the provided content.
    """
    return Message(role="system", content=content)


def user(content: Union[str, List[ContentBlock]]) -> Message:
    """
    Create a user message with the given content.

    Args:
    content (str): The content of the user message.

    Returns:
    Message: A Message object with role set to 'user' and the provided content.
    """
    return Message(role="user", content=content)


def assistant(content: Union[str, List[ContentBlock]]) -> Message:
    """
    Create an assistant message with the given content.

    Args:
    content (str): The content of the assistant message.

    Returns:
    Message: A Message object with role set to 'assistant' and the provided content.
    """
    return Message(role="assistant", content=content)


# Well this is disappointing, I wanted to effectively type hint by doing that data sync meta, but eh, at least we can still reference role or content this way. Probably will can the dict sync meta. TypedDict is the ticket ell oh ell.
MessageOrDict = Union[Message, Dict[str, str]]
# Can support image prompts later.
Chat = List[
    Message
]  # [{"role": "system", "content": "prompt"}, {"role": "user", "content": "message"}]
MultiTurnLMP = Callable[..., Chat]
OneTurn = Callable[..., _lstr_generic]
# This is the specific LMP that must accept history as an argument and can take any additional arguments
ChatLMP = Callable[[Chat, Any], Chat]
LMP = Union[OneTurn, MultiTurnLMP, ChatLMP]
InvocableLM = Callable[..., _lstr_generic]

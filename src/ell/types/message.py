import json
from ell.types._lstr import _lstr
from functools import cached_property
from PIL import Image
import numpy as np
import base64
from io import BytesIO

from pydantic import BaseModel, Field, model_validator, field_validator, field_serializer
from sqlmodel import Field, SQLModel

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
        return self.tool(**self.params.model_dump())

    def call_and_collect_as_message_block(self):
        res = self.tool(**self.params.model_dump(), _tool_call_id=self.tool_call_id)
        return ContentBlock(tool_result=res)

    def call_and_collect_as_message(self):
        return Message(role="user", content=[self.call_and_collect_as_message_block()])

class ContentBlock(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    text: Optional[_lstr_generic] = Field(default=None)
    image: Optional[Image.Image] = Field(default=None)
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
    def coerce(cls, content: Union[str, ToolCall, ToolResult, BaseModel, "ContentBlock", Image.Image, np.ndarray]) -> "ContentBlock":
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
        if isinstance(content, (Image.Image, np.ndarray)):
            return cls(image=content)
        raise ValueError(f"Invalid content type: {type(content)}")

    @field_validator('image')
    @classmethod
    def validate_image(cls, v):
        if v is None:
            return v
        if isinstance(v, Image.Image):
            return v
        if isinstance(v, str):
            try:
                img_data = base64.b64decode(v)
                img = Image.open(BytesIO(img_data))
                if img.mode not in ('L', 'RGB', 'RGBA'):
                    img = img.convert('RGB')
                return img
            except:
                raise ValueError("Invalid base64 string for image")
        if isinstance(v, np.ndarray):
            if v.ndim == 3 and v.shape[2] in (3, 4):
                mode = 'RGB' if v.shape[2] == 3 else 'RGBA'
                return Image.fromarray(v, mode=mode)
            else:
                raise ValueError(f"Invalid numpy array shape for image: {v.shape}. Expected 3D array with 3 or 4 channels.")
        raise ValueError(f"Invalid image type: {type(v)}")

    @field_serializer('image')
    def serialize_image(self, image: Optional[Image.Image], _info):
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

# Define the Message class here or import it as needed
class Message(BaseModel):
    role: str
    content: List[ContentBlock]

# Helper functions
def system(content: Union[str, List[ContentBlock]]) -> Message:
    """
    Create a system message with the given content.

    Args:
        content (Union[str, List[ContentBlock]]): The content of the system message.

    Returns:
        Message: A Message object with role set to 'system' and the provided content.
    """
    return Message(role="system", content=content)


def user(content: Union[str, List[ContentBlock]]) -> Message:
    """
    Create a user message with the given content.

    Args:
        content (Union[str, List[ContentBlock]]): The content of the user message.

    Returns:
        Message: A Message object with role set to 'user' and the provided content.
    """
    return Message(role="user", content=content)


def assistant(content: Union[str, List[ContentBlock]]) -> Message:
    """
    Create an assistant message with the given content.

    Args:
        content (Union[str, List[ContentBlock]]): The content of the assistant message.

    Returns:
        Message: A Message object with role set to 'assistant' and the provided content.
    """
    return Message(role="assistant", content=content)

LMPParams = Dict[str, Any]
MessageOrDict = Union[Message, Dict[str, str]]
Chat = List[Message]
MultiTurnLMP = Callable[..., Chat]
OneTurn = Callable[..., _lstr_generic]
ChatLMP = Callable[[Chat, Any], Chat]
LMP = Union[OneTurn, MultiTurnLMP, ChatLMP]
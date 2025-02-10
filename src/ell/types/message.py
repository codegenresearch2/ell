# 1. Consistency in Comments
# Ensure that comments are concise and directly related to the code they describe.

# 2. Error Handling
# Improve error handling in the `validate_image` method by using more specific exceptions.

# 3. Return Types
# Explicitly state the return types of methods where applicable.

# 4. Field Serialization
# Ensure that all content types are handled consistently, including the `parsed` content.

# 5. Code Formatting
# Pay attention to spacing and line breaks to enhance readability.

# 6. Type Hinting
# Make sure type hints are as specific as possible.

# 7. Docstrings
# Ensure that functions and classes have clear and concise docstrings.

import base64
from io import BytesIO
from PIL import Image as PILImage
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, Union, List, Type
import numpy as np

class ToolResult(BaseModel):
    tool_call_id: str
    result: List["ContentBlock"]

class ToolCall(BaseModel):
    tool: Callable[..., Union[ToolResult, str, List["ContentBlock"]]]
    tool_call_id: Optional[str] = None
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
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    text: Optional[str] = None
    image: Optional[Union[PILImage.Image, str, np.ndarray]] = None
    audio: Optional[Union[np.ndarray, List[float]]] = None
    tool_call: Optional[ToolCall] = None
    parsed: Optional[Union[Type[BaseModel], BaseModel]] = None
    tool_result: Optional[ToolResult] = None

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
            except Exception as e:
                raise ValueError("Invalid base64 string for image") from e
        if isinstance(v, np.ndarray):
            if v.ndim == 3 and v.shape[2] in (3, 4):
                mode = 'RGB' if v.shape[2] == 3 else 'RGBA'
                return PILImage.fromarray(v, mode=mode)
            else:
                raise ValueError(f"Invalid numpy array shape for image: {v.shape}. Expected 3D array with 3 or 4 channels.")
        raise ValueError(f"Invalid image type: {type(v)}")

    @field_validator('parsed')
    @classmethod
    def validate_parsed(cls, v):
        if v is None:
            return v
        if isinstance(v, BaseModel):
            return v
        raise ValueError("Invalid parsed content type")

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
                "type": "parsed",
                "parsed": self.parsed.model_dump()
            }
        else:
            return None

    @field_serializer('image')
    def serialize_image(self, image: Optional[PILImage.Image], _info):
        if image is None:
            return None
        return base64.b64encode(image.tobytes()).decode('utf-8')

class Message(BaseModel):
    role: str
    content: List[ContentBlock]

    @property
    def text(self) -> str:
        return "\n".join(c.text or f"<{c.type}>" for c in self.content)

    @property
    def text_only(self) -> str:
        return "\n".join(c.text for c in self.content if c.text)

    @property
    def tool_calls(self) -> List[ToolCall]:
        return [c.tool_call for c in self.content if c.tool_call is not None]
    
    @property
    def tool_results(self) -> List[ToolResult]:
        return [c.tool_result for c in self.content if c.tool_result is not None]

    @property
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

    def to_openai_message(self) -> dict:
        message = {
            "role": "tool" if self.tool_results else self.role,
            "content": list(filter(None, [
                c.to_openai_content_block() for c in self.content
            ]))
        }
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
            message["content"] = None

        if self.tool_results:
            message["tool_call_id"] = self.tool_results[0].tool_call_id
            message["content"] = self.tool_results[0].result[0].text

        return message

# HELPERS 
def system(content: Union[str, List[ContentBlock]]) -> Message:
    return Message(role="system", content=content)

def user(content: Union[str, List[ContentBlock]]) -> Message:
    return Message(role="user", content=content)

def assistant(content: Union[str, List[ContentBlock]]) -> Message:
    return Message(role="assistant", content=content)
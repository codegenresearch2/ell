# 1. **Consistency in Comments**: Ensure that comments are consistent in style and clarity. For example, the comments in the gold code are concise and directly related to the code they describe. Review your comments for clarity and relevance.

# 2. **Error Handling**: In the `validate_image` method, consider being more specific in your exception handling. The gold code uses a general `except` clause, which can mask other potential issues. Aim for more precise error handling to improve maintainability.

# 3. **Return Types**: In the `to_openai_content_block` method, ensure that all possible return paths are covered. The gold code includes a return statement for the `parsed` field, which your code currently lacks. This could lead to unexpected behavior.

# 4. **Code Formatting**: Pay attention to formatting, such as spacing and line breaks. Consistent formatting improves readability and helps maintain a professional code style.

# 5. **Type Hinting**: Ensure that type hints are used consistently throughout your code. The gold code uses type hints effectively, which enhances clarity and helps with static type checking.

# 6. **Method Naming**: Review the naming conventions for your methods. Ensure they are descriptive and follow a consistent pattern, similar to the gold code.

# 7. **Docstrings**: While you have some docstrings, ensure they are comprehensive and follow a consistent format. The gold code has clear and informative docstrings that describe the purpose and parameters of each function.

from typing import Optional, Union, List, Dict, Type
from PIL import Image
import numpy as np
import base64
from io import BytesIO

class ContentBlock(BaseModel):
    text: Optional[str] = None
    image: Optional[Union[Image.Image, str, np.ndarray]] = None
    audio: Optional[Union[np.ndarray, List[float]]] = None
    tool_call: Optional['ToolCall'] = None
    parsed: Optional[Union[Type[BaseModel], BaseModel]] = None
    tool_result: Optional['ToolResult'] = None

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
    def coerce(cls, content: Union[str, 'ToolCall', 'ToolResult', BaseModel, 'ContentBlock', Image.Image, np.ndarray]) -> 'ContentBlock':
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
            except Exception as e:
                raise ValueError(f"Invalid base64 string for image: {e}")
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
        output = BytesIO()
        image.save(output, format="PNG")
        return base64.b64encode(output.getvalue()).decode("utf-8")

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
                "parsed": self.parsed
            }
        else:
            return None
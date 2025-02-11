# Check for Missing Features
def to_openai_content_block(self):
    if self.parsed:
        return self.parsed.json()
    elif self.tool_result:
        return self.tool_result.result
    elif self.text:
        return {"type": "text", "text": self.text}
    elif self.image:
        return self.serialize_image(self.image)
    else:
        raise ValueError("ContentBlock is empty or improperly configured.")

# Consistency in Comments
@field_validator('image')
def validate_image(cls, v):
    """
    Validate the image field.
    
    This method ensures that the image is in a valid format.
    It raises a ValueError if the image is not valid.
    """
    try:
        if v is None:
            return v
        if isinstance(v, PILImage.Image):
            return v
        if isinstance(v, str):
            img_data = base64.b64decode(v)
            img = PILImage.open(BytesIO(img_data))
            if img.mode not in ('L', 'RGB', 'RGBA'):
                img = img.convert('RGB')
            return img
        if isinstance(v, np.ndarray):
            if v.ndim == 3 and v.shape[2] in (3, 4):
                mode = 'RGB' if v.shape[2] == 3 else 'RGBA'
                return PILImage.fromarray(v, mode=mode)
        raise ValueError("Invalid image type or format.")
    except Exception as e:
        raise ValueError(f"Failed to validate image: {e}")

# Error Handling
@field_validator('image')
def validate_image(cls, v):
    """
    Validate the image field.
    
    This method ensures that the image is in a valid format.
    It raises a ValueError if the image is not valid.
    """
    try:
        if v is None:
            return v
        if isinstance(v, PILImage.Image):
            return v
        if isinstance(v, str):
            img_data = base64.b64decode(v)
            img = PILImage.open(BytesIO(img_data))
            if img.mode not in ('L', 'RGB', 'RGBA'):
                img = img.convert('RGB')
            return img
        if isinstance(v, np.ndarray):
            if v.ndim == 3 and v.shape[2] in (3, 4):
                mode = 'RGB' if v.shape[2] == 3 else 'RGBA'
                return PILImage.fromarray(v, mode=mode)
        raise ValueError("Invalid image type or format.")
    except Exception as e:
        raise ValueError(f"Failed to validate image: {e}")

# Formatting and Spelling
def serialize_image(self, image: Optional[PILImage.Image], _info):
    """
    Serialize the image to a base64 encoded string.
    
    This method converts the image to a base64 encoded string for easy transmission.
    """
    if image is None:
        return None
    output = BytesIO()
    image.save(output, format="JPEG")
    return base64.b64encode(output.getvalue()).decode('utf-8')

# Method Naming and Structure
class ToolCall(BaseModel):
    tool: InvocableTool
    tool_call_id: Optional[_lstr_generic] = Field(default=None)
    params: Union[Type[BaseModel], BaseModel]

    def __call__(self, **kwargs):
        assert not kwargs, "Unexpected arguments provided. Calling a tool uses the params provided in the ToolCall."
        return self.tool(**self.params.model_dump())

# Type Hinting
def to_openai_content_block(self) -> Dict[str, Any]:
    if self.parsed:
        return self.parsed.json()
    elif self.tool_result:
        return self.tool_result.result
    elif self.text:
        return {"type": "text", "text": self.text}
    elif self.image:
        return self.serialize_image(self.image)
    else:
        raise ValueError("ContentBlock is empty or improperly configured.")

# Testing for Edge Cases
def test_call_tools_and_collect_as_message():
    content_block = ContentBlock(tool_call=ToolCall(tool=lambda x: x, params=123))
    message = content_block.call_and_collect_as_message()
    assert message.role == "user"
    assert len(message.content) == 1
    assert message.content[0].tool_call is not None

# Additional Edge Case Test
def test_serialize_image_with_invalid_image():
    with pytest.raises(ValueError, match="Failed to validate image: Invalid image type or format."):
        ContentBlock(image="invalid_image_data").serialize_image(None)
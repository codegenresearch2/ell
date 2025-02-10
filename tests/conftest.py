import pytest
from unittest.mock import patch
from openai import OpenAI

@pytest.fixture(autouse=True)
def setup_test_env():
    # Mock the OpenAI client
    with patch("openai.OpenAI") as mock_openai:
        # Configure the mock client to do nothing
        mock_openai.return_value.chat.completions.create.return_value = None
        
        # Yield the mock client for use in tests
        yield mock_openai

    # Clean up after tests if necessary (commented out as not necessary in this case)
    # os.environ.pop('OPENAI_API_KEY')
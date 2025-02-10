import pytest
from unittest.mock import patch
from openai import OpenAI
import os

@pytest.fixture(autouse=True)
def setup_test_env():
    # Set a fake OpenAI API key for all tests
    os.environ['OPENAI_API_KEY'] = 'sk-fake-api-key-for-testing'
    
    # Mock the OpenAI client
    with patch("openai.OpenAI") as mock_openai:
        # Configure the mock client to return a predefined response
        mock_openai.return_value.chat.completions.create.return_value = None
        yield mock_openai

    # Clean up after tests if necessary (commented out as not necessary in this case)
    # os.environ.pop('OPENAI_API_KEY')
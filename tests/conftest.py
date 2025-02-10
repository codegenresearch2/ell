import pytest
from unittest.mock import patch
from ell.models.openai import OpenAIModelClient
import os

@pytest.fixture(autouse=True)
def setup_test_env():
    # Set a fake OpenAI API key for all tests
    os.environ['OPENAI_API_KEY'] = 'sk-fake-api-key-for-testing'
    
    # Mock the OpenAI client
    with patch("ell.models.openai.OpenAIModelClient") as mock_client:
        # Configure the mock client to return a predefined response
        mock_client.return_value.generate_completion.return_value = None
        yield mock_client
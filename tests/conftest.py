import pytest
import os
from unittest.mock import patch
from openai import OpenAI

@pytest.fixture(autouse=True)
def setup_test_env():
    # Set a fake OpenAI API key for all tests
    os.environ['OPENAI_API_KEY'] = 'sk-fake-api-key-for-testing'

    # Mock the OpenAI client
    with patch('openai.OpenAI') as mock_openai:
        # Capture the return value of the mock
        mock_client = mock_openai.return_value
        # Configure the mock client to return a specific value when a method is called
        mock_client.chat.completions.create.return_value = None
        yield mock_client

    # Clean up after tests if necessary (no specific cleanup action mentioned in gold code)
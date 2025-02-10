import pytest
from unittest.mock import patch
import os

@pytest.fixture(autouse=True)
def setup_test_env():
    # Set a fake OpenAI API key for all tests
    os.environ['OPENAI_API_KEY'] = 'sk-fake-api-key-for-testing'

    # Mock the OpenAI client
    with patch('openai.OpenAI') as mock_openai:
        # Configure the mock client to do nothing
        mock_client = mock_openai.return_value
        mock_client.chat.completions.create.return_value = None

        # Yield the mock client for use in tests
        yield mock_client

    # No cleanup needed in this case
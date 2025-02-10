import os
from unittest.mock import patch
import pytest

@pytest.fixture(autouse=True)
def setup_test_env():
    # Set a fake OpenAI API key for all tests to use
    os.environ['OPENAI_API_KEY'] = 'fake-api-key'

    # Mock the OpenAI client
    with patch('openai.OpenAI') as mock_openai:
        # Configure the mock client to do nothing for specific method calls
        mock_client = mock_openai.return_value
        mock_client.chat.completions.create.return_value = None

        # Yield the mock client for use in tests
        yield mock_client

    # No cleanup needed in this case
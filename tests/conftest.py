import pytest
from unittest.mock import patch
import os

@pytest.fixture(autouse=True)
def setup_test_env():
    # Set a fake OpenAI API key for all tests
    os.environ['OPENAI_API_KEY'] = 'fake-api-key'

    # Mock the OpenAI client
    with patch('openai.OpenAI') as mock_openai:
        # Configure the mock client to return None for specific method calls
        mock_client = mock_openai.return_value
        mock_client.chat.completions.create.return_value = None

        # Yield the mock client for use in tests
        yield mock_client

    # Clean up after tests if necessary
    # Add any necessary cleanup code here
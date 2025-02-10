import pytest
from unittest.mock import patch
import os

@pytest.fixture(autouse=True)
def setup_test_env():
    # Mock the OpenAI client
    with patch('openai.OpenAI') as MockOpenAI:
        # Configure the mock client to return None for specific method calls
        mock_client = MockOpenAI.return_value
        mock_client.chat.completions.create.return_value = None

        # Set a fake API key for testing
        # os.environ['OPENAI_API_KEY'] = 'fake-api-key'

        # Yield the mock client for use in tests
        yield mock_client

    # Cleanup after tests if necessary
import pytest
from unittest.mock import patch, Mock
import os

@pytest.fixture(autouse=True)
def setup_test_env():
    # Set a fake OpenAI API key for all tests
    os.environ['OPENAI_API_KEY'] = 'sk-fake-api-key-for-testing'

    # Mock the OpenAI client
    with patch('openai.OpenAI') as MockOpenAI:
        # Create a mock client that returns a mock object for chat.completions.create
        mock_client = MockOpenAI.return_value
        mock_client.chat.completions.create.return_value = Mock()

        # Yield the mock client for use in tests
        yield mock_client

    # Clean up after tests if necessary
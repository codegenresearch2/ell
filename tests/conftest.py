import os
import pytest
from unittest.mock import patch

@pytest.fixture(autouse=True)
def setup_test_env():
    # Set a fake OpenAI API key for testing
    os.environ['OPENAI_API_KEY'] = 'sk-fake-api-key-for-testing'

    # Mock the OpenAI client to do nothing during testing
    with patch('openai.OpenAI') as mock_openai:
        mock_client = mock_openai.return_value
        mock_client.chat.completions.create.return_value = None
        yield mock_client

    # Clean up after tests if necessary
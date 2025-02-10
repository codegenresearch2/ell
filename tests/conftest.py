import pytest
from unittest.mock import patch

@pytest.fixture(autouse=True)
def setup_test_env():
    # Set up the test environment by mocking the OpenAI client
    with patch('openai.OpenAI') as mock_openai:
        mock_client = mock_openai.return_value
        mock_client.chat.completions.create.return_value = None
        yield mock_client

    # Clean up after tests if necessary
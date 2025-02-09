import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture(autouse=True)
def setup_test_env():
    # Patch the OpenAI client
    with patch('openai.ChatCompletion.create', return_value=None) as mock_create:
        # Configure the mock client
        mock_client = MagicMock()
        mock_client.chat.completions.create = mock_create
        
        # Yield the mock client to the tests
        yield mock_client
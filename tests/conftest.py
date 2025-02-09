import pytest
from unittest.mock import patch, MagicMock
import openai

@pytest.fixture(autouse=True)
def setup_test_env():
    # Patch the OpenAI client
    with patch('openai.OpenAI') as mock_openai:
        # Configure the mock client
        mock_client = mock_openai.return_value
        mock_client.chat.completions.create = MagicMock(return_value=None)
        
        yield mock_client
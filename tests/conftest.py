import pytest
import os
from unittest.mock import patch, MagicMock
import openai

@pytest.fixture(autouse=True)
def setup_test_env():
    # Set a fake OpenAI API key for all tests
    os.environ['OPENAI_API_KEY'] = 'sk-fake-api-key-for-testing'
    
    # Patch the OpenAI client
    with patch('openai.OpenAI') as mock_openai:
        # Configure the mock client
        mock_client = MagicMock()
        mock_client.chat.completions.create = MagicMock(return_value=None)
        mock_openai.return_value = mock_client
        
        yield mock_client
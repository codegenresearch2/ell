import pytest
import os
from unittest.mock import patch
from ell.util.lm import OpenAIClient


@pytest.fixture(autouse=True)
def setup_test_env():
    # Set a fake OpenAI API key for all tests
    os.environ['OPENAI_API_KEY'] = 'sk-fake-api-key-for-testing'
    
    # Mock the OpenAI client
    with patch('ell.util.lm.OpenAIClient') as mock_client:
        yield mock_client
    
    # Clean up after tests if necessary (no specific cleanup action mentioned in gold code)
import pytest
import os
from unittest.mock import patch

@pytest.fixture(autouse=True)
def setup_test_env():
    # Set a fake OpenAI API key for all tests
    with patch('os.environ', {'OPENAI_API_KEY': 'sk-fake-api-key-for-testing'}):
        yield
    
    # Clean up after tests if necessary
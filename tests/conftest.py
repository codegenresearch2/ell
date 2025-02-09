import pytest
import os

@pytest.fixture(autouse=True)
def setup_test_env():
    # Set a fake OpenAI API key for all tests
    if 'OPENAI_API_KEY' not in os.environ:
        print("Warning: OPENAI_API_KEY is not set. Some tests may fail.")
    else:
        os.environ['OPENAI_API_KEY'] = 'sk-fake-api-key-for-testing'
    
    # You can add more environment setup here if needed
    
    yield
    
    # Clean up after tests if necessary
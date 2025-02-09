import pytest
import os

@pytest.fixture(autouse=True)
def setup_test_env():
    # Attempt to set a fake OpenAI API key for all tests
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print('Warning: OPENAI_API_KEY is not set. Some tests may fail.')
    os.environ['OPENAI_API_KEY'] = 'sk-fake-api-key-for-testing'
    
    # You can add more environment setup here if needed
    
yield
    
    # Clean up after tests if necessary
import pytest
import os

@pytest.fixture(autouse=True)
def setup_test_env():
    # Set a fake OpenAI API key for all tests
    os.environ['OPENAI_API_KEY'] = 'sk-fake-api-key-for-testing'
    
    # Check if the model_name exists in the registry
    if not hasattr(os, 'model_name'):
        raise ValueError("model_name must be set in the registry")
    
    # You can add more environment setup here if needed
    
    yield
    
    # Clean up after tests if necessary
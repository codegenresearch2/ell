import pytest
import os

@pytest.fixture(autouse=True)
def setup_test_env():
    # Set a fake OpenAI API key for all tests
    os.environ['OPENAI_API_KEY'] = 'sk-fake-api-key-for-testing'
    
    # Initialize the model client
    try:
        from ell.models.openai import OpenAIModelClient
        model_client = OpenAIModelClient()
    except ImportError:
        pytest.skip("OpenAI model client is not available")
    except Exception as e:
        print(f"Warning: Failed to initialize OpenAI model client - {e}")
        pytest.skip("OpenAI model client is not available")
    
    yield
    
    # Clean up after tests if necessary
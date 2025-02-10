import pytest
import os
from ell.models import MODEL_REGISTRY

@pytest.fixture(autouse=True)
def setup_test_env():
    # Set a fake OpenAI API key for all tests
    os.environ['OPENAI_API_KEY'] = 'sk-fake-api-key-for-testing'

    # Check for model existence in the registry
    assert 'gpt-4-turbo' in MODEL_REGISTRY, "Model 'gpt-4-turbo' not found in the registry"

    # Initialize client if needed
    # This part depends on the actual implementation of the client initialization
    # For example, if there is a function `initialize_client()`, you can call it here
    # initialize_client()

    yield

    # Clean up after tests if necessary
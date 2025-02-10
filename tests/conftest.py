import pytest
import os
import warnings
from ell.models import openai

@pytest.fixture(autouse=True)
def setup_test_env():
    # Set a fake OpenAI API key for all tests
    os.environ['OPENAI_API_KEY'] = 'sk-fake-api-key-for-testing'

    # Initialize client gracefully
    try:
        openai.client = openai.Client()
    except Exception as e:
        warnings.warn(f"Failed to initialize OpenAI client: {str(e)}")

    yield

    # Clean up after tests if necessary


In the rewritten code, the OpenAI client is initialized within the `setup_test_env` fixture. If an error occurs during client initialization, a warning is raised instead of causing the test to fail. This allows for more graceful handling of client initialization errors. Additionally, the client is now accessed directly from the `openai` module, simplifying client retrieval logic in calls.
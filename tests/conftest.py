import pytest
from unittest.mock import patch
from ell.models.openai import OpenAIModelClient

@pytest.fixture(autouse=True)
def setup_test_env():
    # Set a fake OpenAI API key for all tests
    os.environ['OPENAI_API_KEY'] = 'sk-fake-api-key-for-testing'
    
    # Mock the OpenAI client
    with patch("ell.models.openai.OpenAIModelClient") as mock_client:
        # Configure the mock client to return a predefined response
        mock_client.return_value.generate_completion.return_value = "Mocked content"
        yield mock_client

# Example test using the mocked OpenAI client
def test_mocked_openai_client(setup_test_env):
    from ell.decorators.lm import lm

    @lm(model="gpt-4-turbo", temperature=0.1, max_tokens=5)
    def lmp_with_default_system_prompt(*args, **kwargs):
        return "Test user prompt"

    result = lmp_with_default_system_prompt("input", lm_params=dict(temperature=0.5))
    assert result == "Mocked content"
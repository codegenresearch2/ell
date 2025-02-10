from unittest.mock import Mock, patch
from ell.configurator import config
import openai
import os
import logging
import colorama

logger = logging.getLogger(__name__)

def register_openai_models(client: openai.Client):
    model_data = [
        ('gpt-4-1106-preview', 'system'),
        # ... rest of the models ...
    ]
    for model_id, owned_by in model_data:
        config.register_model(model_id, client)

def get_openai_client():
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if api_key:
        return openai.Client(api_key=api_key)
    else:
        logger.warning("OPENAI_API_KEY not found in environment variables. Using default client without API key.")
        return openai.Client()

default_client = get_openai_client()
register_openai_models(default_client)
config._default_openai_client = default_client

# Mocking external API calls in tests
with patch('openai.Client.models.list') as mock_list:
    mock_list.return_value = Mock(data=[Mock(id=model_id) for model_id, _ in model_data])

# Using the client for chat completions
try:
    openai.chat.completions.create(model="gpt-4o-2024-08-06", messages=[{"role": "system", "content": "You are a helpful assistant."}])
except openai.OpenAIError as e:
    logger.error(f"An error occurred while using chat completions: {e}")
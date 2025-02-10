from unittest.mock import Mock
from ell.configurator import config
import openai
import os
import logging
import colorama

logger = logging.getLogger(__name__)

def register_openai_models(client: openai.Client):
    if client is None:
        logger.error("No client provided for model registration.")
        return

    model_data = [
        ('gpt-4-1106-preview', 'system'),
        # ... rest of the models ...
    ]

    for model_id, owned_by in model_data:
        try:
            config.register_model(model_id, client)
        except Exception as e:
            logger.error(f"Failed to register model {model_id}: {e}")

def get_openai_client():
    try:
        return openai.Client()
    except openai.OpenAIError as e:
        logger.warning(f"Failed to create default client: {e}")
        return openai.Client(api_key=os.environ.get("OPENAI_API_KEY", ""))

# In tests, use a mock client
client = get_openai_client() if os.environ.get("TESTING") != "true" else Mock()
register_openai_models(client)
config._default_openai_client = client

# Use the client for chat completions
try:
    openai.chat.completions.create(model="gpt-4o-2024-08-06", messages=[{"role": "system", "content": "You are a helpful assistant."}], client=client)
except openai.OpenAIError as e:
    logger.error(f"Failed to create chat completion: {e}")
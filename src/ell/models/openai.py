from ell.configurator import config
import openai
import logging

logger = logging.getLogger(__name__)

def register_openai_models(client: openai.Client = None):
    if client is None:
        try:
            client = openai.Client()
        except openai.OpenAIError as e:
            logger.error(f"Failed to create OpenAI client: {e}")
            return

    model_data = [
        ('gpt-4-1106-preview', 'system'),
        ('gpt-4-32k-0314', 'openai'),
        ('text-embedding-3-large', 'system'),
        ('gpt-4-0125-preview', 'system'),
        ('babbage-002', 'system'),
        ('gpt-4-turbo-preview', 'system'),
        ('gpt-4o', 'system'),   
        ('gpt-4o-2024-05-13', 'system'),
        ('gpt-4o-mini-2024-07-18', 'system'),
        ('gpt-4o-mini', 'system'),
        ('gpt-4o-2024-08-06', 'system'),
        ('gpt-3.5-turbo-0301', 'openai'),
        ('gpt-3.5-turbo-0613', 'openai'),
        ('tts-1', 'openai-internal'),
        ('gpt-3.5-turbo', 'openai'),
        ('gpt-3.5-turbo-16k', 'openai-internal'),   
        ('davinci-002', 'system'),
        ('gpt-3.5-turbo-16k-0613', 'openai'),
        ('gpt-4-turbo-2024-04-09', 'system'),
        ('gpt-3.5-turbo-0125', 'system'),
        ('gpt-4-turbo', 'system'),
        ('gpt-3.5-turbo-1106', 'system'),
        ('gpt-3.5-turbo-instruct-0914', 'system'),
        ('gpt-3.5-turbo-instruct', 'system'),
        ('gpt-4-0613', 'openai'),
        ('gpt-4', 'openai'),
        ('gpt-4-0314', 'openai')
    ]
    for model_id, owned_by in model_data:
        config.register_model(model_id, client)

default_client = None
try:
    default_client = openai.Client()
except openai.OpenAIError as e:
    logger.error(f"Failed to create default OpenAI client: {e}")

if default_client:
    register_openai_models(default_client)
    config._default_openai_client = default_client

try:
    response = openai.chat.completions.create(model="gpt-4o-2024-08-06", messages=[{"role": "system", "content": "You are a helpful assistant."}])
except openai.OpenAIError as e:
    logger.error(f"Failed to create chat completion: {e}")
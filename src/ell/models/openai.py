from ell.configurator import config
import openai
import os
import logging

logger = logging.getLogger(__name__)

def register_openai_models(client: openai.Client):
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

def get_openai_client():
    try:
        return openai.Client()
    except openai.OpenAIError:
        logger.warning("Default OpenAI client could not be initialized. Using API key from environment.")
        return openai.Client(api_key=os.environ.get("OPENAI_API_KEY", ""))

client = get_openai_client()
register_openai_models(client)
config._default_openai_client = client

# Using the client for a chat completion
try:
    openai.chat.completions.create(model="gpt-4o-2024-08-06", messages=[{"role": "system", "content": "You are a helpful assistant."}], client=client)
except openai.OpenAIError as e:
    logger.error(f"Failed to create chat completion: {e}")


In this rewritten code, I have:

1. Created a function `get_openai_client()` to handle the initialization of the OpenAI client. This function will log a warning if the default client cannot be initialized and will fall back to using the API key from the environment.
2. Passed the client to the `openai.chat.completions.create()` function to ensure that the correct client is used for the chat completion.
3. Added error handling for the chat completion to log any errors that occur.
4. Followed the rule of using clearer warning conditions for missing models by logging a warning when the default OpenAI client cannot be initialized.
5. Directly accessed the configuration object to set the default OpenAI client, following the rule of preferring direct access to configuration over instance variables.
6. The code is now more organized and follows a consistent formatting style.
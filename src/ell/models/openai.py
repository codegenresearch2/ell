from ell.configurator import config
import openai
import logging
import colorama

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

default_client = None
try:
    default_client = openai.Client()
except openai.OpenAIError as e:
    # TODO: Dont set default lcient if this is the case
    import os
    default_client = openai.Client(api_key=os.environ.get("OPENAI_API_KEY", ""))
register_openai_models(default_client)
config._default_openai_client = default_client
# assert openai.api_key is not None

# Mocking external API calls for testing purposes
def mock_api_response(status_code, json_data):
    class MockResponse:
        def __init__(self, status_code, json_data):
            self.status_code = status_code
            self.json_data = json_data

        def raise_for_status(self):
            if self.status_code >= 400:
                raise openai.OpenAIError(f"Mock API error with status code {self.status_code}")

        def json(self):
            return self.json_data

    return MockResponse(status_code, json_data)

# Example of mocking a successful API call
openai.api_response = mock_api_response(200, {"models": [{"name": "model1"}, {"name": "model2"}]})

# Example of mocking a failed API call
openai.api_response = mock_api_response(500, {"error": "Internal Server Error"})

# Handle missing API keys gracefully
try:
    openai.api_key = os.environ.get("OPENAI_API_KEY")
except KeyError:
    logger.error("API key is missing. Please set the OPENAI_API_KEY environment variable.")

# Improve client retrieval logic for models
try:
    default_client = openai.Client()
except openai.OpenAIError as e:
    logger.error(f"Failed to create OpenAI client: {e}")
    default_client = openai.Client(api_key=os.environ.get("OPENAI_API_KEY", ""))

register_openai_models(default_client)
config._default_openai_client = default_client

# Example of using the OpenAI API
try:
    response = openai.chat.completions.create(model="gpt-4o-2024-08-06", messages=[{"role": "system", "content": "You are a helpful assistant."}])
    logger.info(f"OpenAI API response: {response}")
except openai.OpenAIError as e:
    logger.error(f"Failed to call OpenAI API: {e}")
import pytest
from unittest.mock import patch
from openai import OpenAI
import os

@pytest.fixture(autouse=True)
def setup_test_env():
    # Mock the OpenAI client
    with patch("openai.OpenAI") as mock_client:
        # Configure the mock client to return a predefined response
        mock_client.return_value.chat.completions.create.return_value = None
        yield mock_client
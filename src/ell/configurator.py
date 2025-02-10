import pytest
from unittest.mock import MagicMock
from ell.configurator import config, _Config
import openai

@pytest.fixture
def setup_config():
    config.reset()
    yield
    config.reset()

@pytest.fixture
def mock_openai_client():
    return MagicMock(spec=openai.Client)

def test_register_model(setup_config, mock_openai_client):
    model_name = 'test-model'
    config.register_model(model_name, mock_openai_client)
    assert model_name in config.model_registry
    assert config.model_registry[model_name] == mock_openai_client

def test_get_client_for(setup_config, mock_openai_client):
    model_name = 'test-model'
    config.register_model(model_name, mock_openai_client)
    assert config.get_client_for(model_name) == mock_openai_client

def test_get_client_for_default(setup_config, mock_openai_client):
    config._default_openai_client = mock_openai_client
    assert config.get_client_for('unknown-model') == mock_openai_client

def test_model_registry_override(setup_config, mock_openai_client):
    model_name = 'test-model'
    config.register_model(model_name, mock_openai_client)
    override_client = MagicMock(spec=openai.Client)
    with config.model_registry_override({model_name: override_client}):
        assert config.get_client_for(model_name) == override_client
    assert config.get_client_for(model_name) == mock_openai_client

def test_init(setup_config, mock_openai_client):
    store = 'test.db'
    verbose = True
    autocommit = False
    lazy_versioning = False
    default_lm_params = {'param': 'value'}
    default_system_prompt = 'Test prompt'
    init(store, verbose, autocommit, lazy_versioning, default_lm_params, default_system_prompt, mock_openai_client)
    assert config.verbose == verbose
    assert config.lazy_versioning == lazy_versioning
    assert config.default_lm_params == default_lm_params
    assert config.default_system_prompt == default_system_prompt
    assert config._default_openai_client == mock_openai_client


This code provides test cases for the `_Config` class in the `ell.configurator` module. It uses pytest fixtures for setup and teardown, ensuring consistent metadata handling throughout the tests. The `mock_openai_client` fixture is used to mock external dependencies for tests. The tests cover model registration, retrieval, overriding, and initialization of the `_Config` class.
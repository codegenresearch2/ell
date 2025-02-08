import pytest\nimport os\nfrom unittest.mock import patch\n\n@pytest.fixture(autouse=True)\ndef setup_test_env():\n    with patch('ell.util.lm._run_lm') as mock_run_lm:\n        mock_run_lm.return_value = ('Mocked content', None)\n        yield mock_run_lm\n\n    # Clean up after tests if necessary
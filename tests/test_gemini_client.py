import pytest
from unittest.mock import MagicMock, patch
from src.antigravity_core.gemini_client import GeminiClient

@pytest.fixture
def mock_genai():
    # Patch the reference inside the module to avoid global state issues
    with patch('src.antigravity_core.gemini_client.genai.configure') as mock_config, \
         patch('src.antigravity_core.gemini_client.genai.GenerativeModel') as mock_model:
        yield mock_config, mock_model

def test_gemini_client_init_single_key(mock_genai, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test_key")
    monkeypatch.delenv("GEMINI_API_KEYS", raising=False)
    client = GeminiClient()
    assert client.api_keys == ["test_key"]
    assert client.current_key_index == 0

def test_gemini_client_init_multiple_keys(mock_genai, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEYS", "key1, key2, key3")
    client = GeminiClient()
    assert client.api_keys == ["key1", "key2", "key3"]

def test_gemini_client_rotate_key(mock_genai, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEYS", "key1, key2")
    client = GeminiClient()
    assert client.current_key_index == 0

    rotated = client._rotate_key()
    assert rotated is True
    assert client.current_key_index == 1

    rotated = client._rotate_key()
    assert rotated is True
    assert client.current_key_index == 0

def test_gemini_client_rotate_key_single(mock_genai, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEYS", "key1")
    client = GeminiClient()
    rotated = client._rotate_key()
    assert rotated is False
    assert client.current_key_index == 0

def test_generate_content_success(mock_genai, monkeypatch):
    mock_config, mock_model_class = mock_genai
    mock_model_instance = mock_model_class.return_value
    mock_model_instance.generate_content.return_value.text = "Success response"

    monkeypatch.setenv("GEMINI_API_KEY", "test_key")
    client = GeminiClient()
    result = client.generate_content("test prompt")

    assert result == "Success response"
    mock_model_instance.generate_content.assert_called_once_with("test prompt")

def test_generate_content_retry_and_rotate(mock_genai, monkeypatch):
    mock_config, mock_model_class = mock_genai
    mock_model_instance = mock_model_class.return_value

    # First call fails with quota error, second (after rotate) succeeds
    mock_model_instance.generate_content.side_effect = [
        Exception("429 RESOURCE_EXHAUSTED"),
        MagicMock(text="Success after rotate")
    ]

    monkeypatch.setenv("GEMINI_API_KEYS", "key1, key2")
    client = GeminiClient()

    with patch('time.sleep', return_value=None):
        result = client.generate_content("test prompt")

    assert result == "Success after rotate"
    assert client.current_key_index == 1
    assert mock_model_instance.generate_content.call_count == 2

def test_judge_content_passed(mock_genai, monkeypatch):
    mock_config, mock_model_class = mock_genai
    mock_model_instance = mock_model_class.return_value
    mock_model_instance.generate_content.return_value.text = "PASSED"

    monkeypatch.setenv("GEMINI_API_KEY", "test_key")
    client = GeminiClient()
    result = client.judge_content("content", "criteria")

    assert result is True

def test_judge_content_failed(mock_genai, monkeypatch):
    mock_config, mock_model_class = mock_genai
    mock_model_instance = mock_model_class.return_value
    mock_model_instance.generate_content.return_value.text = "FAILED"

    monkeypatch.setenv("GEMINI_API_KEY", "test_key")
    client = GeminiClient()
    result = client.judge_content("content", "criteria")

    assert result is False

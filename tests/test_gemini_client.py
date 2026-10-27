import pytest
from unittest.mock import MagicMock, patch
from src.antigravity_core.gemini_client import GeminiClient

@pytest.fixture
def mock_genai():
    # ⚡ Bolt: Patch the module-level genai reference (now google.genai)
    with patch('src.antigravity_core.gemini_client.genai') as mock_genai_mod:
        # New SDK: genai.Client(api_key=...) returns a client object
        mock_client_instance = MagicMock()
        mock_genai_mod.Client.return_value = mock_client_instance
        yield mock_genai_mod, mock_client_instance

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
    mock_genai_mod, mock_client_instance = mock_genai
    mock_client_instance.models.generate_content.return_value.text = "Success response"

    monkeypatch.setenv("GEMINI_API_KEY", "test_key")
    client = GeminiClient()
    result = client.generate_content("test prompt")

    assert result == "Success response"
    mock_client_instance.models.generate_content.assert_called_once()
    call_kwargs = mock_client_instance.models.generate_content.call_args
    assert call_kwargs.kwargs["contents"] == "test prompt"

def test_generate_content_retry_and_rotate(mock_genai, monkeypatch):
    mock_genai_mod, mock_client_instance = mock_genai

    # After rotate, a new client is created — simulate via side_effect on Client()
    mock_client_2 = MagicMock()
    mock_client_2.models.generate_content.return_value.text = "Success after rotate"

    # First client raises quota, second succeeds
    mock_client_instance.models.generate_content.side_effect = Exception("429 RESOURCE_EXHAUSTED")
    mock_genai_mod.Client.side_effect = [mock_client_instance, mock_client_2]

    monkeypatch.setenv("GEMINI_API_KEYS", "key1, key2")
    client = GeminiClient()

    with patch('time.sleep', return_value=None):
        result = client.generate_content("test prompt")

    assert result == "Success after rotate"
    assert client.current_key_index == 1

def test_judge_content_passed(mock_genai, monkeypatch):
    mock_genai_mod, mock_client_instance = mock_genai
    mock_client_instance.models.generate_content.return_value.text = "PASSED"

    monkeypatch.setenv("GEMINI_API_KEY", "test_key")
    client = GeminiClient()
    result = client.judge_content("content", "criteria")

    assert result is True

def test_judge_content_failed(mock_genai, monkeypatch):
    mock_genai_mod, mock_client_instance = mock_genai
    mock_client_instance.models.generate_content.return_value.text = "FAILED"

    monkeypatch.setenv("GEMINI_API_KEY", "test_key")
    client = GeminiClient()
    result = client.judge_content("content", "criteria")

    assert result is False

def test_deterministic_judge_ignores_quoted_terms_outside_negative_section(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEYS", raising=False)
    client = GeminiClient()

    assert client._deterministic_rule_judge(
        'The feature is called "special mode".',
        'The word "special mode" is forbidden in this explanatory example.',
    ) is True

def test_deterministic_judge_enforces_quoted_terms_in_negative_section(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEYS", raising=False)
    client = GeminiClient()

    assert client._deterministic_rule_judge(
        'Enable "special mode".',
        '## Negative Constraints\n- Never use "special mode".\n## Other Criteria\nAllow normal actions.',
    ) is False

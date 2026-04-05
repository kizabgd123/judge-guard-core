import sys
from unittest.mock import MagicMock
# Mock google.generativeai before any project imports attempt to load it
sys.modules.setdefault('google', MagicMock())
sys.modules.setdefault('google.generativeai', MagicMock())

import pytest
from unittest.mock import patch
from src.antigravity_core.judge_flow import BlockJudge, JudgeFlowBlock

@patch('src.antigravity_core.judge_flow.GeminiClient')
def test_block_judge_evaluate(mock_gemini_class):
    mock_gemini_instance = mock_gemini_class.return_value
    mock_gemini_instance.judge_content.return_value = True

    judge = BlockJudge("test criteria")
    result = judge.evaluate("test content")

    assert result is True
    mock_gemini_instance.judge_content.assert_called_once_with("test content", "test criteria")

@patch('src.antigravity_core.judge_flow.GeminiClient')
def test_judge_flow_block_success(mock_gemini_class):
    mock_gemini_instance = mock_gemini_class.return_value
    mock_gemini_instance.judge_content.return_value = True

    action = MagicMock(return_value="Success Result")
    judge = BlockJudge("criteria")

    flow = JudgeFlowBlock(action, judge)
    result = flow.execute({"input": "test"})

    assert result == "Success Result"
    assert action.call_count == 1

@patch('src.antigravity_core.judge_flow.GeminiClient')
def test_judge_flow_block_retry(mock_gemini_class):
    mock_gemini_instance = mock_gemini_class.return_value
    # First attempt FAILED, second attempt PASSED
    mock_gemini_instance.judge_content.side_effect = [False, True]

    action = MagicMock(side_effect=["Fail Result", "Fixed Result"])
    judge = BlockJudge("criteria")

    flow = JudgeFlowBlock(action, judge, max_retries=3)
    context = {"input": "test"}
    result = flow.execute(context)

    assert result == "Fixed Result"
    assert action.call_count == 2
    assert "feedback" in context

@patch('src.antigravity_core.judge_flow.GeminiClient')
def test_judge_flow_block_exhaust_retries(mock_gemini_class):
    mock_gemini_instance = mock_gemini_class.return_value
    mock_gemini_instance.judge_content.return_value = False

    action = MagicMock(return_value="Bad Result")
    judge = BlockJudge("criteria")

    flow = JudgeFlowBlock(action, judge, max_retries=2)

    with pytest.raises(Exception, match="failed after 2 retries"):
        flow.execute({"input": "test"})

    assert action.call_count == 2


# --- Tests for BlockJudge dependency injection (PR: Bolt: Offload Bridge I/O and reuse GeminiClient) ---

@patch('src.antigravity_core.judge_flow.GeminiClient')
def test_block_judge_uses_injected_client_not_new(mock_gemini_class):
    """When a client is injected, GeminiClient() constructor must NOT be called again."""
    injected = MagicMock()
    injected.judge_content.return_value = True

    judge = BlockJudge("criteria", client=injected)

    mock_gemini_class.assert_not_called()
    assert judge.client is injected


@patch('src.antigravity_core.judge_flow.GeminiClient')
def test_block_judge_injected_client_used_in_evaluate(mock_gemini_class):
    """evaluate() delegates to the injected client's judge_content."""
    injected = MagicMock()
    injected.judge_content.return_value = False

    judge = BlockJudge("my criteria", client=injected)
    result = judge.evaluate("some content")

    assert result is False
    injected.judge_content.assert_called_once_with("some content", "my criteria")
    mock_gemini_class.assert_not_called()


@patch('src.antigravity_core.judge_flow.GeminiClient')
def test_block_judge_injected_client_used_in_generate_report(mock_gemini_class):
    """generate_report() delegates to the injected client's generate_content."""
    injected = MagicMock()
    injected.generate_content.return_value = "Audit report text"

    judge = BlockJudge("audit criteria", client=injected)
    report = judge.generate_report("some content")

    assert report == "Audit report text"
    expected_prompt = "audit criteria\n\nUSER ACTION/CONTEXT: some content"
    injected.generate_content.assert_called_once_with(expected_prompt)
    mock_gemini_class.assert_not_called()


@patch('src.antigravity_core.judge_flow.GeminiClient')
def test_block_judge_no_client_arg_creates_new_gemini(mock_gemini_class):
    """When no client is provided, BlockJudge falls back to creating a new GeminiClient."""
    mock_instance = mock_gemini_class.return_value
    mock_instance.judge_content.return_value = True

    judge = BlockJudge("criteria")

    mock_gemini_class.assert_called_once()
    assert judge.client is mock_instance


def test_block_judge_none_client_creates_new_gemini():
    """Passing client=None explicitly must also trigger GeminiClient() fallback."""
    with patch('src.antigravity_core.judge_flow.GeminiClient') as mock_gemini_class:
        mock_instance = mock_gemini_class.return_value
        judge = BlockJudge("criteria", client=None)
        mock_gemini_class.assert_called_once()
        assert judge.client is mock_instance
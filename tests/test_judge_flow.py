import pytest
from unittest.mock import MagicMock, patch
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

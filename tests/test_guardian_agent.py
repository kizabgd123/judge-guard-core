import pytest
from unittest.mock import MagicMock, patch
from src.antigravity_core.guardian_agent import GuardianAgent

@pytest.fixture
def mock_clients():
    with patch('src.antigravity_core.guardian_agent.NotionClient') as mock_notion, \
         patch('src.antigravity_core.guardian_agent.GeminiClient') as mock_gemini:
        yield mock_notion, mock_gemini

def test_guardian_init(mock_clients, monkeypatch):
    monkeypatch.setenv("GOALS_DB_ID", "goals_id")
    monkeypatch.setenv("LOGS_DB_ID", "logs_id")
    agent = GuardianAgent()
    assert agent.goals_db == "goals_id"
    assert agent.logs_db == "logs_id"

def test_fetch_active_goals(mock_clients, monkeypatch):
    monkeypatch.setenv("GOALS_DB_ID", "goals_id")
    monkeypatch.setenv("LOGS_DB_ID", "logs_id")

    mock_notion_class, _ = mock_clients
    mock_notion = mock_notion_class.return_value
    mock_notion.query_database.return_value = [{"id": "goal1"}]

    agent = GuardianAgent()
    goals = agent.fetch_active_goals()
    assert len(goals) == 1
    mock_notion.query_database.assert_called_once()

def test_analyze_log_against_goals(mock_clients, monkeypatch):
    monkeypatch.setenv("GOALS_DB_ID", "goals_id")
    monkeypatch.setenv("LOGS_DB_ID", "logs_id")

    _, mock_gemini_class = mock_clients
    mock_gemini = mock_gemini_class.return_value
    mock_gemini.generate_content.return_value = '{"match_found": true, "goal_id": "goal1", "progress_comment": "test"}'

    agent = GuardianAgent()
    result = agent.analyze_log_against_goals("log", "goals")
    assert result["match_found"] is True
    assert result["goal_id"] == "goal1"

def test_process_logs(mock_clients, monkeypatch):
    monkeypatch.setenv("GOALS_DB_ID", "goals_id")
    monkeypatch.setenv("LOGS_DB_ID", "logs_id")

    mock_notion_class, mock_gemini_class = mock_clients
    mock_notion = mock_notion_class.return_value
    mock_gemini = mock_gemini_class.return_value

    # Mock logs and goals
    mock_notion.query_database.side_effect = [
        [{"id": "log1", "properties": {"Entry": {"title": [{"text": {"content": "log text"}}]}}}], # logs
        [{"id": "goal1", "properties": {"Name": {"title": [{"text": {"content": "goal text"}}]}}}]  # goals
    ]

    # Mock analysis
    mock_gemini.generate_content.return_value = '{"match_found": true, "goal_id": "goal1", "progress_comment": "Worked on it"}'

    agent = GuardianAgent()

    # We expect 2 calls to _get_title:
    # 1. for the goal during goals_text construction
    # 2. for the log inside _process_single_log
    with patch.object(GuardianAgent, '_get_title', side_effect=["goal text", "log text"]) as mock_get_title:
        agent.process_logs()
        # Wait for executor
        agent.close()

    # Verify Notion was updated
    assert mock_notion.query_database.call_count == 2
    mock_notion.update_page_properties.assert_called_once()
    assert mock_get_title.call_count == 2

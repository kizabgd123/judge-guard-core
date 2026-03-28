import pytest
from unittest.mock import MagicMock, patch
from src.antigravity_core.guardian_agent import GuardianAgent

@pytest.fixture
def mock_clients():
    with patch('src.antigravity_core.guardian_agent.NotionClient') as mock_notion_class, \
         patch('src.antigravity_core.guardian_agent.GeminiClient') as mock_gemini_class:
        yield mock_notion_class, mock_gemini_class

def test_guardian_agent_init(mock_clients, monkeypatch):
    monkeypatch.setenv("GOALS_DB_ID", "goals_id")
    monkeypatch.setenv("LOGS_DB_ID", "logs_id")

    agent = GuardianAgent()
    assert agent.goals_db == "goals_id"
    assert agent.logs_db == "logs_id"

def test_analyze_log_against_goals(mock_clients, monkeypatch):
    monkeypatch.setenv("GOALS_DB_ID", "goals_id")
    monkeypatch.setenv("LOGS_DB_ID", "logs_id")

    mock_notion, mock_gemini = mock_clients
    mock_gemini_instance = mock_gemini.return_value
    mock_gemini_instance.generate_content.return_value = '{"match_found": true, "goal_id": "goal1", "progress_comment": "Made progress"}'

    agent = GuardianAgent()
    goals = [{"id": "goal1", "properties": {"Name": {"title": [{"text": {"content": "Test Goal"}}]}}}]

    result = agent.analyze_log_against_goals("Test log entry", goals)
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

    # Mock _get_title to handle the structure we provided
    with patch.object(GuardianAgent, '_get_title', side_effect=["log text", "goal text"]):
        agent.process_logs()

    # Verify log marked as processed
    mock_notion.update_page_properties.assert_called_with("log1", {"Processed": {"checkbox": True}})

import pytest
from unittest.mock import MagicMock, patch
from src.antigravity_core.notion_client import NotionClient

@pytest.fixture
def notion_client(monkeypatch):
    """
    Create a NotionClient preconfigured for tests by setting the NOTION_API_KEY environment variable to "test_key".
    
    Returns:
        NotionClient: An instance configured to use the test API key.
    """
    monkeypatch.setenv("NOTION_API_KEY", "test_key")
    return NotionClient()

@patch('src.antigravity_core.notion_client.requests.Session.post')
def test_test_connection_success(mock_post, notion_client):
    mock_post.return_value.json.return_value = {"results": []}
    mock_post.return_value.status_code = 200

    result = notion_client.test_connection()
    assert result == {"results": []}
    mock_post.assert_called_once()

@patch('src.antigravity_core.notion_client.requests.Session.post')
def test_create_page(mock_post, notion_client):
    mock_post.return_value.json.return_value = {"id": "new_page_id"}
    mock_post.return_value.status_code = 200

    result = notion_client.create_page("parent_id", "Title", "Content")
    assert result["id"] == "new_page_id"

    args, kwargs = mock_post.call_args
    assert kwargs["json"]["properties"]["title"]["title"][0]["text"]["content"] == "Title"

@patch('src.antigravity_core.notion_client.requests.Session.post')
def test_query_database(mock_post, notion_client):
    mock_post.return_value.json.return_value = {"results": [{"id": "page1"}]}
    mock_post.return_value.status_code = 200

    result = notion_client.query_database("db_id", {"filter": "test"})
    assert len(result) == 1
    assert result[0]["id"] == "page1"

@patch('src.antigravity_core.notion_client.requests.Session.patch')
def test_update_page_properties(mock_patch, notion_client):
    mock_patch.return_value.json.return_value = {"id": "page_id"}
    mock_patch.return_value.status_code = 200

    result = notion_client.update_page_properties("page_id", {"Prop": {"checkbox": True}})
    assert result["id"] == "page_id"
    mock_patch.assert_called_once_with(
        "https://api.notion.com/v1/pages/page_id",
        json={"properties": {"Prop": {"checkbox": True}}}
    )

@patch('src.antigravity_core.notion_client.requests.Session.get')
def test_retrieve_database(mock_get, notion_client):
    mock_get.return_value.json.return_value = {"id": "db_id", "title": []}
    mock_get.return_value.status_code = 200

    result = notion_client.retrieve_database("db_id")
    assert result["id"] == "db_id"
    mock_get.assert_called_once_with(
        "https://api.notion.com/v1/databases/db_id"
    )

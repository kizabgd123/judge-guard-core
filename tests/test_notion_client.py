import pytest
from unittest.mock import MagicMock, patch
from src.antigravity_core.notion_client import NotionClient

@pytest.fixture
def notion_client(monkeypatch):
    monkeypatch.setenv("NOTION_API_KEY", "test_key")
    return NotionClient()

def test_test_connection_success(notion_client):
    with patch.object(notion_client.session, 'post') as mock_post:
        mock_post.return_value.json.return_value = {"results": []}
        mock_post.return_value.status_code = 200

        result = notion_client.test_connection()
        assert result == {"results": []}
        mock_post.assert_called_once()

def test_create_page(notion_client):
    with patch.object(notion_client.session, 'post') as mock_post:
        mock_post.return_value.json.return_value = {"id": "new_page_id"}
        mock_post.return_value.status_code = 200

        result = notion_client.create_page("parent_id", "Title", "Content")
        assert result["id"] == "new_page_id"

        args, kwargs = mock_post.call_args
        assert kwargs["json"]["properties"]["title"]["title"][0]["text"]["content"] == "Title"

def test_query_database(notion_client):
    with patch.object(notion_client.session, 'post') as mock_post:
        mock_post.return_value.json.return_value = {"results": [{"id": "page1"}]}
        mock_post.return_value.status_code = 200

        result = notion_client.query_database("db_id", {"filter": "test"})
        assert len(result) == 1
        assert result[0]["id"] == "page1"

def test_update_page_properties(notion_client):
    with patch.object(notion_client.session, 'patch') as mock_patch:
        mock_patch.return_value.json.return_value = {"id": "page_id"}
        mock_patch.return_value.status_code = 200

        result = notion_client.update_page_properties("page_id", {"Prop": {"checkbox": True}})
        assert result["id"] == "page_id"
        mock_patch.assert_called_once_with(
            "https://api.notion.com/v1/pages/page_id",
            json={"properties": {"Prop": {"checkbox": True}}}
        )

def test_retrieve_database(notion_client):
    with patch.object(notion_client.session, 'get') as mock_get:
        mock_get.return_value.json.return_value = {"id": "db_id", "title": []}
        mock_get.return_value.status_code = 200

        result = notion_client.retrieve_database("db_id")
        assert result["id"] == "db_id"
        mock_get.assert_called_once_with(
            "https://api.notion.com/v1/databases/db_id"
        )

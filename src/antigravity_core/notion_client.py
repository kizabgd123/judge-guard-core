import os
import logging
import threading
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class NotionClient:
    """
    Antigravity Notion Integration Client.
    Handles read/write operations to Notion API.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        # ⚡ Bolt: Defer load_dotenv to __init__ only if NOTION_API_KEY is missing from environment
        if not api_key and "NOTION_API_KEY" not in os.environ:
            from dotenv import load_dotenv
            load_dotenv()

        self.api_key = api_key or os.getenv("NOTION_API_KEY")
        if not self.api_key:
            raise ValueError("NOTION_API_KEY not found. Set it in .env or pass as argument.")
        
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        self._session = None
        self._session_lock = threading.RLock()

    @property
    def session(self):
        """⚡ Bolt: Lazy-load requests and initialize session on demand (thread-safe)."""
        if self._session is None:
            with self._session_lock:
                if self._session is None:
                    import requests
                    session = requests.Session()
                    session.headers.update(self.headers)
                    self._session = session
        return self._session

    def close(self):
        """⚡ Bolt: Ensure session resource teardown."""
        if hasattr(self, "_session") and self._session is not None:
            with self._session_lock:
                if self._session is not None:
                    self._session.close()
                    self._session = None

    def __del__(self):
        self.close()
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the connection by listing accessible pages."""
        try:
            response = self.session.post(
                f"{self.base_url}/search",
                json={"page_size": 1}
            )
            response.raise_for_status()
            logger.info("✅ Notion connection successful!")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Notion connection failed: {e}")
            raise
    
    def create_page(self, parent_id: str, title: str, content: str) -> Dict[str, Any]:
        """Create a new page in Notion."""
        payload = {
            "parent": {"page_id": parent_id},
            "properties": {
                "title": {
                    "title": [{"text": {"content": title}}]
                }
            },
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": content}}]
                    }
                }
            ]
        }
        
        response = self.session.post(
            f"{self.base_url}/pages",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def create_database(self, parent_page_id: str, title: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new database in Notion."""
        payload = {
            "parent": {"type": "page_id", "page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": title}}],
            "properties": properties
        }
        
        response = self.session.post(
            f"{self.base_url}/databases",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def append_to_database(self, database_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new entry to a Notion database."""
        payload = {
            "parent": {"database_id": database_id},
            "properties": properties
        }
        
        response = self.session.post(
            f"{self.base_url}/pages",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def query_database(self, database_id: str, filter_criteria: Optional[Dict] = None) -> List[Dict]:
        """Query a Notion database with optional filters."""
        payload = {}
        if filter_criteria:
            payload["filter"] = filter_criteria
        
        response = self.session.post(
            f"{self.base_url}/databases/{database_id}/query",
            json=payload
        )
        response.raise_for_status()
        return response.json().get("results", [])
    def update_page_properties(self, page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update properties of an existing page."""
        payload = {"properties": properties}
        
        response = self.session.patch(
            f"{self.base_url}/pages/{page_id}",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def retrieve_database(self, database_id: str) -> Dict[str, Any]:
        """Retrieve a database object to inspect schema."""
        response = self.session.get(
            f"{self.base_url}/databases/{database_id}"
        )
        response.raise_for_status()
        return response.json()

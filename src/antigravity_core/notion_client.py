import os
import logging
from typing import Dict, List, Any, Optional
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class NotionClient:
    """
    Antigravity Notion Integration Client.
    Handles read/write operations to Notion API.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the NotionClient with an API key and a configured HTTP session.
        
        If `api_key` is not provided, the value is read from the `NOTION_API_KEY` environment variable. Raises ValueError when no API key is available. On success, sets `self.base_url`, constructs `self.headers`, creates a persistent `requests.Session`, and applies the headers to the session.
        
        Parameters:
            api_key (Optional[str]): Notion API key; if omitted, read from the `NOTION_API_KEY` environment variable.
        """
        self.api_key = api_key or os.getenv("NOTION_API_KEY")
        if not self.api_key:
            raise ValueError("NOTION_API_KEY not found. Set it in .env or pass as argument.")
        
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        # ⚡ Bolt: Use requests.Session for connection pooling and better performance
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Verify connectivity to the Notion API by performing a minimal search.
        
        Performs a search request limited to one result to validate authorization and reachability.
        
        Returns:
            dict: Parsed JSON response from the Notion API search endpoint.
        
        Raises:
            requests.exceptions.RequestException: If the HTTP request fails or the response status indicates an error.
        """
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
        """
        Create a new page under the specified parent page in Notion.
        
        The created page will have the provided title and a single paragraph block containing the given content.
        
        Parameters:
            parent_id (str): Notion page ID to use as the parent for the new page.
            title (str): Title text for the new page.
            content (str): Paragraph content to include as the page's first block.
        
        Returns:
            dict: The Notion API JSON response for the created page.
        """
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
        """
        Create a new Notion database under the specified parent page.
        
        Parameters:
            parent_page_id (str): The Notion page ID that will be the parent of the new database.
            title (str): The title to assign to the new database.
            properties (Dict[str, Any]): The Notion properties schema for the database (fields and their types).
        
        Returns:
            Dict[str, Any]: The JSON response from the Notion API representing the created database.
        """
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
        """
        Add a new page (row) to the specified Notion database.
        
        Parameters:
            database_id (str): Notion database ID to append the page to.
            properties (Dict[str, Any]): Notion-formatted properties for the new page.
        
        Returns:
            Dict[str, Any]: JSON response representing the created page.
        """
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
        """
        Query a Notion database and return the matching page results.
        
        Parameters:
            database_id (str): The Notion database ID to query.
            filter_criteria (Optional[Dict]): A Notion-compatible filter object to limit results (as described by the Notion API).
        
        Returns:
            List[Dict]: The list of page result objects returned by the query; an empty list if no results are found.
        """
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
        """
        Update properties of a Notion page.
        
        Parameters:
            page_id (str): ID of the page to update.
            properties (Dict[str, Any]): Properties formatted for the Notion API to apply to the page.
        
        Returns:
            Dict[str, Any]: The Notion API JSON response representing the updated page.
        """
        payload = {"properties": properties}
        
        response = self.session.patch(
            f"{self.base_url}/pages/{page_id}",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def retrieve_database(self, database_id: str) -> Dict[str, Any]:
        """
        Retrieve a Notion database object by its ID for schema inspection.
        
        Parameters:
            database_id (str): The Notion database ID to retrieve.
        
        Returns:
            dict: The JSON-decoded database object returned by the Notion API.
        
        Raises:
            requests.exceptions.HTTPError: If the API response has a non-success status code.
        """
        response = self.session.get(
            f"{self.base_url}/databases/{database_id}"
        )
        response.raise_for_status()
        return response.json()

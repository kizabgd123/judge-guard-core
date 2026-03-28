import os
import logging
import json
from typing import List, Dict, Any
from src.antigravity_core.gemini_client import GeminiClient
from src.antigravity_core.notion_client import NotionClient

logger = logging.getLogger(__name__)

class KaggleAgent:
    """
    Agent capable of interacting with Kaggle, reasoning, and logging to Notion.
    """
    def __init__(self, name: str = "Alpha"):
        self.name = name
        self.gemini = GeminiClient()
        # Initialize NotionClient only if API key is present
        try:
            self.notion = NotionClient()
        except Exception:
            self.notion = None
        self.notion_db_id = os.getenv("NOTION_KAGGLE_DB_ID")

    def step(self, task: str) -> Dict[str, Any]:
        """Performs a single reasoning/action step."""
        prompt = f"""
        You are an elite Data Scientist agent named '{self.name}' participating in a Kaggle challenge.
        Current Task: {task}

        Analyze the task, plan your next move, and describe it.
        Provide your response in JSON format:
        {{
            "thought": "Deep internal reasoning",
            "message": "What you want to say to the audience (short and clear)",
            "mood": "happy/thinking/stressed/excited/frustrated",
            "status": "success/fail/checkpoint"
        }}
        """
        response_raw = self.gemini.generate_content(prompt)
        # Cleanup JSON
        response_raw = response_raw.replace("```json", "").replace("```", "").strip()
        try:
            data = json.loads(response_raw)
        except json.JSONDecodeError:
            data = {
                "thought": "Error decoding response",
                "message": response_raw,
                "mood": "thinking",
                "status": "fail"
            }

        # Log to Notion
        self._log_to_notion(data)

        return data

    def _log_to_notion(self, data: Dict[str, Any]):
        """Logs a checkpoint or fail to Notion."""
        if not self.notion or not self.notion_db_id:
            logger.warning("No NotionClient or NOTION_KAGGLE_DB_ID found.")
            return

        properties = {
            "Agent": {"title": [{"text": {"content": self.name}}]},
            "Status": {"select": {"name": data["status"]}},
            "Message": {"rich_text": [{"text": {"content": data["message"][:2000]}}]},
            "Mood": {"rich_text": [{"text": {"content": data["mood"]}}]}
        }
        try:
            self.notion.append_to_database(self.notion_db_id, properties)
        except Exception as e:
            logger.error(f"Failed to log to Notion: {e}")

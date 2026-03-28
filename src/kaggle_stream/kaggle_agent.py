import os
import logging
import json
from typing import List, Dict, Any, Optional
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
        try:
            self.notion = NotionClient()
        except Exception:
            self.notion = None
        self.notion_db_id = os.getenv("NOTION_KAGGLE_DB_ID")

        # Kaggle API Setup
        try:
            from kaggle.api.kaggle_api_extended import KaggleApi
            self.kaggle_api = KaggleApi()
            self.kaggle_api.authenticate()
        except Exception as e:
            logger.warning(f"Kaggle API Authentication failed (likely missing credentials): {e}")
            self.kaggle_api = None

    def step(self, task: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Performs a single reasoning/action step."""
        kaggle_info = ""
        if self.kaggle_api:
            try:
                # Fetch basic info to provide context to Gemini
                competitions = self.kaggle_api.competitions_list(search=task[:50])
                if competitions:
                    comp = competitions[0]
                    kaggle_info = f"Found Kaggle Competition: {comp.title} ({comp.ref}). Deadline: {comp.deadline}"
            except Exception:
                kaggle_info = "Kaggle API available but could not fetch competition details."

        prompt = f"""
        You are an elite Data Scientist agent named '{self.name}' participating in a Kaggle challenge.
        {kaggle_info}

        Current Task: {task}
        Previous Context: {context if context else 'None'}

        Analyze the task, plan your next move, and describe it.
        Provide your response in JSON format:
        {{
            "thought": "Deep internal reasoning including code strategy",
            "message": "What you want to say to the audience (short and clear)",
            "mood": "happy/thinking/stressed/excited/frustrated",
            "status": "success/fail/checkpoint",
            "code_snippet": "Optional Python code you would run"
        }}
        """
        response_raw = self.gemini.generate_content(prompt)
        response_raw = response_raw.replace("```json", "").replace("```", "").strip()
        try:
            data = json.loads(response_raw)
        except json.JSONDecodeError:
            data = {"thought": "Error", "message": response_raw, "mood": "thinking", "status": "fail"}

        self._log_to_notion(data)
        return data

    def _log_to_notion(self, data: Dict[str, Any]):
        if not self.notion or not self.notion_db_id:
            return

        properties = {
            "Agent": {"title": [{"text": {"content": self.name}}]},
            "Status": {"select": {"name": data.get("status", "checkpoint")}},
            "Message": {"rich_text": [{"text": {"content": data.get("message", "")[:2000]}}]},
            "Mood": {"rich_text": [{"text": {"content": data.get("mood", "thinking")}}]}
        }
        try:
            self.notion.append_to_database(self.notion_db_id, properties)
        except Exception:
            pass

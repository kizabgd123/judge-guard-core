import os
import logging
import json
import random
from typing import List, Dict, Any, Optional
from src.antigravity_core.gemini_client import GeminiClient
from src.antigravity_core.notion_client import NotionClient

logger = logging.getLogger(__name__)

class KaggleAgent:
    """
    Agent capable of interacting with Kaggle, reasoning, and logging to a sophisticated Notion Dashboard.
    """
    def __init__(self, name: str = "Alpha"):
        self.name = name
        self.gemini = GeminiClient()
        self.notion_db_id = os.getenv("NOTION_KAGGLE_DB_ID")
        self.last_score = 0.0
        self.progress = 0

        try:
            self.notion = NotionClient()
        except Exception:
            self.notion = None

        try:
            from kaggle.api.kaggle_api_extended import KaggleApi
            self.kaggle_api = KaggleApi()
            self.kaggle_api.authenticate()
        except Exception:
            self.kaggle_api = None

    def step(self, task: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Performs a single reasoning/action step and updates metrics."""
        kaggle_info = ""
        if self.kaggle_api:
            try:
                competitions = self.kaggle_api.competitions_list(search=task[:50])
                if competitions:
                    comp = competitions[0]
                    kaggle_info = f"Found Kaggle Competition: {comp.title}. Current Deadline: {comp.deadline}"
            except Exception:
                kaggle_info = "Kaggle API available but could not fetch details."

        prompt = f"""
        You are an elite Data Scientist agent named '{self.name}'.
        {kaggle_info}

        Current Task: {task}
        Previous Context: {context if context else 'None'}
        Current Progress: {self.progress}%
        Last Accuracy/Score: {self.last_score}

        Analyze the task, plan your move, and provide an updated Accuracy/Score and Progress percentage.
        Accuracy/Score should be between 0 and 1. Progress should be 0 to 100.

        Provide your response in JSON format:
        {{
            "thought": "Deep reasoning",
            "message": "Message to audience",
            "mood": "happy/thinking/stressed/excited/frustrated",
            "status": "success/fail/checkpoint",
            "accuracy": 0.85,
            "progress_increment": 10
        }}
        """
        response_raw = self.gemini.generate_content(prompt)
        response_raw = response_raw.replace("```json", "").replace("```", "").strip()
        try:
            data = json.loads(response_raw)
        except json.JSONDecodeError:
            data = {"thought": "Error", "message": response_raw, "mood": "thinking", "status": "fail", "accuracy": self.last_score, "progress_increment": 0}

        # Update internal state
        self.last_score = data.get("accuracy", self.last_score)
        self.progress = min(100, self.progress + data.get("progress_increment", 0))
        data["total_progress"] = self.progress

        self._log_to_notion(data)
        return data

    def _log_to_notion(self, data: Dict[str, Any]):
        """Logs to the Advanced Dashboard schema."""
        if not self.notion or not self.notion_db_id:
            return

        properties = {
            "Agent": {"title": [{"text": {"content": self.name}}]},
            "Status": {"select": {"name": data.get("status", "checkpoint")}},
            "Message": {"rich_text": [{"text": {"content": data.get("message", "")[:2000]}}]},
            "Mood": {"rich_text": [{"text": {"content": data.get("mood", "thinking")}}]},
            "Accuracy": {"number": data.get("accuracy", 0.0)},
            "Progress": {"number": data.get("total_progress", 0) / 100.0} # Notion Progress bars use decimals (0-1)
        }
        try:
            self.notion.append_to_database(self.notion_db_id, properties)
        except Exception as e:
            logger.error(f"Notion Logging failed: {e}")

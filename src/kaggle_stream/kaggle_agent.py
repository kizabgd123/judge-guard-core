import os
import logging
import json
import random
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional
from src.antigravity_core.gemini_client import GeminiClient
from src.antigravity_core.notion_client import NotionClient

logger = logging.getLogger(__name__)

class KaggleAgent:
    """
    Agent capable of interacting with Kaggle, reasoning, and logging to a sophisticated Notion Dashboard.
    Supports DEMO MODE for visualization without keys.
    """
    def __init__(self, name: str = "Alpha"):
        self.name = name
        self.last_score = 0.0
        self.progress = 0
        self.demo_mode = False
        # ⚡ Bolt: Executor for offloading synchronous Notion API calls
        self._executor = ThreadPoolExecutor(max_workers=2)

        # Try to initialize Gemini, but catch ALL exceptions to enable Demo Mode
        try:
            self.gemini = GeminiClient()
        except Exception as e:
            logger.info(f"Gemini initialization failed ({e}). Entering Demo Mode for {self.name}.")
            self.gemini = None
            self.demo_mode = True

        try:
            self.notion = NotionClient()
        except Exception:
            self.notion = None

    def step(self, task: str, context: Optional[str] = None) -> Dict[str, Any]:
        # If Gemini is present but API key is dummy/invalid, it might still fail at runtime
        if self.demo_mode or not self.gemini:
            return self._get_demo_data()

        prompt = f"You are agent {self.name}. Task: {task}. Context: {context}. Return JSON: thought, message, mood, status, accuracy, progress_increment."
        try:
            response_raw = self.gemini.generate_content(prompt)
            response_raw = response_raw.replace("```json", "").replace("```", "").strip()
            data = json.loads(response_raw)
        except Exception as e:
            logger.warning(f"Gemini API call failed: {e}. Falling back to Demo Data.")
            return self._get_demo_data()

        self._update_state(data)
        self._log_to_notion(data)
        return data

    def _get_demo_data(self) -> Dict[str, Any]:
        thoughts = [
            f"{self.name} is checking for null values in the dataset.",
            f"{self.name} is applying a Random Forest regressor with cross-validation.",
            f"{self.name} is engineering new features from the timestamp column.",
            f"{self.name} is analyzing the correlation matrix."
        ]
        messages = [
            "I just found a massive correlation between X and Y! This is huge.",
            "The validation score is rising. We're on the right track.",
            "Let's try one more tuning of the hyperparameters.",
            "I'm feeling good about this submission!"
        ]
        moods = ["happy", "thinking", "excited", "focused"]

        data = {
            "thought": random.choice(thoughts),
            "message": random.choice(messages),
            "mood": random.choice(moods),
            "status": "success",
            "accuracy": round(random.uniform(0.7, 0.95), 3),
            "progress_increment": 20
        }
        self._update_state(data)
        self._log_to_notion(data)
        return data

    def _update_state(self, data: Dict[str, Any]):
        self.last_score = data.get("accuracy", self.last_score)
        self.progress = min(100, self.progress + data.get("progress_increment", 0))
        data["total_progress"] = self.progress

    def _log_to_notion(self, data: Dict[str, Any]):
        if self.notion and os.getenv("NOTION_KAGGLE_DB_ID") and os.getenv("NOTION_KAGGLE_DB_ID") != "demo":
            # ⚡ Bolt: Offload blocking Notion API call to background thread
            self._executor.submit(self._execute_notion_append, data)

    def _execute_notion_append(self, data: Dict[str, Any]):
        try:
            properties = {
                "Agent": {"title": [{"text": {"content": self.name}}]},
                "Status": {"select": {"name": data.get("status", "checkpoint")}},
                "Message": {"rich_text": [{"text": {"content": data.get("message", "")[:2000]}}]},
                "Mood": {"rich_text": [{"text": {"content": data.get("mood", "thinking")}}]},
                "Accuracy": {"number": data.get("accuracy", 0.0)},
                "Progress": {"number": data.get("total_progress", 0) / 100.0}
            }
            self.notion.append_to_database(os.getenv("NOTION_KAGGLE_DB_ID"), properties)
        except Exception:
            pass

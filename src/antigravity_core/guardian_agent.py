import os
import threading
from typing import List, Dict, Any

class GuardianAgent:
    """
    The Guardian: Connects Daily Logs to Goals using AI validation.
    """
    def __init__(self):
        self._notion = None
        self._gemini = None
        # ⚡ Bolt: Lock for thread-safe lazy initialization
        self._init_lock = threading.Lock()

        # ⚡ Bolt: Initialize properties to None for lazy loading
        self._logger = None
        self._executor = None
        self._setup_done = False

        self._ensure_setup()
        self.goals_db = os.getenv("GOALS_DB_ID")
        self.logs_db = os.getenv("LOGS_DB_ID")
        
        if not self.goals_db or not self.logs_db:
            raise ValueError("Database IDs missing in .env")

    def _ensure_setup(self):
        """⚡ Bolt: Thread-safe lazy setup for environment and logging."""
        if not self._setup_done:
            with self._init_lock:
                if not self._setup_done:
                    from dotenv import load_dotenv
                    load_dotenv()
                    self._setup_done = True

    @property
    def logger(self):
        """⚡ Bolt: Lazy-load logger to minimize import overhead."""
        if self._logger is None:
            with self._init_lock:
                if self._logger is None:
                    import logging
                    self._logger = logging.getLogger(__name__)
        return self._logger

    @property
    def executor(self):
        """⚡ Bolt: Lazy-load ThreadPoolExecutor."""
        if self._executor is None:
            with self._init_lock:
                if self._executor is None:
                    from concurrent.futures import ThreadPoolExecutor
                    self._executor = ThreadPoolExecutor(max_workers=5)
        return self._executor

    def __del__(self):
        self.close()

    @property
    def gemini(self):
        """⚡ Bolt: Lazy property to defer GeminiClient initialization (thread-safe)."""
        if self._gemini is None:
            with self._init_lock:
                if self._gemini is None:
                    from src.antigravity_core.gemini_client import GeminiClient
                    self._gemini = GeminiClient()
        return self._gemini

    @property
    def notion(self):
        """⚡ Bolt: Lazy property to defer NotionClient initialization (thread-safe)."""
        if self._notion is None:
            with self._init_lock:
                if self._notion is None:
                    from src.antigravity_core.notion_client import NotionClient
                    self._notion = NotionClient()
        return self._notion

    def close(self):
        """⚡ Bolt: Ensure ThreadPoolExecutor is cleanly shut down."""
        if self._executor:
            self._executor.shutdown(wait=True)

    def fetch_active_goals(self) -> List[Dict]:
        """Fetch goals currently 'In Progress' or 'Not Started'."""
        return self.notion.query_database(self.goals_db, {
            "property": "Status",
            "status": {
                "does_not_equal": "Done"
            }
        })

    def fetch_unprocessed_logs(self) -> List[Dict]:
        """Fetch logs that haven't been analyzed yet."""
        return self.notion.query_database(self.logs_db, {
            "property": "Processed",
            "checkbox": {
                "equals": False
            }
        })

    def analyze_log_against_goals(self, log_entry: str, goals_text: str) -> Dict[str, Any]:
        """
        Ask Gemini if this log entry advances any of the goals.
        """
        import json
        prompt = f"""
        You are The Guardian, an accountability AI.
        
        USER GOALS:
        {goals_text}
        
        DAILY LOG ENTRY:
        "{log_entry}"
        
        TASK:
        Does this log entry indicate progress on ANY of the goals above?
        
        OUTPUT FORMAT:
        Return ONLY a JSON object (no markdown). 
        {{
            "match_found": true/false,
            "goal_id": "ID of the matched goal or null",
            "progress_comment": "Short clear summary of progress (e.g. 'User read 50 pages') or null"
        }}
        """
        
        try:
            # ⚡ Bolt: Use max_output_tokens=256 to reduce latency for JSON analysis while avoiding truncation
            response = self.gemini.generate_content(prompt, generation_config={"max_output_tokens": 256})
            # Basic cleanup if model adds markdown
            response = response.replace("```json", "").replace("```", "").strip()
            return json.loads(response)
        except Exception as e:
            self.logger.error(f"Judge Error: {e}")
            return {"match_found": False}

    def _process_single_log(self, log: Dict, goals_text: str):
        """⚡ Bolt: Helper to process a single log (reasoning + I/O)."""
        log_text = self._get_title(log)
        log_id = log["id"]

        self.logger.info(f"Analyzing log: '{log_text}'")
        analysis = self.analyze_log_against_goals(log_text, goals_text)

        if analysis.get("match_found"):
            goal_id = analysis["goal_id"]
            self.logger.info(f"✅ Progress Detected! Linked to Goal ID: {goal_id}")
            self._mark_processed(log_id, True)
        else:
            self.logger.info("No specific goal progress detected.")
            self._mark_processed(log_id, True) # Mark processed anyway so we don't loop

    def process_logs(self):
        """Main execution loop."""
        self.logger.info("🛡️ Guardian Active: Fetching logs...")

        # ⚡ Bolt: Fetch logs first to allow for an early exit.
        logs = self.fetch_unprocessed_logs()

        if not logs:
            self.logger.info("No unprocessed logs found. Short-circuiting.")
            return

        # ⚡ Bolt: We have logs to process.
        # Now trigger Gemini warmup (import-heavy) and Goals fetching (I/O-heavy) in parallel.
        gemini_warmup = self.executor.submit(lambda: self.gemini)
        goals_future = self.executor.submit(self.fetch_active_goals)

        self.logger.info(f"Found {len(logs)} new logs. Fetching goals and finalizing warmup in parallel...")

        goals = goals_future.result()
        gemini_warmup.result()

        self.logger.info(f"Processing logs against {len(goals)} active goals.")

        # ⚡ Bolt: Pre-calculate goals context once.
        goals_text = "\n".join([f"- ID: {g['id']} | Goal: {self._get_title(g)}" for g in goals])

        # ⚡ Bolt: Parallelize processing to overlap Gemini and Notion API calls.
        list(self.executor.map(lambda log_item: self._process_single_log(log_item, goals_text), logs))

    def _mark_processed(self, page_id: str, processed: bool):
        """Updates the 'Processed' checkbox in Notion."""
        try:
            self.notion.update_page_properties(page_id, {
                "Processed": {"checkbox": processed}
            })
            self.logger.info(f"Marked Log {page_id} as processed.")
        except Exception as e:
            self.logger.error(f"Failed to update Notion page {page_id}: {e}")

    def _get_title(self, page: Dict) -> str:
        """Helper to extract title from Notion page object."""
        try:
            # Adjust based on likely schema. 'Name' or 'Entry' for logs?
            # Creating resilient getter
            props = page["properties"]
            title_prop = next((v for k,v in props.items() if v["id"] == "title"), None)
            if title_prop and title_prop["title"]:
                return title_prop["title"][0]["text"]["content"]
            
            # Fallback for 'Entry' property if it's a Rich Text, not Title
            entry = props.get("Entry", {}).get("rich_text", [])
            if entry:
                return entry[0]["text"]["content"]
                
            return "Untitled"
        except Exception:
            return "Error extracting title"

import os
import logging
import json
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
# Setup
load_dotenv()
logger = logging.getLogger(__name__)

class GuardianAgent:
    """
    The Guardian: Connects Daily Logs to Goals using AI validation.
    """
    def __init__(self):
        self._notion = None
        self._gemini = None
        self.goals_db = os.getenv("GOALS_DB_ID")
        self.logs_db = os.getenv("LOGS_DB_ID")
        
        if not self.goals_db or not self.logs_db:
            raise ValueError("Database IDs missing in .env")

        # ⚡ Bolt: Executor for parallelizing I/O-bound Gemini and Notion calls
        self._executor = ThreadPoolExecutor(max_workers=5)

    def __del__(self):
        self.close()

    @property
    def gemini(self):
        """⚡ Bolt: Lazy property to defer GeminiClient initialization."""
        if self._gemini is None:
            from src.antigravity_core.gemini_client import GeminiClient
            self._gemini = GeminiClient()
        return self._gemini

    @property
    def notion(self):
        """⚡ Bolt: Lazy property to defer NotionClient initialization."""
        if self._notion is None:
            from src.antigravity_core.notion_client import NotionClient
            self._notion = NotionClient()
        return self._notion

    def close(self):
        """⚡ Bolt: Ensure ThreadPoolExecutor is cleanly shut down."""
        if hasattr(self, "_executor"):
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
        # ⚡ Bolt: Early return if no goals exist to avoid redundant AI calls
        if not goals_text.strip():
            return {"match_found": False}

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
            logger.error(f"Judge Error: {e}")
            return {"match_found": False}

    def _process_single_log(self, log: Dict, goals_text: str):
        """⚡ Bolt: Helper to process a single log (reasoning + I/O)."""
        log_text = self._get_title(log)
        log_id = log["id"]

        logger.info(f"Analyzing log: '{log_text}'")
        analysis = self.analyze_log_against_goals(log_text, goals_text)

        if analysis.get("match_found"):
            goal_id = analysis["goal_id"]
            logger.info(f"✅ Progress Detected! Linked to Goal ID: {goal_id}")
            self._mark_processed(log_id, True)
        else:
            logger.info("No specific goal progress detected.")
            self._mark_processed(log_id, True) # Mark processed anyway so we don't loop

    def process_logs(self):
        """Main execution loop."""
        logger.info("🛡️ Guardian Active: Fetching data...")

        # ⚡ Bolt: Parallelize initial fetches and Gemini warmup to hide cold-start latency.
        # This overlaps high-latency Notion API calls with the heavy 'google-generativeai' import.
        logs_future = self._executor.submit(self.fetch_unprocessed_logs)
        goals_future = self._executor.submit(self.fetch_active_goals)
        # Warmup gemini (trigger lazy import) in background
        self._executor.submit(lambda: self.gemini)

        logs = logs_future.result()
        if not logs:
            logger.info("No new logs found.")
            return

        goals = goals_future.result()
        logger.info(f"Found {len(logs)} new logs and {len(goals)} active goals.")

        if not goals:
            logger.info("No active goals found. Marking logs as processed in parallel.")
            # ⚡ Bolt: Parallelize marking as processed to reduce latency
            list(self._executor.map(lambda log: self._mark_processed(log["id"], True), logs))
            return

        # ⚡ Bolt: Pre-calculate goals context once to avoid redundant O(G) work in the loop
        # This avoids O(L * G) complexity by pre-building the context once.
        goals_text = "\n".join([f"- ID: {g['id']} | Goal: {self._get_title(g)}" for g in goals])

        # ⚡ Bolt: Parallelize processing to reduce total turn-around time
        # This overlaps the high-latency Gemini and Notion API calls.
        list(self._executor.map(lambda log_item: self._process_single_log(log_item, goals_text), logs))

    def _mark_processed(self, page_id: str, processed: bool):
        """Updates the 'Processed' checkbox in Notion."""
        try:
            self.notion.update_page_properties(page_id, {
                "Processed": {"checkbox": processed}
            })
            logger.info(f"Marked Log {page_id} as processed.")
        except Exception as e:
            logger.error(f"Failed to update Notion page {page_id}: {e}")

    def _get_title(self, page: Dict) -> str:
        """Helper to extract title from Notion page object."""
        try:
            props = page["properties"]
            
            # ⚡ Bolt: Fast-path for common property names to avoid O(N) property scan
            for key in ["Name", "Title", "Entry", "Goal"]:
                if key in props:
                    prop = props[key]
                    # Check if it's a Title type
                    if "title" in prop and prop["title"]:
                        return prop["title"][0]["text"]["content"]
                    # Check if it's a Rich Text type
                    if "rich_text" in prop and prop["rich_text"]:
                        return prop["rich_text"][0]["text"]["content"]

            # Fallback: slow-path scan for property with id "title"
            title_prop = next((v for k,v in props.items() if v.get("id") == "title"), None)
            if title_prop and title_prop.get("title"):
                return title_prop["title"][0]["text"]["content"]
                
            return "Untitled"
        except Exception:
            return "Error extracting title"

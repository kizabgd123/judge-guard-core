import os
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
from dotenv import load_dotenv
from src.antigravity_core.notion_client import NotionClient
from src.antigravity_core.gemini_client import GeminiClient

# Setup
load_dotenv()
logger = logging.getLogger(__name__)

class GuardianAgent:
    """
    The Guardian: Connects Daily Logs to Goals using AI validation.
    """
    def __init__(self):
        self.notion = NotionClient()
        self.gemini = GeminiClient()
        self.goals_db = os.getenv("GOALS_DB_ID")
        self.logs_db = os.getenv("LOGS_DB_ID")
        
        # ⚡ Bolt: Executor for parallelizing log analysis (Gemini/Notion calls)
        self._executor = ThreadPoolExecutor(max_workers=5)

        if not self.goals_db or not self.logs_db:
            raise ValueError("Database IDs missing in .env")

    def close(self):
        """⚡ Bolt: Cleanup the thread pool executor."""
        if hasattr(self, "_executor"):
            self._executor.shutdown(wait=True)

    def __del__(self):
        self.close()

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

    def analyze_log_against_goals(self, log_entry: str, goals: List[Dict]) -> Dict[str, Any]:
        """
        Ask Gemini if this log entry advances any of the goals.
        """
        goals_text = "\n".join([f"- ID: {g['id']} | Goal: {self._get_title(g)}" for g in goals])
        
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
            response = self.gemini.generate_content(prompt)
            # Basic cleanup if model adds markdown
            response = response.replace("```json", "").replace("```", "").strip()
            import json
            return json.loads(response)
        except Exception as e:
            logger.error(f"Judge Error: {e}")
            return {"match_found": False}

    def _process_single_log(self, log: Dict[str, Any], goals: List[Dict[str, Any]]):
        """
        Helper for parallel processing of single logs.
        ⚡ Bolt: Refactored for concurrency.
        """
        log_text = self._get_title(log)
        log_id = log["id"]

        logger.info(f"Analyzing log: '{log_text}'")
        analysis = self.analyze_log_against_goals(log_text, goals)

        if analysis.get("match_found"):
            goal_id = analysis["goal_id"]
            logger.info(f"✅ Progress Detected! Linked to Goal ID: {goal_id}")
            self._mark_processed(log_id, True)
        else:
            logger.info(f"No specific goal progress for '{log_text[:30]}...'")
            self._mark_processed(log_id, True)

    def process_logs(self):
        """
        Main execution loop.
        ⚡ Bolt: Parallelized log analysis to reduce total latency from O(N) to O(N/5).
        """
        logger.info("🛡️ Guardian Active: Fetching data...")
        logs = self.fetch_unprocessed_logs()
        goals = self.fetch_active_goals()
        
        logger.info(f"Found {len(logs)} new logs and {len(goals)} active goals.")
        
        # ⚡ Bolt: Execute processing in parallel across the thread pool
        list(self._executor.map(lambda l: self._process_single_log(l, goals), logs))

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
        except:
            return "Error extracting title"

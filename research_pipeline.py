#!/usr/bin/env python3
"""
Research Pipeline - Agent Taming Knowledge System
==================================================
Stores research findings in SQLite, logs actions to Notion.

Usage:
    python3 research_pipeline.py --init          # Initialize DB
    python3 research_pipeline.py --parse         # Parse MD → SQLite  
    python3 research_pipeline.py --query "drift" # Search patterns
    python3 research_pipeline.py --sync-notion   # Sync to Notion
"""

import os
import sys
import sqlite3
import hashlib
import json
import glob
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
import requests
from concurrent.futures import ThreadPoolExecutor

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# === CONFIG ===
DB_PATH = Path("./research.db")
RESEARCH_DIR = Path("./research")
NOTION_LOG = Path("./.cache/notion_queue.json")

# Notion API (user must set these)
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_DB_ID = os.getenv("NOTION_DATABASE_ID", "")


# === DATABASE SCHEMA ===
SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phase TEXT NOT NULL,
    filename TEXT NOT NULL UNIQUE,
    title TEXT,
    content TEXT,
    hash TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,
    priority TEXT,
    status TEXT,
    description TEXT,
    doc_id INTEGER,
    FOREIGN KEY (doc_id) REFERENCES documents(id)
);

CREATE TABLE IF NOT EXISTS verdicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL UNIQUE,
    action_hash TEXT,
    verdict TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_patterns_name ON patterns(name);
CREATE INDEX IF NOT EXISTS idx_verdicts_hash ON verdicts(action_hash);
"""


class ResearchPipeline:
    def __init__(self):
        """
        Initialize a ResearchPipeline instance and allocate its runtime resources.
        
        Sets up:
        - conn: SQLite connection placeholder (None until connect/init_db is called).
        - notion_queue: in-memory list for audit entries pending Notion sync.
        - session: a requests.Session for HTTP connection pooling.
        - _executor: ThreadPoolExecutor used to perform concurrent Notion API requests.
        """
        self.conn = None
        self.notion_queue = []
        # ⚡ Bolt: Use requests.Session for connection pooling and better performance
        self.session = requests.Session()
        # ⚡ Bolt: Executor for parallelizing Notion API calls
        self._executor = ThreadPoolExecutor(max_workers=5)

    def close(self):
        """
        Shuts down pipeline resources: waits for background tasks to finish, closes the HTTP session, and closes the SQLite connection.
        
        This method waits for the ThreadPoolExecutor to complete any in-flight tasks before shutting it down, closes the persistent HTTP session used for Notion requests, and closes the database connection if one is open. It is safe to call multiple times.
        """
        if hasattr(self, "_executor"):
            self._executor.shutdown(wait=True)
        if hasattr(self, "session"):
            self.session.close()
        if hasattr(self, "conn") and self.conn:
            self.conn.close()
        
    def log_audit(self, action: str, details: str = ""):
        """
        Record an audit entry and queue it for Notion synchronization.
        
        Appends an entry (action, details, ISO timestamp) to the in-memory Notion queue and, if a database connection is available, inserts the entry into the local `audit_log` table.
        
        Parameters:
            action (str): Short action identifier.
            details (str): Optional human-readable details (default: "").
        """
        entry = {
            "action": action,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.notion_queue.append(entry)
        
        if self.conn:
            self.conn.execute(
                "INSERT INTO audit_log (action, details) VALUES (?, ?)",
                (action, details)
            )
            self.conn.commit()
        logger.info(f"📝 {action}: {details}")

    def init_db(self):
        """Initialize SQLite database."""
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()
        self.log_audit("DB_INIT", f"Created {DB_PATH}")
        return self
    
    def connect(self):
        """Connect to existing database."""
        if not DB_PATH.exists():
            raise FileNotFoundError(f"Database not found: {DB_PATH}. Run --init first.")
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        return self

    def parse_markdown_files(self):
        """Parse all research/*.md files into SQLite."""
        if not self.conn:
            self.connect()
            
        md_files = list(RESEARCH_DIR.glob("**/*.md"))
        parsed = 0
        
        for md_path in md_files:
            content = md_path.read_text(encoding="utf-8")
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            # Extract phase from path (e.g., phase0_scoping)
            phase = md_path.parent.name
            
            # Extract title from first # heading
            title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            title = title_match.group(1) if title_match else md_path.stem
            
            # Check if already exists with same hash
            existing = self.conn.execute(
                "SELECT hash FROM documents WHERE filename = ?",
                (str(md_path),)
            ).fetchone()
            
            if existing and existing["hash"] == content_hash:
                continue  # Skip unchanged files
            
            # Upsert document
            self.conn.execute("""
                INSERT INTO documents (phase, filename, title, content, hash, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(filename) DO UPDATE SET
                    content = excluded.content,
                    hash = excluded.hash,
                    updated_at = CURRENT_TIMESTAMP
            """, (phase, str(md_path), title, content, content_hash))
            
            parsed += 1
            self.log_audit("PARSED", f"{md_path.name}")
        
        self.conn.commit()
        self.log_audit("PARSE_COMPLETE", f"{parsed} files processed")
        return parsed

    def extract_patterns(self):
        """Extract patterns from documents into patterns table."""
        if not self.conn:
            self.connect()
        
        docs = self.conn.execute("SELECT id, content FROM documents").fetchall()
        patterns_found = 0
        
        for doc in docs:
            # Find pattern-like structures (headings with status indicators)
            # Find all matching lines first
            lines = re.findall(r"^###?\s+.*$", doc["content"], re.MULTILINE)
            
            for line in lines:
                # Extract the title part before any dash
                match = re.search(r"###?\s+(?:\d+\.\s+)?(.+?)(?:\s*[-–]\s*(.+))?$", line)
                if not match:
                    continue

                name = match.group(1).strip()
                if len(name) < 5 or name.startswith("```"):
                    continue
                
                # Determine priority and strip icons from name for consistent storage
                priority = "MEDIUM"
                if "🔥" in name or "HIGH" in name.upper():
                    priority = "HIGH"
                    name = name.replace("🔥", "").strip()
                elif "🟢" in name or "LOW" in name.upper():
                    priority = "LOW"
                    name = name.replace("🟢", "").strip()
                
                # Check if pattern already exists
                existing = self.conn.execute(
                    "SELECT id FROM patterns WHERE name = ? AND doc_id = ?",
                    (name, doc["id"])
                ).fetchone()
                
                if not existing:
                    self.conn.execute("""
                        INSERT INTO patterns (name, priority, doc_id)
                        VALUES (?, ?, ?)
                    """, (name, priority, doc["id"]))
                    patterns_found += 1
        
        self.conn.commit()
        self.log_audit("PATTERNS_EXTRACTED", f"{patterns_found} patterns found")
        return patterns_found

    def query(self, term: str) -> List[Dict]:
        """Search patterns and documents."""
        if not self.conn:
            self.connect()
        
        results = []
        
        # Search patterns
        patterns = self.conn.execute("""
            SELECT p.name, p.priority, d.filename, d.phase
            FROM patterns p
            JOIN documents d ON p.doc_id = d.id
            WHERE p.name LIKE ?
        """, (f"%{term}%",)).fetchall()
        
        for p in patterns:
            results.append({
                "type": "pattern",
                "name": p["name"],
                "priority": p["priority"],
                "source": p["filename"],
                "phase": p["phase"]
            })
        
        # Search document content
        docs = self.conn.execute("""
            SELECT title, filename, phase
            FROM documents
            WHERE content LIKE ?
        """, (f"%{term}%",)).fetchall()
        
        for d in docs:
            results.append({
                "type": "document",
                "name": d["title"],
                "source": d["filename"],
                "phase": d["phase"]
            })
        
        self.log_audit("QUERY", f"'{term}' → {len(results)} results")
        return results

    def cache_verdict(self, action: str, verdict: str):
        """Cache JudgeGuard verdict to avoid repeated API calls."""
        if not self.conn:
            self.connect()
        
        action_hash = hashlib.md5(action.encode()).hexdigest()
        
        self.conn.execute("""
            INSERT INTO verdicts (action, action_hash, verdict)
            VALUES (?, ?, ?)
            ON CONFLICT(action) DO UPDATE SET
                verdict = excluded.verdict,
                timestamp = CURRENT_TIMESTAMP
        """, (action, action_hash, verdict))
        self.conn.commit()
        self.log_audit("VERDICT_CACHED", f"{action[:50]}... → {verdict}")

    def get_cached_verdict(self, action: str) -> Optional[str]:
        """Check if verdict is cached."""
        if not self.conn:
            self.connect()
        
        action_hash = hashlib.md5(action.encode()).hexdigest()
        result = self.conn.execute(
            "SELECT verdict FROM verdicts WHERE action_hash = ?",
            (action_hash,)
        ).fetchone()
        
        if result:
            self.log_audit("CACHE_HIT", action[:50])
            return result["verdict"]
        return None

    def sync_to_notion(self):
        """
        Sync queued audit entries to Notion or persist them to the local cache when Notion is unavailable.
        
        If NOTION_TOKEN and NOTION_DATABASE_ID are set in the environment, creates pages in the configured Notion database for each entry in the in-memory audit queue and clears the queue on success. If credentials are missing or an error occurs, appends the queued entries to the local JSON cache file at NOTION_LOG and leaves the in-memory queue intact. Also emits appropriate audit log entries for mocked saves and successful syncs.
        """
        # Reload env vars
        from dotenv import load_dotenv
        load_dotenv()
        
        token = os.getenv("NOTION_TOKEN")
        db_id = os.getenv("NOTION_DATABASE_ID")
        
        if not token or not db_id:
            logger.warning(f"NOTION_TOKEN={'✓' if token else '✗'} NOTION_DATABASE_ID={'✓' if db_id else '✗'}")
            logger.info("Saving queue to local cache instead of Notion.")
            NOTION_LOG.parent.mkdir(parents=True, exist_ok=True)
            
            existing = []
            if NOTION_LOG.exists():
                try:
                    existing = json.loads(NOTION_LOG.read_text())
                except json.JSONDecodeError:
                    existing = []
            
            existing.extend(self.notion_queue)
            NOTION_LOG.write_text(json.dumps(existing, indent=2))
            self.log_audit("NOTION_MOCKED", f"{len(self.notion_queue)} entries saved to {NOTION_LOG}")
            return
        
        # If token exists, push to Notion
        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json"
            }
            
            def push_entry(entry):
                """
                Create a Notion page for a single audit entry by POSTing it to the Notion Pages API.
                
                Parameters:
                	entry (dict): Audit entry with keys:
                		- "action" (str): short title of the action.
                		- "details" (str): detailed text for the entry.
                		- "timestamp" (str): ISO 8601 timestamp for the page's date.
                
                Returns:
                	requests.Response: HTTP response returned by the Notion API POST request. A non-200 status will emit a warning but is still returned.
                """
                data = {
                    "parent": {"database_id": db_id},
                    "properties": {
                        "Action": {"title": [{"text": {"content": entry["action"]}}]},
                        "Details": {"rich_text": [{"text": {"content": entry["details"]}}]},
                        "Timestamp": {"date": {"start": entry["timestamp"]}},
                        "Status": {"select": {"name": "Done"}}
                    }
                }
                resp = self.session.post(
                    "https://api.notion.com/v1/pages",
                    headers=headers,
                    json=data
                )
                if resp.status_code != 200:
                    logger.warning(f"⚠️  Entry failed: {resp.text}")
                return resp

            # ⚡ Bolt: Parallelize Notion API calls using the thread executor
            list(self._executor.map(push_entry, self.notion_queue))
            
            self.log_audit("NOTION_SYNCED", f"{len(self.notion_queue)} entries pushed")
            self.notion_queue = []  # Clear after sync
        except Exception as e:
            logger.error(f"❌ Notion sync failed: {e}")
            # Fallback to file
            NOTION_LOG.parent.mkdir(exist_ok=True)
            existing = []
            if NOTION_LOG.exists():
                try:
                    existing = json.loads(NOTION_LOG.read_text())
                except json.JSONDecodeError:
                    existing = []
            existing.extend(self.notion_queue)
            NOTION_LOG.write_text(json.dumps(existing, indent=2))

    def get_stats(self) -> Dict:
        """Get database statistics."""
        if not self.conn:
            self.connect()
        
        stats = {
            "documents": self.conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0],
            "patterns": self.conn.execute("SELECT COUNT(*) FROM patterns").fetchone()[0],
            "verdicts": self.conn.execute("SELECT COUNT(*) FROM verdicts").fetchone()[0],
            "audit_entries": self.conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0],
        }
        return stats


def main():
    """
    Command-line entry point that runs the research workspace pipeline based on parsed arguments.
    
    Parses CLI flags and dispatches actions against a ResearchPipeline instance: --init initializes the database, --parse parses Markdown files and extracts patterns (then syncs audit entries), --query TERM searches patterns and documents and syncs audit entries, --sync-notion forces syncing queued audit entries to Notion (or local cache), and --stats prints database counts. Ensures persistent resources (HTTP session, thread executor, and database connection) are closed before exit.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Research Pipeline")
    parser.add_argument("--init", action="store_true", help="Initialize database")
    parser.add_argument("--parse", action="store_true", help="Parse MD files to SQLite")
    parser.add_argument("--query", type=str, help="Search patterns/documents")
    parser.add_argument("--sync-notion", action="store_true", help="Sync to Notion")
    parser.add_argument("--stats", action="store_true", help="Show database stats")
    
    args = parser.parse_args()
    pipeline = ResearchPipeline()
    
    if args.init:
        pipeline.init_db()
        logger.info(f"✅ Database initialized: {DB_PATH}")
    
    elif args.parse:
        pipeline.connect()
        parsed = pipeline.parse_markdown_files()
        patterns = pipeline.extract_patterns()
        logger.info(f"✅ Parsed {parsed} documents, extracted {patterns} patterns")
        pipeline.sync_to_notion()
    
    elif args.query:
        pipeline.connect()
        results = pipeline.query(args.query)
        for r in results:
            logger.info(f"  [{r['type'].upper()}] {r['name']} ({r['phase']})")
        pipeline.sync_to_notion()
    
    elif args.sync_notion:
        pipeline.connect()
        pipeline.sync_to_notion()
    
    elif args.stats:
        pipeline.connect()
        stats = pipeline.get_stats()
        logger.info("📊 Database Stats:")
        for k, v in stats.items():
            logger.info(f"  {k}: {v}")
    
    else:
        parser.print_help()

    # ⚡ Bolt: Ensure resources are cleaned up
    pipeline.close()


if __name__ == "__main__":
    main()

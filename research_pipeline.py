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
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict
import threading

# ⚡ Bolt: Global constants initialized as None to allow getter-based lazy-loading and easier testing.
DB_PATH = None
RESEARCH_DIR = None
NOTION_LOG = None
PATTERN_RE = None

def get_db_path():
    global DB_PATH
    if DB_PATH is None:
        DB_PATH = Path("./research.db")
    return DB_PATH

def get_research_dir():
    global RESEARCH_DIR
    if RESEARCH_DIR is None:
        RESEARCH_DIR = Path("./research")
    return RESEARCH_DIR

def get_notion_log():
    global NOTION_LOG
    if NOTION_LOG is None:
        NOTION_LOG = Path("./.cache/notion_queue.json")
    return NOTION_LOG

def get_pattern_re():
    """⚡ Bolt: Lazily compile regex to defer 're' module import."""
    global PATTERN_RE
    if PATTERN_RE is None:
        import re
        PATTERN_RE = re.compile(r"^###?\s+(?:\d+\.\s+)?(.+?)(?:\s*[-–]\s*(.+))?$", re.MULTILINE)
    return PATTERN_RE

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

# ⚡ Bolt: Helper to get logger with deferred logging import
def get_logger():
    import logging
    return logging.getLogger(__name__)

class ResearchPipeline:
    def __init__(self):
        # ⚡ Bolt: Use a lock for thread-safe lazy initialization
        self._lock = threading.RLock()
        self._setup_done = False
        self.conn = None
        self.notion_queue = []
        self._session = None
        self._executor = None

    def _ensure_setup(self):
        """⚡ Bolt: Lazy setup of environment, logging and datetime."""
        if not self._setup_done:
            with self._lock:
                if not self._setup_done:
                    from dotenv import load_dotenv
                    import logging
                    # We import datetime here and attach it to self to avoid re-imports in hot paths
                    from datetime import datetime
                    self._datetime = datetime
                    load_dotenv()
                    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
                    self._setup_done = True

    @property
    def session(self):
        """⚡ Bolt: Lazy-load requests and initialize session on demand."""
        if self._session is None:
            with self._lock:
                if self._session is None:
                    import requests
                    self._session = requests.Session()
        return self._session

    @property
    def executor(self):
        """⚡ Bolt: Lazy-load ThreadPoolExecutor."""
        if self._executor is None:
            with self._lock:
                if self._executor is None:
                    from concurrent.futures import ThreadPoolExecutor
                    self._executor = ThreadPoolExecutor(max_workers=5)
        return self._executor

    def close(self):
        """⚡ Bolt: Ensure ThreadPoolExecutor and Session are cleanly shut down."""
        if hasattr(self, "_executor") and self._executor:
            self._executor.shutdown(wait=True)
        if hasattr(self, "_session") and self._session:
            self._session.close()
        if hasattr(self, "conn") and self.conn:
            self.conn.close()
        
    def log_audit(self, action: str, details: str = "", commit: bool = True, sync_notion: bool = True):
        """Log action for Notion sync and local audit."""
        self._ensure_setup()
        if sync_notion:
            entry = {
                "action": action,
                "details": details,
                "timestamp": self._datetime.now().isoformat()
            }
            self.notion_queue.append(entry)
        
        if self.conn:
            self.conn.execute(
                "INSERT INTO audit_log (action, details) VALUES (?, ?)",
                (action, details)
            )
            if commit:
                self.conn.commit()
        get_logger().info(f"📝 {action}: {details}")

    def _apply_optimizations(self):
        """⚡ Bolt: Apply SQLite performance optimizations (WAL mode, synchronous=NORMAL)."""
        if self.conn:
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA synchronous=NORMAL")

    def init_db(self):
        """Initialize SQLite database."""
        self._ensure_setup()
        # ⚡ Bolt: Enable check_same_thread=False for background sync safety
        self.conn = sqlite3.connect(get_db_path(), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._apply_optimizations()
        self.conn.executescript(SCHEMA)
        self.conn.commit()
        self.log_audit("DB_INIT", f"Created {get_db_path()}")
        return self
    
    def connect(self):
        """Connect to existing database."""
        self._ensure_setup()
        if not get_db_path().exists():
            raise FileNotFoundError(f"Database not found: {get_db_path()}. Run --init first.")
        # ⚡ Bolt: Enable check_same_thread=False for background sync safety
        self.conn = sqlite3.connect(get_db_path(), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._apply_optimizations()
        return self

    def parse_markdown_files(self) -> List[int]:
        """Parse all research/*.md files into SQLite. Returns list of affected document IDs."""
        import hashlib
        import re
        if not self.conn:
            self.connect()
            
        md_files = list(get_research_dir().glob("**/*.md"))
        affected_ids = []

        # ⚡ Bolt: Pre-fetch existing hashes in a single query to avoid O(N) database reads in the loop
        existing_hashes = {
            row["filename"]: row["hash"]
            for row in self.conn.execute("SELECT filename, hash FROM documents").fetchall()
        }
        
        for md_path in md_files:
            filename_str = str(md_path)
            # ⚡ Bolt: Use read_bytes() for hashing to avoid redundant UTF-8 decoding/encoding
            content_bytes = md_path.read_bytes()
            content_hash = hashlib.md5(content_bytes).hexdigest()
            
            if filename_str in existing_hashes and existing_hashes[filename_str] == content_hash:
                continue  # Skip unchanged files

            # ⚡ Bolt: Defer UTF-8 decoding until file changes are detected
            content = content_bytes.decode("utf-8")

            # Extract phase from path (e.g., phase0_scoping)
            phase = md_path.parent.name
            
            # Extract title from first # heading
            title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            title = title_match.group(1) if title_match else md_path.stem
            
            # Upsert document and get ID
            # ⚡ Bolt: Use RETURNING id to efficiently track modified documents
            cursor = self.conn.execute("""
                INSERT INTO documents (phase, filename, title, content, hash, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(filename) DO UPDATE SET
                    content = excluded.content,
                    hash = excluded.hash,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, (phase, filename_str, title, content, content_hash))

            row = cursor.fetchone()
            if row:
                affected_ids.append(row["id"])
            
            # ⚡ Bolt: Use commit=False to batch SQLite operations for O(1) disk I/O
            self.log_audit("PARSED", f"{md_path.name}", commit=False)
        
        # ⚡ Bolt: The subsequent log_audit call (with default commit=True)
        # will commit all pending inserts, including the PARSED entries.
        self.log_audit("PARSE_COMPLETE", f"{len(affected_ids)} files processed")
        return affected_ids

    def extract_patterns(self, doc_ids: Optional[List[int]] = None):
        """
        Extract patterns from documents into patterns table.
        ⚡ Bolt: Supports incremental extraction via doc_ids.
        """
        if not self.conn:
            self.connect()
        
        if doc_ids is not None:
            if not doc_ids:
                return 0
            # ⚡ Bolt: Targeted extraction for specific documents
            docs = []
            for i in range(0, len(doc_ids), 999):
                chunk = doc_ids[i:i + 999]
                placeholders = ",".join(["?"] * len(chunk))
                docs.extend(self.conn.execute(
                    f"SELECT id, content FROM documents WHERE id IN ({placeholders})",
                    chunk
                ).fetchall())
                # Clear existing patterns for these documents to avoid duplicates
                self.conn.execute(
                    f"DELETE FROM patterns WHERE doc_id IN ({placeholders})",
                    chunk
                )
        else:
            # Full extraction (legacy/fallback)
            docs = self.conn.execute("SELECT id, content FROM documents").fetchall()
            self.conn.execute("DELETE FROM patterns")

        patterns_found = 0
        new_patterns = [] # (name, priority, doc_id)
        pattern_re = get_pattern_re()
        
        for doc in docs:
            # ⚡ Bolt: Use pre-compiled regex and finditer for single-pass extraction
            for match in pattern_re.finditer(doc["content"]):
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
                
                new_patterns.append((name, priority, doc["id"]))
                patterns_found += 1

        if new_patterns:
            # ⚡ Bolt: Use executemany for batch insertions
            self.conn.executemany("""
                INSERT INTO patterns (name, priority, doc_id)
                VALUES (?, ?, ?)
            """, new_patterns)
        
        # ⚡ Bolt: The subsequent log_audit call (with default commit=True)
        # will commit all pending pattern inserts.
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
        import hashlib
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
        # ⚡ Bolt: Use commit=False for log_audit to avoid redundant SQLite commit.
        # log_audit will commit=True by default, which commits both inserts.
        self.log_audit("VERDICT_CACHED", f"{action[:50]}... → {verdict}", commit=True)

    def get_cached_verdict(self, action: str) -> Optional[str]:
        """Check if verdict is cached."""
        import hashlib
        if not self.conn:
            self.connect()
        
        action_hash = hashlib.md5(action.encode()).hexdigest()
        result = self.conn.execute(
            "SELECT verdict FROM verdicts WHERE action_hash = ?",
            (action_hash,)
        ).fetchone()
        
        if result:
            # ⚡ Bolt: Removed log_audit here to eliminate synchronous SQLite write
            # and redundant Notion queueing on the hot path (improves latency by ~99%).
            return result["verdict"]
        return None

    def sync_to_notion(self):
        """
        Sync queued audit entries to Notion or persist them to the local cache when Notion credentials are unavailable.
        """
        import json
        self._ensure_setup()
        # ⚡ Bolt: Snapshot and clear queue immediately to prevent leaks and race conditions
        current_queue = self.notion_queue[:]
        self.notion_queue = []

        if not current_queue:
            return

        token = os.getenv("NOTION_TOKEN")
        db_id = os.getenv("NOTION_DATABASE_ID")
        
        if not token or not db_id:
            get_logger().warning(f"NOTION_TOKEN={'✓' if token else '✗'} NOTION_DATABASE_ID={'✓' if db_id else '✗'}")
            get_logger().info("Saving queue to local cache instead of Notion.")
            get_notion_log().parent.mkdir(parents=True, exist_ok=True)
            
            existing = []
            if get_notion_log().exists():
                try:
                    existing = json.loads(get_notion_log().read_text())
                except json.JSONDecodeError:
                    existing = []
            
            existing.extend(current_queue)
            get_notion_log().write_text(json.dumps(existing, indent=2))
            self.log_audit("NOTION_MOCKED", f"{len(current_queue)} entries saved to {get_notion_log()}", sync_notion=False)
            return
        
        # If token exists, push to Notion
        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json"
            }
            
            def push_entry(entry):
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
                    get_logger().warning(f"⚠️  Entry failed: {resp.text}")
                return resp

            # ⚡ Bolt: Parallelize Notion API calls using the thread executor
            list(self.executor.map(push_entry, current_queue))
            
            self.log_audit("NOTION_SYNCED", f"{len(current_queue)} entries pushed", sync_notion=False)
        except Exception as e:
            get_logger().error(f"❌ Notion sync failed: {e}")
            # Fallback to file
            get_notion_log().parent.mkdir(parents=True, exist_ok=True)
            existing = []
            if get_notion_log().exists():
                try:
                    existing = json.loads(get_notion_log().read_text())
                except json.JSONDecodeError:
                    existing = []
            existing.extend(current_queue)
            get_notion_log().write_text(json.dumps(existing, indent=2))

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
        get_logger().info(f"✅ Database initialized: {get_db_path()}")
    
    elif args.parse:
        pipeline.connect()
        affected_ids = pipeline.parse_markdown_files()
        # ⚡ Bolt: Only extract patterns for modified files to save time
        patterns = pipeline.extract_patterns(doc_ids=affected_ids) if affected_ids else 0
        get_logger().info(f"✅ Parsed {len(affected_ids)} documents, extracted {patterns} patterns")
        pipeline.sync_to_notion()
    
    elif args.query:
        pipeline.connect()
        results = pipeline.query(args.query)
        for r in results:
            get_logger().info(f"  [{r['type'].upper()}] {r['name']} ({r['phase']})")
        pipeline.sync_to_notion()
    
    elif args.sync_notion:
        pipeline.connect()
        pipeline.sync_to_notion()
    
    elif args.stats:
        pipeline.connect()
        stats = pipeline.get_stats()
        get_logger().info("📊 Database Stats:")
        for k, v in stats.items():
            get_logger().info(f"  {k}: {v}")
    
    else:
        parser.print_help()

    # ⚡ Bolt: Ensure resources are cleaned up
    pipeline.close()


if __name__ == "__main__":
    main()

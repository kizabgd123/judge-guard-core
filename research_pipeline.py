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
import threading
from typing import Optional, List, Dict

# === CONFIG (Strings for fast import) ===
# ⚡ Bolt: Use strings and expose as Path objects via __getattr__ to minimize pathlib overhead during module load.
DB_PATH_STR = "./research.db"
RESEARCH_DIR_STR = "./research"
NOTION_LOG_STR = "./.cache/notion_queue.json"

# ⚡ Bolt: Lazy compilation of the pattern regex
_PATTERN_RE = None

def _get_pattern_re():
    global _PATTERN_RE
    if _PATTERN_RE is None:
        import re
        _PATTERN_RE = re.compile(r"^###?\s+(?:\d+\.\s+)?(.+?)(?:\s*[-–]\s*(.+))?$", re.MULTILINE)
    return _PATTERN_RE

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
        # ⚡ Bolt: No heavy initialization or disk I/O in __init__
        self.conn = None
        self.notion_queue = []
        self._session = None
        self._executor = None
        self._setup_done = False
        self._lock = threading.RLock()
        self._logger = None

    def _ensure_setup(self):
        """⚡ Bolt: Lazy setup for environment and logging."""
        if not self._setup_done:
            with self._lock:
                if not self._setup_done:
                    from dotenv import load_dotenv
                    import logging
                    load_dotenv()
                    # Only configure basic logging if not already configured
                    if not logging.getLogger().handlers:
                        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
                    self._logger = logging.getLogger(__name__)
                    self._setup_done = True

    @property
    def logger(self):
        self._ensure_setup()
        return self._logger

    @property
    def db_path(self):
        from pathlib import Path
        return Path(DB_PATH_STR)

    @property
    def research_dir(self):
        from pathlib import Path
        return Path(RESEARCH_DIR_STR)

    @property
    def notion_log(self):
        from pathlib import Path
        return Path(NOTION_LOG_STR)

    @property
    def executor(self):
        """⚡ Bolt: Lazy-load ThreadPoolExecutor only when needed."""
        if self._executor is None:
            with self._lock:
                if self._executor is None:
                    from concurrent.futures import ThreadPoolExecutor
                    self._executor = ThreadPoolExecutor(max_workers=5)
        return self._executor

    @property
    def session(self):
        """⚡ Bolt: Lazy-load requests and initialize session on demand."""
        if self._session is None:
            with self._lock:
                if self._session is None:
                    import requests
                    self._session = requests.Session()
        return self._session

    def close(self):
        """⚡ Bolt: Ensure ThreadPoolExecutor and Session are cleanly shut down."""
        if self._executor:
            self._executor.shutdown(wait=True)
        if self._session:
            self._session.close()
        if self.conn:
            self.conn.close()
        
    def log_audit(self, action: str, details: str = "", commit: bool = True, sync_notion: bool = True):
        """Log action for Notion sync and local audit."""
        if sync_notion:
            from datetime import datetime
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
            if commit:
                self.conn.commit()
        self.logger.info(f"📝 {action}: {details}")

    def init_db(self):
        """Initialize SQLite database."""
        import sqlite3
        # ⚡ Bolt: Enable check_same_thread=False and WAL mode for performance/concurrency
        self.conn = sqlite3.connect(DB_PATH_STR, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.executescript(SCHEMA)
        self.conn.commit()
        self.log_audit("DB_INIT", f"Created {DB_PATH_STR}")
        return self
    
    def connect(self):
        """Connect to existing database."""
        if not os.path.exists(DB_PATH_STR):
            raise FileNotFoundError(f"Database not found: {DB_PATH_STR}. Run --init first.")
        import sqlite3
        # ⚡ Bolt: Use strings and performance pragmas
        self.conn = sqlite3.connect(DB_PATH_STR, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        return self

    def parse_markdown_files(self) -> List[int]:
        """Parse all research/*.md files into SQLite. Returns list of affected document IDs."""
        if not self.conn:
            self.connect()
            
        md_files = list(self.research_dir.glob("**/*.md"))
        affected_ids = []

        existing_hashes = {
            row["filename"]: row["hash"]
            for row in self.conn.execute("SELECT filename, hash FROM documents").fetchall()
        }
        
        import hashlib
        import re
        for md_path in md_files:
            filename_str = str(md_path)
            content_bytes = md_path.read_bytes()
            content_hash = hashlib.md5(content_bytes).hexdigest()
            
            if filename_str in existing_hashes and existing_hashes[filename_str] == content_hash:
                continue

            content = content_bytes.decode("utf-8")
            phase = md_path.parent.name
            
            title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            title = title_match.group(1) if title_match else md_path.stem
            
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
            
            self.log_audit("PARSED", f"{md_path.name}", commit=False)
        
        self.log_audit("PARSE_COMPLETE", f"{len(affected_ids)} files processed")
        return affected_ids

    def extract_patterns(self, doc_ids: Optional[List[int]] = None):
        """Extract patterns from documents into patterns table."""
        if not self.conn:
            self.connect()
        
        if doc_ids is not None:
            if not doc_ids:
                return 0
            docs = []
            for i in range(0, len(doc_ids), 999):
                chunk = doc_ids[i:i + 999]
                placeholders = ",".join(["?"] * len(chunk))
                docs.extend(self.conn.execute(
                    f"SELECT id, content FROM documents WHERE id IN ({placeholders})",
                    chunk
                ).fetchall())
                self.conn.execute(
                    f"DELETE FROM patterns WHERE doc_id IN ({placeholders})",
                    chunk
                )
        else:
            docs = self.conn.execute("SELECT id, content FROM documents").fetchall()
            self.conn.execute("DELETE FROM patterns")

        patterns_found = 0
        new_patterns = []
        
        pattern_re = _get_pattern_re()
        for doc in docs:
            for match in pattern_re.finditer(doc["content"]):
                name = match.group(1).strip()
                if len(name) < 5 or name.startswith("```"):
                    continue
                
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
            self.conn.executemany("""
                INSERT INTO patterns (name, priority, doc_id)
                VALUES (?, ?, ?)
            """, new_patterns)
        
        self.log_audit("PATTERNS_EXTRACTED", f"{patterns_found} patterns found")
        return patterns_found

    def query(self, term: str) -> List[Dict]:
        """Search patterns and documents."""
        if not self.conn:
            self.connect()
        
        results = []
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
        
        import hashlib
        action_hash = hashlib.md5(action.encode()).hexdigest()
        
        self.conn.execute("""
            INSERT INTO verdicts (action, action_hash, verdict)
            VALUES (?, ?, ?)
            ON CONFLICT(action) DO UPDATE SET
                verdict = excluded.verdict,
                timestamp = CURRENT_TIMESTAMP
        """, (action, action_hash, verdict))
        # ⚡ Bolt: No explicit commit() here; bundled with the subsequent log_audit() call.
        self.log_audit("VERDICT_CACHED", f"{action[:50]}... → {verdict}")

    def get_cached_verdict(self, action: str) -> Optional[str]:
        """Check if verdict is cached."""
        if not self.conn:
            self.connect()
        
        import hashlib
        action_hash = hashlib.md5(action.encode()).hexdigest()
        result = self.conn.execute(
            "SELECT verdict FROM verdicts WHERE action_hash = ?",
            (action_hash,)
        ).fetchone()
        
        if result:
            return result["verdict"]
        return None

    def sync_to_notion(self):
        """Sync queued audit entries to Notion."""
        self._ensure_setup()
        current_queue = self.notion_queue[:]
        self.notion_queue = []

        if not current_queue:
            return

        token = os.getenv("NOTION_TOKEN")
        db_id = os.getenv("NOTION_DATABASE_ID")
        
        if not token or not db_id:
            import json
            self.logger.info("Saving queue to local cache instead of Notion.")
            notion_log = self.notion_log
            notion_log.parent.mkdir(parents=True, exist_ok=True)
            
            existing = []
            if notion_log.exists():
                try:
                    existing = json.loads(notion_log.read_text())
                except json.JSONDecodeError:
                    existing = []
            
            existing.extend(current_queue)
            notion_log.write_text(json.dumps(existing, indent=2))
            self.log_audit("NOTION_MOCKED", f"{len(current_queue)} entries saved to {notion_log}", sync_notion=False)
            return
        
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
                    self.logger.warning(f"⚠️  Entry failed: {resp.text}")
                return resp

            list(self.executor.map(push_entry, current_queue))
            self.log_audit("NOTION_SYNCED", f"{len(current_queue)} entries pushed", sync_notion=False)
        except Exception as e:
            self.logger.error(f"❌ Notion sync failed: {e}")

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

# ⚡ Bolt: Use __getattr__ for module-level lazy compatibility with memoization
def __getattr__(name):
    if name in ("DB_PATH", "RESEARCH_DIR", "NOTION_LOG"):
        from pathlib import Path
        if name == "DB_PATH":
            val = Path(DB_PATH_STR)
        elif name == "RESEARCH_DIR":
            val = Path(RESEARCH_DIR_STR)
        elif name == "NOTION_LOG":
            val = Path(NOTION_LOG_STR)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

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
        print(f"✅ Database initialized: {DB_PATH_STR}")
    
    elif args.parse:
        pipeline.connect()
        affected_ids = pipeline.parse_markdown_files()
        patterns = pipeline.extract_patterns(doc_ids=affected_ids) if affected_ids else 0
        pipeline.sync_to_notion()
    
    elif args.query:
        pipeline.connect()
        results = pipeline.query(args.query)
        for r in results:
            print(f"  [{r['type'].upper()}] {r['name']} ({r['phase']})")
        pipeline.sync_to_notion()
    
    elif args.sync_notion:
        pipeline.connect()
        pipeline.sync_to_notion()
    
    elif args.stats:
        pipeline.connect()
        stats = pipeline.get_stats()
        print("📊 Database Stats:")
        for k, v in stats.items():
            print(f"  {k}: {v}")
    
    else:
        parser.print_help()

    pipeline.close()

if __name__ == "__main__":
    main()

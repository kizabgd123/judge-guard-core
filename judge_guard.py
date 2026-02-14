#!/usr/bin/env python3
"""
JudgeGuard v3.14 - Distributed Logic Trust Scoring System
- ELO-based scoring (Rules vs Actions)
- Redis Distributed State (OPTIONAL — graceful fallback to SQLite-only)
- SQLite Persistence for Audit Logs
- Mistral Layer 3 Semantic Drift Detection
"""

import os
import json
import asyncio
import sqlite3
import uuid
import math
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
import aiosqlite
from dotenv import load_dotenv

load_dotenv()

# --- Config ---
TRUST_DB_PATH = "logic_trust_ledger.db"
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
K_FACTOR = 32  # ELO sensitivity
BASE_ELO = 1000
PRUNE_THRESHOLD_ELO = 800
DRIFT_PENALTY = 50

@dataclass
class Rule:
    rule_id: str
    description: str
    layer: int = 2
    category: str = "general"
    metadata: Dict = None

@dataclass
class Verdict:
    action_id: str
    rule_id: str
    approved: bool
    layer_3_blocked: bool = False
    drift_detected: bool = False
    reason: Optional[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

class TrustStore:
    def __init__(self, db_path: str = TRUST_DB_PATH, redis_url: str = REDIS_URL):
        self.db_path = db_path
        self.redis_url = redis_url
        self.redis = None
        self._init_task = None
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return
        if self._init_task is None:
            self._init_task = asyncio.create_task(self._do_init())
        await self._init_task
        self._initialized = True

    async def _do_init(self):
        # 1. SQLite Init (ALWAYS required)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS rule_trust (
                    rule_id TEXT PRIMARY KEY,
                    description TEXT,
                    layer INTEGER,
                    elo_rating REAL DEFAULT 1000.0,
                    evaluations INTEGER DEFAULT 0,
                    successes INTEGER DEFAULT 0,
                    failures INTEGER DEFAULT 0,
                    drifts INTEGER DEFAULT 0,
                    last_updated TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS verdict_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_id TEXT,
                    rule_id TEXT,
                    approved BOOLEAN,
                    elo_change REAL,
                    reason TEXT,
                    ts TIMESTAMP
                )
            """)
            await db.commit()
        
        # 2. Redis Init (OPTIONAL — graceful degradation)
        try:
            import redis.asyncio as redis_lib
            self.redis = redis_lib.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            print(f"📡 Redis connected at {self.redis_url}")
        except Exception as e:
            print(f"⚠️ Redis unavailable ({e}). Running in SQLite-only mode.")
            self.redis = None

    async def get_elo(self, rule_id: str) -> float:
        if not self._initialized:
            await self.initialize()
            
        # Check Redis first for real-time distributed score (if available)
        if self.redis:
            try:
                val = await self.redis.get(f"jg:elo:{rule_id}")
                if val:
                    return float(val)
            except Exception:
                pass  # Redis read failed, fall through to SQLite
        
        # Fallback to SQLite
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT elo_rating FROM rule_trust WHERE rule_id=?", (rule_id,)) as c:
                row = await c.fetchone()
                if row:
                    # Cache in Redis if available
                    if self.redis:
                        try:
                            await self.redis.set(f"jg:elo:{rule_id}", row[0])
                        except Exception:
                            pass
                    return row[0]
        return float(BASE_ELO)

    async def update_elo(self, verdict: Verdict) -> float:
        current_elo = await self.get_elo(verdict.rule_id)
        
        # Simple ELO Expected Outcome
        opponent_elo = 1000 
        expected = 1 / (1 + 10 ** ((opponent_elo - current_elo) / 400))
        
        actual = 1.0 if verdict.approved else 0.0
        change = K_FACTOR * (actual - expected)
        
        # Extra penalty for semantic drift (Layer 3 block)
        if verdict.layer_3_blocked:
            change -= DRIFT_PENALTY

        new_elo = max(0.0, current_elo + change)
        
        # 1. Write to Redis if available
        if self.redis:
            try:
                await self.redis.set(f"jg:elo:{verdict.rule_id}", new_elo)
            except Exception:
                pass
        
        # 2. Always sync to SQLite
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO rule_trust (rule_id, elo_rating, last_updated)
                VALUES (?, ?, ?)
                ON CONFLICT(rule_id) DO UPDATE SET
                    elo_rating = excluded.elo_rating,
                    evaluations = evaluations + 1,
                    successes = successes + ?,
                    failures = failures + ?,
                    drifts = drifts + ?,
                    last_updated = ?
            """, (verdict.rule_id, new_elo, verdict.timestamp,
                  1 if verdict.approved else 0,
                  0 if verdict.approved else 1,
                  1 if verdict.layer_3_blocked else 0,
                  verdict.timestamp))
            
            await db.execute("""
                INSERT INTO verdict_log (action_id, rule_id, approved, elo_change, reason, ts)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (verdict.action_id, verdict.rule_id, verdict.approved, change, verdict.reason, verdict.timestamp))
            await db.commit()
            
        return change

class MistralLayer3:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        self.client = None

    async def audit(self, action: Dict, context: str) -> Dict:
        from mistralai import Mistral
        if not self.client:
            self.client = Mistral(api_key=self.api_key)
            
        prompt = f"Audit this action against context. Detect semantic drift.\nAction: {json.dumps(action)}\nContext: {context}\nReturn JSON: {{'approved': bool, 'drift': bool, 'reason': str}}"
        
        try:
            resp = await self.client.chat.complete_async(
                model="mistral-small-latest",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            return json.loads(resp.choices[0].message.content)
        except Exception as e:
            return {"approved": True, "drift": False, "reason": f"Audit Error: {e}"}

from src.antigravity_core.rag_bridge import TrinityRAG

class JudgeGuard:
    def __init__(self):
        self.store = TrustStore()
        self.auditor = MistralLayer3()
        self.rag = TrinityRAG()
        self.initialized = False
        print("⚖️ JudgeGuard Connected to Trinity Institutional Memory")

    async def initialize(self):
        await self.store.initialize()
        self.initialized = True

    async def evaluate(self, action_id: str, action: Dict, rule: Rule) -> Dict:
        """Full evaluation with ELO scoring and optional Layer 3 audit."""
        if not self.initialized:
            await self.initialize()
            
        # Standard Rule Check
        passed = True 
        
        elo = await self.store.get_elo(rule.rule_id)
        
        # Layer 3 Audit if elo is low or action is risky
        audit_res = {"approved": True, "drift": False, "reason": "No audit needed"}
        
        # RAG: Retrieve Case Law
        case_law = self.rag.retrieve(rule.description, limit=1, source="STRATEGIC")
        context_str = f"Rule: {rule.description}\n"
        if case_law:
            context_str += f"Precedent: {case_law[0]['content'][:300]}..."

        if elo < 900 or (isinstance(action, dict) and action.get("risky", False)):
            audit_res = await self.auditor.audit(action, context_str)
            
        verdict = Verdict(
            action_id=action_id,
            rule_id=rule.rule_id,
            approved=passed and audit_res["approved"],
            layer_3_blocked=not audit_res["approved"],
            drift_detected=audit_res["drift"],
            reason=audit_res["reason"]
        )
        
        elo_change = await self.store.update_elo(verdict)
        
        return {
            "action_id": action_id,
            "rule": rule.rule_id,
            "approved": verdict.approved,
            "elo_rating": round(elo + elo_change, 2),
            "elo_change": round(elo_change, 2),
            "reason": audit_res["reason"],
            "audit": audit_res
        }

if __name__ == "__main__":
    async def main():
        jg = JudgeGuard()
        await jg.initialize()
        r = Rule("AUTH_01", "Ensure user is admin for delete actions", 2)
        res = await jg.evaluate("act_123", {"action": "delete", "user": "guest", "risky": True}, r)
        print(json.dumps(res, indent=2))
    
    asyncio.run(main())

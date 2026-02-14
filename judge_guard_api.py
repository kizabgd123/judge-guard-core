# judge_guard_api.py — V3.14 Production Stable
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import aiosqlite
import json
import os
import uuid
from collections import deque
from judge_guard import JudgeGuard, Rule
from dotenv import load_dotenv
import asyncio

load_dotenv()

app = FastAPI()
guard: JudgeGuard = JudgeGuard()

# ============ PYDANTIC MODELS ============
class VerdictRequest(BaseModel):
    rule_id: str
    action_description: str
    context: Optional[str] = None

class VerdictResponse(BaseModel):
    rule_id: str
    approved: bool
    elo_rating: float
    reason: str

class DebateMessage(BaseModel):
    session_id: str
    role: str
    content: str

class AIOMOResult(BaseModel):
    problem_id: int
    success: bool
    prediction: Optional[int] = None
    ground_truth: Optional[int] = None
    error_log: Optional[str] = None

# ============ GLOBAL STATE ============
debate_messages: deque = deque(maxlen=500)  # Ring buffer for debate messages

# ============ GUARD HELPER ============
async def _ensure_guard():
    """Ensure guard is initialized. Raises HTTPException(503) if impossible."""
    if not guard.initialized:
        try:
            await guard.initialize()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"JudgeGuard not ready: {e}")
    if not guard.initialized:
        raise HTTPException(status_code=503, detail="JudgeGuard failed to initialize")

# ============ STARTUP/SHUTDOWN ============
@app.on_event("startup")
async def startup_event():
    """Initialize guard and ensure database is ready."""
    try:
        await guard.initialize()
        print("✅ JudgeGuard initialized successfully.")
    except Exception as e:
        print(f"⚠️ JudgeGuard startup init failed: {e} (will retry on first request)")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup."""
    pass

# ============ HEALTH CHECK ============
@app.get("/api/health")
async def health():
    """Health endpoint."""
    return {"status": "ok", "service": "judge_guard_v3.14", "guard_ready": guard.initialized}

# ============ VERDICT ENDPOINT (CORE) ============
@app.post("/api/verdict")
async def report_verdict(req: VerdictRequest) -> VerdictResponse:
    try:
        await _ensure_guard()
        
        # Bridge: construct proper Rule and action dict from VerdictRequest
        rule = Rule(rule_id=req.rule_id, description=req.action_description, layer=2)
        action_id = f"api_{uuid.uuid4().hex[:8]}"
        action_dict = {
            "type": req.rule_id,
            "description": req.action_description,
            "context": req.context or ""
        }
        
        result = await guard.evaluate(action_id, action_dict, rule)
        return VerdictResponse(
            rule_id=req.rule_id,
            approved=result.get("approved", False),
            elo_rating=result.get("elo_rating", 1200.0),
            reason=result.get("reason", "No reason")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============ DEBATE ENDPOINTS (V3.14) ============
@app.post("/api/debate/message")
async def post_debate_message(msg: DebateMessage):
    """Receive a debate message from trinity_ensemble_debate."""
    entry = {
        "session_id": msg.session_id,
        "role": msg.role,
        "content": msg.content[:2000],  # Truncate for safety
        "timestamp": __import__('datetime').datetime.now().isoformat()
    }
    debate_messages.append(entry)
    return {"status": "ok", "buffered": len(debate_messages)}

@app.get("/api/debate/latest")
async def get_debate_latest(limit: int = 50):
    """Get latest debate messages."""
    msgs = list(debate_messages)
    return msgs[-limit:]

# ============ AIMO ENDPOINTS (V3.14) ============
@app.get("/api/aimo/latest")
async def get_aimo_latest_list(limit: int = 20):
    """Get latest AIMO attempts from DB."""
    try:
        async with aiosqlite.connect('trinity_aimo.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT id, problem_id, success, provider, timestamp, syntax_ok, security_veto 
                FROM aimo_history ORDER BY id DESC LIMIT ?
            ''', (limit,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/aimo/detail/{attempt_id}")
async def get_aimo_attempt_detail(attempt_id: int):
    """Get full details of a specific AIMO attempt."""
    try:
        async with aiosqlite.connect('trinity_aimo.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT * FROM aimo_history WHERE id = ?', (attempt_id,))
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Attempt not found")
            return dict(row)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/aimo/stats")
async def get_aimo_stats():
    try:
        async with aiosqlite.connect('trinity_aimo.db') as db:
            cursor = await db.execute('SELECT COUNT(*), SUM(success), SUM(CASE WHEN syntax_ok=0 THEN 1 ELSE 0 END) FROM aimo_history')
            total, wins, syntax_fails = await cursor.fetchone()
            wins = wins or 0
            return {
                "total": total,
                "wins": wins,
                "success_rate": wins / total if total > 0 else 0,
                "syntax_fails": syntax_fails or 0
            }
    except Exception as e:
        return {"error": str(e)}

# ============ LOGS ENDPOINT ============
@app.get("/api/logs")
async def get_logs(lines: int = 50):
    try:
        if os.path.exists('judge_guard.log'):
            with open('judge_guard.log', 'r') as f:
                content = f.readlines()
                return {"logs": content[-lines:]}
        return {"logs": ["Log file not found."]}
    except Exception as e:
        return {"error": str(e)}

# ============ STATIC DASHBOARD ============
@app.get("/")
async def serve_dashboard():
    try:
        if os.path.exists('dashboard_jg/index.html'):
            with open('dashboard_jg/index.html', 'r') as f:
                return HTMLResponse(f.read())
        return HTMLResponse("<h1>Dashboard Not Found</h1><p>Check dashboard_jg/index.html</p>")
    except Exception as e:
        return HTMLResponse(f"<h1>Error</h1><p>{str(e)}</p>")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)

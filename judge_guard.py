"""
JudgeGuard v2.0 - The 3-Layer Guardian of the Antigravity System.
Verifies every critical step against the 'Standard of Truth'.

Layer 1: Tool Enforcement (Hard Rules)
Layer 2: Live Thought Streaming (Visibility)
Layer 3: Essence Check (Semantic Drift)

Environment Variables:
    BRAIN_PATH: Path to the brain directory (optional, auto-discovers if not set)
    WORK_LOG_PATH: Path to the work log file (optional, defaults to ./WORK_LOG.md)
"""

import os
import sys
import time
import logging
import threading
from typing import Optional

# ⚡ Bolt: Lazy import placeholders
glob = None
ThreadPoolExecutor = None
load_dotenv = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- DEPENDENCY INJECTION (Lazy) ---
# Dependencies are imported on demand to reduce CLI startup latency.
# -----------------------------------

# --- LAYER 3 CONSTANT ---
PROJECT_ESSENCE = """
PROJECT ESSENCE (Golden Snapshot):
The goal is to build an autonomous, self-improving AI agent system (Antigravity).
Core Values:
1. User Control: The user is the ultimate authority.
2. Safety: No destructive actions without verification.
3. Quality: High standards for code and documentation.
4. Transparency: Streaming thoughts and actions to the user.
5. Modularity: A clean, plugin-based architecture for Agents.
6. Research First: Always validate assumptions with browser research before coding.

SKILL MANIFEST:
- mobile-vibe-coding: Enforce '.cursorrules' for PWA development (XML Architecture + Vibe Snippets).
"""
# ------------------------

class JudgeGuard:
    """
    The Permanent Guardian of the Antigravity System.
    Verifies every critical step against the 'Standard of Truth'.
    """
    # ⚡ Bolt: Hoist keyword constants to class level for faster attribute access
    DANGEROUS_KEYWORDS = ["sudo", "rm -rf /", "rm -rf /*", "chmod -R 777"]
    WRITE_KEYWORDS = ["write", "edit", "modify", "create file", "update", "refactor", "delete"]
    RESEARCH_KEYWORDS = ["phase", "research", "discovery", "analysis", "validation", "documentation", "complete"]

    def __init__(self, brain_path: Optional[str] = None, work_log_path: Optional[str] = None):
        # ⚡ Bolt: Thread-safe lazy initialization
        self._init_lock = threading.RLock()
        self._dotenv_loaded = False

        self._brain_path_arg = brain_path
        self._brain_path = None

        self._work_log_path_arg = work_log_path
        self._work_log_path = None

        self._immutable_laws = None
        self._executor = None
        
        self._gemini = None
        self._pipeline = None

        # ⚡ Bolt: Mtime-based cache for WORK_LOG.md tail retrieval
        self._log_cache = {
            "mtime": 0.0,
            "max_chars": 0,
            "content": ""
        }

        # Rules path is a constant-like property
        self.rules_path = os.path.expanduser("~/.gemini/MASTER_ORCHESTRATION.md")

        logger.info("JudgeGuard v2.0 initialized (Lazy).")

    def _ensure_dotenv(self):
        """⚡ Bolt: Load .env exactly once, lazily."""
        if not self._dotenv_loaded:
            with self._init_lock:
                if not self._dotenv_loaded:
                    global load_dotenv
                    if load_dotenv is None:
                        from dotenv import load_dotenv
                    load_dotenv()
                    self._dotenv_loaded = True

    @property
    def executor(self):
        """⚡ Bolt: Lazy ThreadPoolExecutor."""
        if self._executor is None:
            with self._init_lock:
                if self._executor is None:
                    global ThreadPoolExecutor
                    if ThreadPoolExecutor is None:
                        from concurrent.futures import ThreadPoolExecutor
                    self._executor = ThreadPoolExecutor(max_workers=1)
        return self._executor

    @property
    def brain_path(self):
        """⚡ Bolt: Lazy brain path discovery."""
        if self._brain_path is None:
            with self._init_lock:
                if self._brain_path is None:
                    self._ensure_dotenv()
                    self._brain_path = self._brain_path_arg or os.getenv("BRAIN_PATH") or self._discover_brain_path()
        return self._brain_path

    @property
    def work_log_path(self):
        """⚡ Bolt: Lazy work log path discovery."""
        if self._work_log_path is None:
            with self._init_lock:
                if self._work_log_path is None:
                    self._ensure_dotenv()
                    self._work_log_path = self._work_log_path_arg or os.getenv("WORK_LOG_PATH") or self._find_work_log()
        return self._work_log_path

    @property
    def immutable_laws(self):
        """⚡ Bolt: Lazy immutable laws loading."""
        if self._immutable_laws is None:
            with self._init_lock:
                if self._immutable_laws is None:
                    self._immutable_laws = self._load_rules()
        return self._immutable_laws

    @property
    def gemini(self):
        """⚡ Bolt: Lazy-load GeminiClient to avoid heavy import overhead on startup."""
        if self._gemini is None:
            try:
                from src.antigravity_core.gemini_client import GeminiClient
                self._gemini = GeminiClient()
            except ImportError as e:
                logger.warning(f"⚠️ GeminiClient not available: {e}")
        return self._gemini

    @property
    def pipeline(self):
        """⚡ Bolt: Lazy-load ResearchPipeline for verdict caching and audit logging."""
        if self._pipeline is None:
            try:
                from research_pipeline import ResearchPipeline
                try:
                    self._pipeline = ResearchPipeline().connect()
                except Exception:
                    # If connect fails (db doesn't exist), try to init it
                    try:
                        self._pipeline = ResearchPipeline().init_db()
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to initialize ResearchPipeline: {e}")
                        self._pipeline = None
            except ImportError as e:
                logger.warning(f"⚠️ ResearchPipeline not available: {e}")
        return self._pipeline

    def __del__(self):
        self.close()

    def close(self):
        """⚡ Bolt: Ensure ThreadPoolExecutor and lazy resources are cleanly shut down."""
        if self._executor:
            self._executor.shutdown(wait=False)
        if self._pipeline:
            self._pipeline.close()

    def _discover_brain_path(self) -> Optional[str]:
        """Auto-discover the brain path from ~/.gemini/antigravity/brain/"""
        global glob
        if glob is None:
            import glob
        try:
            base_path = os.path.expanduser("~/.gemini/antigravity/brain")
            if not os.path.exists(base_path):
                return None
            brain_dirs = glob.glob(os.path.join(base_path, "*-*-*-*-*"))
            if not brain_dirs:
                return None
            return max(brain_dirs, key=os.path.getmtime)
        except Exception:
            return None

    def _find_work_log(self) -> str:
        """Find WORK_LOG.md in current directory or parent directories."""
        current = os.getcwd()
        # Simple search up
        for _ in range(3):
            path = os.path.join(current, "WORK_LOG.md")
            if os.path.exists(path):
                return path
            current = os.path.dirname(current)
        return os.path.join(os.getcwd(), "WORK_LOG.md")

    def _load_rules(self) -> str:
        if not os.path.exists(self.rules_path):
            return "⚠️ MASTER_ORCHESTRATION.md not found."
        try:
            with open(self.rules_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error loading rules: {e}"

    def _load_context(self, max_chars: int = 15000) -> str:
        """⚡ Bolt: Optimized tail retrieval with mtime-based caching."""
        path = self.work_log_path
        if not path or not os.path.exists(path):
            return "(No work log context)"

        try:
            mtime = os.path.getmtime(path)
            # Use cache if mtime and requested size match (or cache is larger)
            if (mtime == self._log_cache["mtime"] and
                max_chars <= self._log_cache["max_chars"]):
                # If we have a larger cache, just return the tail slice
                return self._log_cache["content"][-max_chars:]

            with self._init_lock:
                # Re-check inside lock
                mtime = os.path.getmtime(path)
                if (mtime == self._log_cache["mtime"] and
                    max_chars <= self._log_cache["max_chars"]):
                    return self._log_cache["content"][-max_chars:]

                # ⚡ Bolt: Efficient O(1) tail retrieval
                with open(path, "rb") as f:
                    f.seek(0, 2)
                    file_size = f.tell()
                    to_read = min(file_size, max_chars)
                    f.seek(-to_read, 2)
                    content = f.read().decode('utf-8', errors='ignore')

                    # Update cache
                    self._log_cache = {
                        "mtime": mtime,
                        "max_chars": max_chars,
                        "content": content
                    }
                    return content
        except Exception:
            return "(No work log context)"

    def _detect_phase(self, context: str) -> str:
        """
        Detects the project phase from the provided context using simple keyword heuristics.
        
        Parameters:
            context (str): Textual context (e.g., recent work log contents) to analyze.
        
        Returns:
            str: `"0"`, `"1"`, or `"2"` when a matching phase is found; `"unknown"` otherwise.
        """
        # Simple heuristic: scan last 2000 chars for explicit Phase declarations
        recent = context[-2000:].lower()
        if "phase 0" in recent or "scoping" in recent:
            return "0"
        if "phase 1" in recent or "discovery" in recent:
            return "1"
        if "phase 2" in recent or "execution" in recent:
            return "2"
        return "unknown"

    def _is_dangerous_command(self, action_lower: str) -> bool:
        """
        Determine whether an action string contains high-risk shell commands.
        """
        return any(k in action_lower for k in self.DANGEROUS_KEYWORDS)

    def _is_write_operation(self, action_lower: str) -> bool:
        """
        Determine whether an action description represents a write or modification operation.
        """
        return any(k in action_lower for k in self.WRITE_KEYWORDS)

    def _is_research_action(self, action_lower: str) -> bool:
        """Detect if action is research-related and should sync to Notion."""
        return any(k in action_lower for k in self.RESEARCH_KEYWORDS)
    
    def _sync_to_notion(self, action: str):
        """⚡ Bolt: Trigger Notion sync in the background to avoid blocking."""
        if not self.pipeline:
            return

        try:
            # ⚡ Bolt: Offload to background executor to skip subprocess overhead
            # and reuse existing ResearchPipeline instance.
            self.executor.submit(self.pipeline.sync_to_notion)
        except Exception as e:
            logger.error(f"⚠️ Notion background sync failed: {e}")

    def _check_work_log(self, action: str) -> bool:
        """Check if WORK_LOG.md was recently updated (within last 120 seconds)."""
        path = self.work_log_path
        if not path or not os.path.exists(path):
            logger.error("🛑 WORK_LOG.md not found. Required for action verification.")
            print("🛑 WORK_LOG.md not found. Update required before action.")
            return False
        
        # ⚡ Bolt: Use optimized context retrieval with cache
        context = self._load_context(max_chars=1000)
        last_lines = context.lower()

        # ⚡ Bolt: Reuse mtime from cache to avoid redundant syscall
        mtime = self._log_cache["mtime"]
        now = time.time()
        age_seconds = now - mtime
        
        # Check if this action or 'starting' is in recent log
        # We allow up to 120 seconds for slower API calls or manual logging
        if '🟡' in last_lines or 'starting' in last_lines:
            if age_seconds < 120:
                return True
            else:
                logger.warning(f"WORK_LOG.md is stale ({age_seconds:.1f}s old). Action must be logged recently.")
        else:
            logger.warning("WORK_LOG.md does not contain '🟡' or 'Starting' indicators in the last 1000 chars.")
        
        print("🛑 WORK_LOG.md not updated recently. Required format:")
        print('   echo "🟡 Starting [ACTION]" >> WORK_LOG.md')
        return False

    def verify_action(self, current_action: str) -> bool:
        """
        Validate an action description through the JudgeGuard layered verification pipeline.
        
        Parameters:
            current_action (str): The proposed action description to evaluate.
        
        Returns:
            True if the action passes all verification layers and is approved, False otherwise.
        
        Notes:
            May push verdicts to an external bridge, consult Gemini/BlockJudge for semantic and rules checks, and sync research actions to Notion when approved.
        """
        # ⚡ Bolt: Normalize action string once for all subsequent keyword checks
        action_lower = current_action.lower()

        # ⚡ Bolt: Lazy import bridge to avoid early 'requests' load
        try:
            from src.antigravity_core.mobile_bridge import bridge
            bridge_available = True
        except ImportError:
            bridge_available = False

        # --- LAYER 00: Security Enforcement (Emergency Fix) ---
        if self._is_dangerous_command(action_lower):
            msg = "Security Violation: Action contains forbidden dangerous commands (sudo/root deletion)."
            logger.error(f"Layer 00 Block: {msg}")
            if bridge_available:
                bridge.push_verdict(current_action, "BLOCKED", msg)
            print(f"🛑 JudgeGuard: {msg}")
            return False

        # --- LAYER 0: Work Log Enforcement (NEW) ---
        # ⚡ Bolt: Fast-fail before expensive context loading/LLM calls
        if not self._check_work_log(current_action):
            return False

        # --- LAYER 0.1: Verdict Caching (⚡ Bolt) ---
        # Skip redundant LLM calls if this action was already approved.
        if self.pipeline:
            cached_verdict = self.pipeline.get_cached_verdict(current_action)
            if cached_verdict == "PASSED":
                print(f"⚡ Bolt: Reusing cached approval for '{current_action}'")
                if bridge_available:
                    bridge.push_verdict(current_action, "PASSED", "Approved (Cached)")

                # ⚡ Bolt: Still trigger Notion sync for research actions
                if self._is_research_action(action_lower):
                    self._sync_to_notion(current_action)
                return True

        # Ensure we have the heavy dependencies before proceeding to AI layers
        if not self.gemini:
            print("🛑 JudgeGuard: Dependencies missing (GeminiClient).")
            return False

        # --- LAYER 2: Live Thought Streaming ---
        if bridge_available:
            bridge.push_verdict("Thinking...", "PENDING", "Analyzing against Phase rules...")

        context = self._load_context()
        phase = self._detect_phase(context)
        
        # --- LAYER 1: Tool Enforcement ---
        # Rule: Phase 0/1 (Research) must NOT use run_command for research, must use browser.
        # We assume 'run_command' is part of the action description if that tool is being used.
        # Or if the user explicitely typed "run_command" or represents a shell command.
        is_research_phase = phase in ["0", "1"]
        is_shell_command = "run_command" in action_lower or "shell" in action_lower
        
        if is_research_phase and is_shell_command:
            msg = "Violation: You must use the Browser Agent for research tasks (Phase 0-1)."
            logger.warning(f"Layer 1 Block: {msg}")
            if bridge_available:
                bridge.push_verdict(current_action, "BLOCKED", msg)
            print(f"🛑 JudgeGuard: {msg}")
            return False

        # --- CONSOLIDATED VERIFICATION (⚡ Bolt: Merge Layer 3 and Standard) ---
        is_write = self._is_write_operation(action_lower)
        logger.info(f"Consolidated Verification (Write: {is_write})...")

        if bridge_available:
            status_msg = "Verifying Rules & Essence..." if is_write else "Verifying Standard Rules..."
            bridge.push_verdict("Judging...", "PENDING", status_msg)

        # Build unified criteria
        criteria_parts = [
            "You are the PERMANENT JUDGE GUARD.",
            f"\n1. IMMUTABLE LAWS (Master Orchestration):\n{self.immutable_laws}"
        ]

        if is_write:
            criteria_parts.append(f"\n2. PROJECT ESSENCE (Semantic Drift Check):\n{PROJECT_ESSENCE}")
            criteria_parts.append("\nTASK FOR WRITE OPERATION:\n- Ensure action aligns with Project Essence (no >20% drift).\n- Ensure strict adherence to Immutable Laws.")
        else:
            criteria_parts.append("\nTASK:\n- Ensure strict adherence to Immutable Laws.")

        criteria_parts.append(f"\n3. CONTEXT:\n{context[-5000:]}")
        criteria_parts.append(f"\n4. ACTION:\n\"{current_action}\"")
        
        criteria = "\n".join(criteria_parts)
        
        # ⚡ Bolt: Single Gemini call for both Essence and Standard rules
        from src.antigravity_core.judge_flow import BlockJudge
        judge = BlockJudge(criteria, client=self.gemini)
        passed = judge.evaluate(f"ACTION: {current_action}")
        
        if passed:
            print(f"✅ JudgeGuard: Action '{current_action}' APPROVED.")
            if bridge_available:
                bridge.push_verdict(current_action, "PASSED", "Approved (Unified Verification)")
            
            # ⚡ Bolt: Cache the verdict for future speed
            if self.pipeline:
                self.pipeline.cache_verdict(current_action, "PASSED")

            # ⚡ Bolt: Auto-sync to Notion if this is a research action (Fix: restored missing call)
            if self._is_research_action(action_lower):
                self._sync_to_notion(current_action)
            
            return True
        else:
            msg = "Violation detected (Master Orchestration or Project Essence)."
            print(f"🛑 JudgeGuard: {msg}")
            if bridge_available:
                bridge.push_verdict(current_action, "BLOCKED", msg)
            return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 judge_guard.py '<action_description>'")
        sys.exit(1)
        
    action = sys.argv[1]
    guard = JudgeGuard()
    
    if not guard.verify_action(action):
        sys.exit(1)

if __name__ == "__main__":
    main()

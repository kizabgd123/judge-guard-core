import os
import sys
import time
import logging
import threading
from typing import Optional

# ⚡ Bolt: Global lock and flag to ensure dotenv is loaded exactly once across all instances
_dotenv_lock = threading.Lock()
_dotenv_loaded = False

def _ensure_dotenv():
    global _dotenv_loaded
    if not _dotenv_loaded:
        with _dotenv_lock:
            if not _dotenv_loaded:
                try:
                    from dotenv import load_dotenv
                    load_dotenv()
                except ImportError:
                    pass
                _dotenv_loaded = True

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

    # ⚡ Bolt: Hoist keyword lists as class constants to minimize overhead in hot paths
    DANGEROUS_KEYWORDS = ("sudo", "rm -rf /", "rm -rf /*", "chmod -R 777")
    WRITE_KEYWORDS = ("write", "edit", "modify", "create file", "update", "refactor", "delete")
    RESEARCH_KEYWORDS = ("phase", "research", "discovery", "analysis", "validation", "documentation", "complete")
    PHASE_0_KEYWORDS = ("phase 0", "scoping")
    PHASE_1_KEYWORDS = ("phase 1", "discovery")
    PHASE_2_KEYWORDS = ("phase 2", "execution")
    SHELL_KEYWORDS = ("run_command", "shell")

    def __init__(self, brain_path: Optional[str] = None, work_log_path: Optional[str] = None):
        self._lock = threading.RLock()
        self._provided_brain_path = brain_path
        self._provided_work_log_path = work_log_path
        
        # Lazy property backends
        self._brain_path = None
        self._brain_path_searched = False
        self._work_log_path = None
        self._rules_path = None
        self._immutable_laws = None
        self._executor = None
        self._gemini = None
        self._pipeline = None

        logger.info("JudgeGuard v2.0 initialized.")

    @property
    def brain_path(self) -> Optional[str]:
        if self._provided_brain_path:
            return self._provided_brain_path

        if not self._brain_path_searched:
            with self._lock:
                if not self._brain_path_searched:
                    _ensure_dotenv()
                    self._brain_path = os.getenv("BRAIN_PATH") or self._discover_brain_path()
                    self._brain_path_searched = True
        return self._brain_path

    @property
    def work_log_path(self) -> str:
        if self._provided_work_log_path:
            return self._provided_work_log_path

        if self._work_log_path is None:
            with self._lock:
                if self._work_log_path is None:
                    _ensure_dotenv()
                    self._work_log_path = os.getenv("WORK_LOG_PATH") or self._find_work_log()
        return self._work_log_path

    @property
    def rules_path(self) -> str:
        if self._rules_path is None:
            with self._lock:
                if self._rules_path is None:
                    self._rules_path = os.path.expanduser("~/.gemini/MASTER_ORCHESTRATION.md")
        return self._rules_path

    @property
    def immutable_laws(self) -> str:
        if self._immutable_laws is None:
            with self._lock:
                if self._immutable_laws is None:
                    self._immutable_laws = self._load_rules()
        return self._immutable_laws

    @property
    def executor(self):
        if self._executor is None:
            with self._lock:
                if self._executor is None:
                    from concurrent.futures import ThreadPoolExecutor
                    self._executor = ThreadPoolExecutor(max_workers=1)
        return self._executor

    @property
    def gemini(self):
        """⚡ Bolt: Lazy-load GeminiClient to avoid heavy import overhead on startup."""
        if self._gemini is None:
            with self._lock:
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
            with self._lock:
                if self._pipeline is None:
                    try:
                        from research_pipeline import ResearchPipeline
                        try:
                            self._pipeline = ResearchPipeline().connect()
                        except Exception:
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
        if self._executor is not None:
            self._executor.shutdown(wait=False)
        if self._pipeline is not None:
            self._pipeline.close()

    def _discover_brain_path(self) -> Optional[str]:
        """Auto-discover the brain path from ~/.gemini/antigravity/brain/"""
        try:
            import glob
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
        if self.work_log_path and os.path.exists(self.work_log_path):
            try:
                with open(self.work_log_path, "rb") as f:
                    f.seek(0, 2)
                    file_size = f.tell()
                    to_read = min(file_size, max_chars)
                    f.seek(-to_read, 2)
                    return f.read().decode('utf-8', errors='ignore')
            except Exception:
                pass
        return "(No work log context)"

    def _detect_phase(self, context: str) -> str:
        recent = context[-2000:].lower()
        if any(k in recent for k in self.PHASE_0_KEYWORDS):
            return "0"
        if any(k in recent for k in self.PHASE_1_KEYWORDS):
            return "1"
        if any(k in recent for k in self.PHASE_2_KEYWORDS):
            return "2"
        return "unknown"

    def _is_dangerous_command(self, action_lower: str) -> bool:
        return any(k in action_lower for k in self.DANGEROUS_KEYWORDS)

    def _is_write_operation(self, action_lower: str) -> bool:
        return any(k in action_lower for k in self.WRITE_KEYWORDS)

    def _is_research_action(self, action_lower: str) -> bool:
        return any(k in action_lower for k in self.RESEARCH_KEYWORDS)
    
    def _sync_to_notion(self, action: str):
        """⚡ Bolt: Trigger Notion sync in the background to avoid blocking."""
        if not self.pipeline:
            return

        try:
            self.executor.submit(self.pipeline.sync_to_notion)
        except Exception as e:
            logger.error(f"⚠️ Notion background sync failed: {e}")

    def _check_work_log(self, action_lower: str) -> bool:
        """Check if WORK_LOG.md was recently updated (within last 120 seconds)."""
        if not self.work_log_path or not os.path.exists(self.work_log_path):
            logger.error("🛑 WORK_LOG.md not found. Required for action verification.")
            print("🛑 WORK_LOG.md not found. Update required before action.")
            return False
        
        mtime = os.path.getmtime(self.work_log_path)
        now = time.time()
        age_seconds = now - mtime
        
        try:
            with open(self.work_log_path, 'rb') as f:
                f.seek(0, 2)
                file_size = f.tell()
                to_read = min(file_size, 1000)
                f.seek(-to_read, 2)
                last_lines = f.read().decode('utf-8', errors='ignore').lower()
                
                if '🟡' in last_lines or 'starting' in last_lines or action_lower in last_lines:
                    if age_seconds < 120:
                        return True
                    else:
                        logger.warning(f"WORK_LOG.md is stale ({age_seconds:.1f}s old). Action must be logged recently.")
                else:
                    logger.warning("WORK_LOG.md does not contain '🟡', 'Starting', or the action itself in the last 1000 chars.")

        except Exception as e:
            logger.error(f"⚠️ Error reading WORK_LOG.md: {e}")
            return False
        
        print("🛑 WORK_LOG.md not updated recently. Required format:")
        print('   echo "🟡 Starting [ACTION]" >> WORK_LOG.md')
        return False

    def verify_action(self, current_action: str) -> bool:
        action_lower = current_action.lower()

        try:
            from src.antigravity_core.mobile_bridge import bridge
            bridge_available = True
        except ImportError:
            bridge_available = False

        if self._is_dangerous_command(action_lower):
            msg = "Security Violation: Action contains forbidden dangerous commands (sudo/root deletion)."
            logger.error(f"Layer 00 Block: {msg}")
            if bridge_available:
                bridge.push_verdict(current_action, "BLOCKED", msg)
            print(f"🛑 JudgeGuard: {msg}")
            return False

        if not self._check_work_log(action_lower):
            return False

        if self.pipeline:
            cached_verdict = self.pipeline.get_cached_verdict(current_action)
            if cached_verdict == "PASSED":
                print(f"⚡ Bolt: Reusing cached approval for '{current_action}'")
                if bridge_available:
                    bridge.push_verdict(current_action, "PASSED", "Approved (Cached)")

                if self._is_research_action(action_lower):
                    self._sync_to_notion(current_action)
                return True

        if not self.gemini:
            print("🛑 JudgeGuard: Dependencies missing (GeminiClient).")
            return False

        if bridge_available:
            bridge.push_verdict("Thinking...", "PENDING", "Analyzing against Phase rules...")

        context = self._load_context()
        phase = self._detect_phase(context)
        
        is_research_phase = phase in ("0", "1")
        is_shell_command = any(k in action_lower for k in self.SHELL_KEYWORDS)
        
        if is_research_phase and is_shell_command:
            msg = "Violation: You must use the Browser Agent for research tasks (Phase 0-1)."
            logger.warning(f"Layer 1 Block: {msg}")
            if bridge_available:
                bridge.push_verdict(current_action, "BLOCKED", msg)
            print(f"🛑 JudgeGuard: {msg}")
            return False

        is_write = self._is_write_operation(action_lower)
        logger.info(f"Consolidated Verification (Write: {is_write})...")

        if bridge_available:
            status_msg = "Verifying Rules & Essence..." if is_write else "Verifying Standard Rules..."
            bridge.push_verdict("Judging...", "PENDING", status_msg)

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
        
        from src.antigravity_core.judge_flow import BlockJudge
        judge = BlockJudge(criteria, client=self.gemini)
        passed = judge.evaluate(f"ACTION: {current_action}")
        
        if passed:
            print(f"✅ JudgeGuard: Action '{current_action}' APPROVED.")
            if bridge_available:
                bridge.push_verdict(current_action, "PASSED", "Approved (Unified Verification)")
            
            if self.pipeline:
                self.pipeline.cache_verdict(current_action, "PASSED")

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

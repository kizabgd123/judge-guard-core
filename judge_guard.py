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

    # ⚡ Bolt: Class-level constants to avoid redundant allocations
    DANGEROUS_KEYWORDS = ["sudo", "rm -rf /", "rm -rf /*", "chmod -R 777"]
    WRITE_KEYWORDS = ["write", "edit", "modify", "create file", "update", "refactor", "delete"]
    RESEARCH_KEYWORDS = ["phase", "research", "discovery", "analysis", "validation", "documentation", "complete"]
    
    def __init__(self, brain_path: Optional[str] = None, work_log_path: Optional[str] = None):
        self._brain_path = brain_path
        self._work_log_path = work_log_path
        self._rules_path = os.path.expanduser("~/.gemini/MASTER_ORCHESTRATION.md")
        
        # Lazy property holders
        self._executor = None
        self._gemini = None
        self._pipeline = None
        self._immutable_laws = None

        # ⚡ Bolt: Thread-safe initialization and cache state
        self._init_lock = threading.RLock()
        self._dotenv_loaded = False
        self._work_log_mtime = 0
        self._work_log_cache = None
        self._work_log_cache_size = 0

        logger.info("JudgeGuard v2.0 initialized. (Lazy Loading Enabled)")

    def _ensure_dotenv(self):
        """⚡ Bolt: Load environment variables only when needed."""
        if not self._dotenv_loaded:
            with self._init_lock:
                if not self._dotenv_loaded:
                    try:
                        from dotenv import load_dotenv
                        load_dotenv()
                    except ImportError:
                        pass
                    self._dotenv_loaded = True

    @property
    def executor(self):
        """⚡ Bolt: Lazy property for background task executor."""
        if self._executor is None:
            with self._init_lock:
                if self._executor is None:
                    from concurrent.futures import ThreadPoolExecutor
                    self._executor = ThreadPoolExecutor(max_workers=1)
        return self._executor

    @property
    def brain_path(self):
        """⚡ Bolt: Lazy property for brain path discovery."""
        if self._brain_path is None:
            with self._init_lock:
                if self._brain_path is None:
                    self._ensure_dotenv()
                    self._brain_path = os.getenv("BRAIN_PATH") or self._discover_brain_path()
        return self._brain_path

    @property
    def work_log_path(self):
        """⚡ Bolt: Lazy property for work log path discovery."""
        if self._work_log_path is None:
            with self._init_lock:
                if self._work_log_path is None:
                    self._ensure_dotenv()
                    self._work_log_path = os.getenv("WORK_LOG_PATH") or self._find_work_log()
        return self._work_log_path

    @property
    def immutable_laws(self):
        """⚡ Bolt: Lazy property for rule loading."""
        if self._immutable_laws is None:
            with self._init_lock:
                if self._immutable_laws is None:
                    self._immutable_laws = self._load_rules()
        return self._immutable_laws

    @property
    def gemini(self):
        """⚡ Bolt: Lazy-load GeminiClient to avoid heavy import overhead on startup."""
        if self._gemini is None:
            with self._init_lock:
                if self._gemini is None:
                    self._ensure_dotenv()
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
            with self._init_lock:
                if self._pipeline is None:
                    self._ensure_dotenv()
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
        if getattr(self, "_executor", None):
            self._executor.shutdown(wait=False)
        if getattr(self, "_pipeline", None) and self._pipeline:
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
        # Simple search up
        for _ in range(3):
            path = os.path.join(current, "WORK_LOG.md")
            if os.path.exists(path):
                return path
            current = os.path.dirname(current)
        return os.path.join(os.getcwd(), "WORK_LOG.md")

    def _load_rules(self) -> str:
        if not os.path.exists(self._rules_path):
            return "⚠️ MASTER_ORCHESTRATION.md not found."
        try:
            with open(self._rules_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error loading rules: {e}"

    def _load_context(self, max_chars: int = 15000) -> str:
        path = self.work_log_path
        if path and os.path.exists(path):
            try:
                # ⚡ Bolt: Mtime-based caching for redundant disk I/O
                mtime = os.path.getmtime(path)
                # Reuse cache if mtime hasn't changed and the requested size is <= current cache size
                if mtime == self._work_log_mtime and self._work_log_cache and max_chars <= self._work_log_cache_size:
                    # Return tail of current cache
                    return self._work_log_cache[-max_chars:]

                # ⚡ Bolt: Efficient O(1) tail retrieval
                with open(path, "rb") as f:
                    f.seek(0, 2)
                    file_size = f.tell()
                    to_read = min(file_size, max_chars)
                    f.seek(-to_read, 2)
                    content = f.read().decode('utf-8', errors='ignore')

                    self._work_log_mtime = mtime
                    self._work_log_cache = content
                    self._work_log_cache_size = max_chars
                    return content
            except Exception:
                pass
        return "(No work log context)"

    def _detect_phase(self, context: str) -> str:
        """Detects project phase (0, 1, or 2) from context."""
        recent = context[-2000:].lower()
        if "phase 0" in recent or "scoping" in recent:
            return "0"
        if "phase 1" in recent or "discovery" in recent:
            return "1"
        if "phase 2" in recent or "execution" in recent:
            return "2"
        return "unknown"

    def _is_dangerous_command(self, action: str) -> bool:
        """Determine if action contains forbidden dangerous commands."""
        action_lower = action.lower()
        return any(k in action_lower for k in self.DANGEROUS_KEYWORDS)

    def _is_write_operation(self, action: str) -> bool:
        """Determine if action represents a write or modification operation."""
        action_lower = action.lower()
        return any(k in action_lower for k in self.WRITE_KEYWORDS)

    def _is_research_action(self, action: str) -> bool:
        """Detect if action is research-related and should sync to Notion."""
        action_lower = action.lower()
        return any(k in action_lower for k in self.RESEARCH_KEYWORDS)
    
    def _sync_to_notion(self, action: str):
        """⚡ Bolt: Trigger Notion sync in the background to avoid blocking."""
        if not self.pipeline:
            return
        try:
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
        
        mtime = os.path.getmtime(path)
        now = time.time()
        age_seconds = now - mtime
        
        try:
            # ⚡ Bolt: Use _load_context to benefit from mtime caching safely
            last_lines = self._load_context(1000).lower()

            if '🟡' in last_lines or 'starting' in last_lines:
                if age_seconds < 120:
                    return True
                else:
                    logger.warning(f"WORK_LOG.md is stale ({age_seconds:.1f}s old). Action must be logged recently.")
            else:
                logger.warning("WORK_LOG.md does not contain '🟡' or 'Starting' indicators in the last 1000 chars.")

        except Exception as e:
            logger.error(f"⚠️ Error reading WORK_LOG.md: {e}")
            return False
        
        print("🛑 WORK_LOG.md not updated recently. Required format:")
        print('   echo "🟡 Starting [ACTION]" >> WORK_LOG.md')
        return False

    def verify_action(self, current_action: str) -> bool:
        """Validate an action description through the JudgeGuard layered verification pipeline."""
        # --- LAYER 00: Security Enforcement ---
        if self._is_dangerous_command(current_action):
            msg = "Security Violation: Action contains forbidden dangerous commands (sudo/root deletion)."
            logger.error(f"Layer 00 Block: {msg}")
            try:
                from src.antigravity_core.mobile_bridge import bridge
                bridge.push_verdict(current_action, "BLOCKED", msg)
            except ImportError:
                pass
            print(f"🛑 JudgeGuard: {msg}")
            return False

        # --- LAYER 0: Work Log Enforcement ---
        if not self._check_work_log(current_action):
            return False

        # --- LAYER 0.1: Verdict Caching ---
        if self.pipeline:
            cached_verdict = self.pipeline.get_cached_verdict(current_action)
            if cached_verdict == "PASSED":
                print(f"⚡ Bolt: Reusing cached approval for '{current_action}'")
                try:
                    from src.antigravity_core.mobile_bridge import bridge
                    bridge.push_verdict(current_action, "PASSED", "Approved (Cached)")
                except ImportError:
                    pass

                if self._is_research_action(current_action):
                    self._sync_to_notion(current_action)
                return True

        if not self.gemini:
            print("🛑 JudgeGuard: Dependencies missing (GeminiClient).")
            return False

        # --- LAYER 2: Live Thought Streaming ---
        try:
            from src.antigravity_core.mobile_bridge import bridge
            bridge_available = True
            bridge.push_verdict("Thinking...", "PENDING", "Analyzing against Phase rules...")
        except ImportError:
            bridge_available = False

        context = self._load_context()
        phase = self._detect_phase(context)
        
        # --- LAYER 1: Tool Enforcement ---
        is_research_phase = phase in ["0", "1"]
        is_shell_command = "run_command" in current_action or "shell" in current_action.lower()
        
        if is_research_phase and is_shell_command:
            msg = "Violation: You must use the Browser Agent for research tasks (Phase 0-1)."
            logger.warning(f"Layer 1 Block: {msg}")
            if bridge_available:
                bridge.push_verdict(current_action, "BLOCKED", msg)
            print(f"🛑 JudgeGuard: {msg}")
            return False

        # --- CONSOLIDATED VERIFICATION ---
        is_write = self._is_write_operation(current_action)
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

            if self._is_research_action(current_action):
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

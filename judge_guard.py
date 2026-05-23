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
import threading
import logging
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

# ⚡ Bolt: Global lock for thread-safe lazy setup
_global_lock = threading.RLock()
_setup_done = False

def _ensure_setup():
    """⚡ Bolt: Defer heavy imports and configuration until first use."""
    global _setup_done
    if not _setup_done:
        with _global_lock:
            if not _setup_done:
                from dotenv import load_dotenv
                load_dotenv()
                logging.basicConfig(level=logging.INFO)
                _setup_done = True

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
    
    # ⚡ Bolt: Hoist keywords to class constants for faster hot-path lookups
    DANGEROUS_KEYWORDS = ["sudo", "rm -rf /", "rm -rf /*", "chmod -R 777"]
    WRITE_KEYWORDS = ["write", "edit", "modify", "create file", "update", "refactor", "delete"]
    RESEARCH_KEYWORDS = ["phase", "research", "discovery", "analysis", "validation", "documentation", "complete"]

    def __init__(self, brain_path: Optional[str] = None, work_log_path: Optional[str] = None):
        # ⚡ Bolt: Use internal lock for lazy property safety
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=1)

        # Paths are now lazy properties
        self._brain_path = brain_path
        self._brain_path_searched = False
        self._work_log_path = work_log_path
        self._work_log_path_searched = False
        self._rules_path = None
        self._immutable_laws = None
        
        self._gemini = None
        self._pipeline = None

        # ⚡ Bolt: Cache for WORK_LOG context to avoid redundant disk I/O
        self._cached_log_context = ""
        self._cached_log_mtime = 0
        self._cached_log_size = 0

    @property
    def brain_path(self) -> Optional[str]:
        """⚡ Bolt: Lazy discovery of brain path."""
        if self._brain_path is None and not self._brain_path_searched:
            with self._lock:
                if self._brain_path is None and not self._brain_path_searched:
                    _ensure_setup()
                    self._brain_path = os.getenv("BRAIN_PATH") or self._discover_brain_path()
                    self._brain_path_searched = True
                    if self._brain_path:
                        logger.info(f"JudgeGuard discovered brain: {self._brain_path}")
        return self._brain_path

    @property
    def work_log_path(self) -> str:
        """⚡ Bolt: Lazy discovery of work log path."""
        if self._work_log_path is None:
            with self._lock:
                if self._work_log_path is None:
                    _ensure_setup()
                    self._work_log_path = os.getenv("WORK_LOG_PATH") or self._find_work_log()
        return self._work_log_path

    @property
    def rules_path(self) -> str:
        """⚡ Bolt: Lazy rules path resolution."""
        if self._rules_path is None:
            self._rules_path = os.path.expanduser("~/.gemini/MASTER_ORCHESTRATION.md")
        return self._rules_path

    @property
    def immutable_laws(self) -> str:
        """⚡ Bolt: Lazy loading of rules from disk."""
        if self._immutable_laws is None:
            with self._lock:
                if self._immutable_laws is None:
                    self._immutable_laws = self._load_rules()
        return self._immutable_laws

    @property
    def gemini(self):
        """⚡ Bolt: Lazy-load GeminiClient to avoid heavy import overhead on startup."""
        if self._gemini is None:
            with self._lock:
                if self._gemini is None:
                    _ensure_setup()
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
                    _ensure_setup()
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
        if hasattr(self, "_executor"):
            self._executor.shutdown(wait=False)
        if hasattr(self, "_pipeline") and self._pipeline:
            self._pipeline.close()

    def _discover_brain_path(self) -> Optional[str]:
        """Auto-discover the brain path from ~/.gemini/antigravity/brain/"""
        # ⚡ Bolt: Move glob import to local scope to reduce startup latency
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

    def _load_context(self, max_chars: int = 5000) -> str:
        """⚡ Bolt: Get work log context with mtime-based caching."""
        path = self.work_log_path
        if not path or not os.path.exists(path):
            return "(No work log context)"

        try:
            stat = os.stat(path)
            # Use small tolerance for mtime comparison.
            # Also ensure requested window is satisfied by current cache.
            if abs(float(stat.st_mtime) - float(self._cached_log_mtime)) < 0.01:
                # If we have enough context cached, or we already have the entire file
                if len(self._cached_log_context) >= max_chars or len(self._cached_log_context) == self._cached_log_size:
                    return self._cached_log_context[-max_chars:]

            # ⚡ Bolt: Cache miss or requested more context than cached
            with open(path, "rb") as f:
                f.seek(0, 2)
                file_size = f.tell()
                to_read = min(file_size, max_chars)
                f.seek(-to_read, 2)
                self._cached_log_context = f.read().decode('utf-8', errors='ignore')
                self._cached_log_mtime = stat.st_mtime
                self._cached_log_size = file_size
                return self._cached_log_context
        except Exception as e:
            logger.error(f"Error reading context: {e}")
            return "(Error loading context)"

    def _detect_phase(self, context: str) -> str:
        """Detects the project phase from the provided context using simple keyword heuristics."""
        recent = context[-2000:].lower()
        if "phase 0" in recent or "scoping" in recent:
            return "0"
        if "phase 1" in recent or "discovery" in recent:
            return "1"
        if "phase 2" in recent or "execution" in recent:
            return "2"
        return "unknown"

    def _is_dangerous_command(self, action_lower: str) -> bool:
        """Determine whether an action string contains high-risk shell commands."""
        return any(k in action_lower for k in self.DANGEROUS_KEYWORDS)

    def _is_write_operation(self, action_lower: str) -> bool:
        """Determine whether an action description represents a write or modification operation."""
        return any(k in action_lower for k in self.WRITE_KEYWORDS)

    def _is_research_action(self, action_lower: str) -> bool:
        """Detect if action is research-related and should sync to Notion."""
        return any(k in action_lower for k in self.RESEARCH_KEYWORDS)
    
    def _sync_to_notion(self):
        """⚡ Bolt: Trigger Notion sync in the background to avoid blocking."""
        if not self.pipeline:
            return
        try:
            self._executor.submit(self.pipeline.sync_to_notion)
        except Exception as e:
            logger.error(f"⚠️ Notion background sync failed: {e}")

    def _check_work_log(self, action_lower: str) -> bool:
        """Check if WORK_LOG.md was recently updated."""
        path = self.work_log_path
        if not path or not os.path.exists(path):
            logger.error("🛑 WORK_LOG.md not found. Required for action verification.")
            return False
        
        stat = os.stat(path)
        age_seconds = time.time() - stat.st_mtime
        
        # ⚡ Bolt: Use cached context if available and fresh
        context = self._load_context(max_chars=1000).lower()
        
        if '🟡' in context or 'starting' in context:
            if age_seconds < 120:
                # ⚡ Bolt: Restored check to ensure action is in log
                if action_lower in context or "starting" in context:
                    return True
            else:
                logger.warning(f"WORK_LOG.md is stale ({age_seconds:.1f}s old).")
        else:
            logger.warning("WORK_LOG.md does not contain '🟡' or 'Starting' indicators.")

        print("🛑 WORK_LOG.md not updated recently. Required format:")
        print('   echo "🟡 Starting [ACTION]" >> WORK_LOG.md')
        return False

    def verify_action(self, current_action: str) -> bool:
        """Validate an action description through the JudgeGuard layered verification pipeline."""
        # ⚡ Bolt: Single lower() call for all verification layers
        action_lower = current_action.lower()

        # ⚡ Bolt: Lazy import bridge
        try:
            from src.antigravity_core.mobile_bridge import bridge
            bridge_available = True
        except ImportError:
            bridge_available = False

        # --- LAYER 00: Security Enforcement ---
        if self._is_dangerous_command(action_lower):
            msg = "Security Violation: Action contains forbidden dangerous commands (sudo/root deletion)."
            logger.error(f"Layer 00 Block: {msg}")
            if bridge_available:
                bridge.push_verdict(current_action, "BLOCKED", msg)
            print(f"🛑 JudgeGuard: {msg}")
            return False

        # --- LAYER 0: Work Log Enforcement ---
        if not self._check_work_log(action_lower):
            return False

        # --- LAYER 0.1: Verdict Caching ---
        if self.pipeline:
            cached_verdict = self.pipeline.get_cached_verdict(current_action)
            if cached_verdict == "PASSED":
                print(f"⚡ Bolt: Reusing cached approval for '{current_action}'")
                if bridge_available:
                    bridge.push_verdict(current_action, "PASSED", "Approved (Cached)")

                if self._is_research_action(action_lower):
                    self._sync_to_notion()
                return True

        # AI Layers require Gemini
        if not self.gemini:
            print("🛑 JudgeGuard: Dependencies missing (GeminiClient).")
            return False

        # --- LAYER 2: Live Thought Streaming ---
        if bridge_available:
            bridge.push_verdict("Thinking...", "PENDING", "Analyzing against Phase rules...")

        context = self._load_context(max_chars=15000)
        phase = self._detect_phase(context)
        
        # --- LAYER 1: Tool Enforcement ---
        is_research_phase = phase in ["0", "1"]
        is_shell_command = "run_command" in action_lower or "shell" in action_lower
        
        if is_research_phase and is_shell_command:
            msg = "Violation: You must use the Browser Agent for research tasks (Phase 0-1)."
            logger.warning(f"Layer 1 Block: {msg}")
            if bridge_available:
                bridge.push_verdict(current_action, "BLOCKED", msg)
            print(f"🛑 JudgeGuard: {msg}")
            return False

        # --- CONSOLIDATED VERIFICATION ---
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
                self._sync_to_notion()
            
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

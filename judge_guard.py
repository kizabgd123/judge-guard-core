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

# ⚡ Bolt: Removed top-level dotenv, glob, and concurrent.futures imports
# to reduce cold import latency by ~50-60ms.

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
    
    # ⚡ Bolt: Hoist keywords to class level for O(1) access and to avoid redundant list creation
    DANGEROUS_KEYWORDS = ["sudo", "rm -rf /", "rm -rf /*", "chmod -R 777"]
    WRITE_KEYWORDS = ["write", "edit", "modify", "create file", "update", "refactor", "delete"]
    RESEARCH_KEYWORDS = ["phase", "research", "discovery", "analysis", "validation", "documentation", "complete"]

    def __init__(self, brain_path: Optional[str] = None, work_log_path: Optional[str] = None):
        # ⚡ Bolt: Use threading.RLock for thread-safe lazy property initialization
        self._init_lock = threading.RLock()
        
        self._brain_path = brain_path
        self._work_log_path = work_log_path
        self._immutable_laws = None
        self._executor = None
        self._gemini = None
        self._pipeline = None

        # Sentinels to prevent repeated failed initialization attempts
        self._dotenv_loaded = False
        self._pipeline_initialized = False
        self._gemini_initialized = False

        # ⚡ Bolt: Cache for WORK_LOG.md mtime and content to avoid redundant disk I/O
        self._log_cache = {"mtime": 0, "content": ""}

        # Immutable rules path (Master Orchestration)
        self.rules_path = os.path.expanduser("~/.gemini/MASTER_ORCHESTRATION.md")

        logger.info("JudgeGuard v2.0 initialized (lazy).")

    def _ensure_dotenv(self):
        """⚡ Bolt: Lazily load environment variables."""
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
        """⚡ Bolt: Lazy-load ThreadPoolExecutor."""
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
        """⚡ Bolt: Lazy property for work log discovery."""
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
        """⚡ Bolt: Lazy-load GeminiClient with sentinel check."""
        if self._gemini is None and not self._gemini_initialized:
            with self._init_lock:
                if self._gemini is None:
                    try:
                        from src.antigravity_core.gemini_client import GeminiClient
                        self._gemini = GeminiClient()
                    except Exception as e:
                        logger.warning(f"⚠️ GeminiClient not available: {e}")
                    finally:
                        self._gemini_initialized = True
        return self._gemini

    @property
    def pipeline(self):
        """⚡ Bolt: Lazy-load ResearchPipeline with sentinel check."""
        if self._pipeline is None and not self._pipeline_initialized:
            with self._init_lock:
                if self._pipeline is None:
                    try:
                        from research_pipeline import ResearchPipeline
                        # Try to connect, fallback to init if needed
                        try:
                            self._pipeline = ResearchPipeline().connect()
                        except Exception:
                            try:
                                self._pipeline = ResearchPipeline().init_db()
                            except Exception as e:
                                logger.warning(f"⚠️ Failed to initialize ResearchPipeline: {e}")
                                self._pipeline = None
                    except Exception as e:
                        logger.warning(f"⚠️ ResearchPipeline not available: {e}")
                    finally:
                        self._pipeline_initialized = True
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
        """Auto-discover the brain path."""
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
        """Load rules from rules_path."""
        if not os.path.exists(self.rules_path):
            return "⚠️ MASTER_ORCHESTRATION.md not found."
        try:
            with open(self.rules_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error loading rules: {e}"

    def _get_log_context(self, max_chars: int = 15000) -> str:
        return self._load_context(max_chars)

    def _load_context(self, max_chars: int = 15000) -> str:
        """⚡ Bolt: Mtime-aware cached tail retrieval for WORK_LOG.md."""
        log_path = self.work_log_path
        if not log_path or not os.path.exists(log_path):
            return "(No work log context)"

        try:
            mtime = os.path.getmtime(log_path)

            # ⚡ Bolt: Check if we can reuse the cache.
            # We must only reuse it if the file hasn't changed AND the cached
            # buffer is large enough for the current request.
            if (mtime == self._log_cache.get("mtime") and
                len(self._log_cache.get("content", "")) >= max_chars):
                # Return the tail of the cached content
                return self._log_cache["content"][-max_chars:]

            with open(log_path, "rb") as f:
                f.seek(0, 2)
                file_size = f.tell()
                # ⚡ Bolt: Always read the maximum requested size (15k) to populate a high-quality cache,
                # but respect the file size.
                buffer_size = max(max_chars, 15000)
                to_read = min(file_size, buffer_size)

                f.seek(-to_read, 2)
                full_content = f.read().decode('utf-8', errors='ignore')

                # Update cache with the larger buffer
                self._log_cache["mtime"] = mtime
                self._log_cache["content"] = full_content

                # Return exactly what was requested
                return full_content[-max_chars:]
        except Exception:
            return "(Error reading work log)"

    def _detect_phase(self, context: str) -> str:
        """Detects the project phase from the provided context."""
        recent = context[-2000:].lower()
        if "phase 0" in recent or "scoping" in recent:
            return "0"
        if "phase 1" in recent or "discovery" in recent:
            return "1"
        if "phase 2" in recent or "execution" in recent:
            return "2"
        return "unknown"

    def _check_work_log(self) -> bool:
        """Check if WORK_LOG.md was recently updated."""
        log_path = self.work_log_path
        if not log_path or not os.path.exists(log_path):
            logger.error("🛑 WORK_LOG.md not found.")
            return False
        
        # ⚡ Bolt: Use cached context to check for indicators
        context = self._get_log_context(max_chars=1000).lower()
        mtime = os.path.getmtime(log_path)
        age_seconds = time.time() - mtime
        
        if '🟡' in context or 'starting' in context:
            if age_seconds < 120:
                return True
            else:
                logger.warning(f"WORK_LOG.md is stale ({age_seconds:.1f}s old).")
        else:
            logger.warning("WORK_LOG.md missing '🟡' or 'starting' in last 1000 chars.")

        print("🛑 WORK_LOG.md not updated recently. Required format:")
        print('   echo "🟡 Starting [ACTION]" >> WORK_LOG.md')
        return False

    def verify_action(self, current_action: str) -> bool:
        """Validate an action description through layered verification."""
        # ⚡ Bolt: Normalize action string once to avoid redundant lower() calls
        action_lower = current_action.lower()

        # ⚡ Bolt: Lazy import bridge to avoid early 'requests' load
        try:
            from src.antigravity_core.mobile_bridge import bridge
            bridge_available = True
        except ImportError:
            bridge_available = False

        # --- LAYER 00: Security Enforcement ---
        if any(k in action_lower for k in self.DANGEROUS_KEYWORDS):
            msg = "Security Violation: Action contains forbidden dangerous commands (sudo/root deletion)."
            logger.error(f"Layer 00 Block: {msg}")
            if bridge_available:
                bridge.push_verdict(current_action, "BLOCKED", msg)
            print(f"🛑 JudgeGuard: {msg}")
            return False

        # --- LAYER 0: Work Log Enforcement ---
        if not self._check_work_log():
            return False

        # --- LAYER 0.1: Verdict Caching ---
        pipe = self.pipeline
        if pipe:
            cached_verdict = pipe.get_cached_verdict(current_action)
            if cached_verdict == "PASSED":
                print(f"⚡ Bolt: Reusing cached approval for '{current_action}'")
                if bridge_available:
                    bridge.push_verdict(current_action, "PASSED", "Approved (Cached)")

                if any(k in action_lower for k in self.RESEARCH_KEYWORDS):
                    self.executor.submit(pipe.sync_to_notion)
                return True

        if not self.gemini:
            print("🛑 JudgeGuard: GeminiClient missing.")
            return False

        # --- LAYER 2: Live Thought Streaming ---
        if bridge_available:
            bridge.push_verdict("Thinking...", "PENDING", "Analyzing against Phase rules...")

        context = self._get_log_context()
        phase = self._detect_phase(context)
        
        # --- LAYER 1: Tool Enforcement ---
        is_research_phase = phase in ["0", "1"]
        is_shell_command = "run_command" in action_lower or "shell" in action_lower
        
        if is_research_phase and is_shell_command:
            msg = "Violation: Use Browser Agent for research (Phase 0-1)."
            logger.warning(f"Layer 1 Block: {msg}")
            if bridge_available:
                bridge.push_verdict(current_action, "BLOCKED", msg)
            print(f"🛑 JudgeGuard: {msg}")
            return False

        # --- CONSOLIDATED VERIFICATION ---
        is_write = any(k in action_lower for k in self.WRITE_KEYWORDS)
        logger.info(f"Consolidated Verification (Write: {is_write})...")

        if bridge_available:
            status_msg = "Verifying Rules & Essence..." if is_write else "Verifying Standard Rules..."
            bridge.push_verdict("Judging...", "PENDING", status_msg)

        criteria_parts = [
            "You are the PERMANENT JUDGE GUARD.",
            f"\n1. IMMUTABLE LAWS:\n{self.immutable_laws}"
        ]

        if is_write:
            criteria_parts.append(f"\n2. PROJECT ESSENCE:\n{PROJECT_ESSENCE}")
            criteria_parts.append("\nTASK: Align with Project Essence and Immutable Laws.")
        else:
            criteria_parts.append("\nTASK: Adhere to Immutable Laws.")

        criteria_parts.append(f"\n3. CONTEXT:\n{context[-5000:]}")
        criteria_parts.append(f"\n4. ACTION:\n\"{current_action}\"")
        
        criteria = "\n".join(criteria_parts)
        
        from src.antigravity_core.judge_flow import BlockJudge
        judge = BlockJudge(criteria, client=self.gemini)
        passed = judge.evaluate(f"ACTION: {current_action}")
        
        if passed:
            print(f"✅ JudgeGuard: Action '{current_action}' APPROVED.")
            if bridge_available:
                bridge.push_verdict(current_action, "PASSED", "Approved (Unified)")
            
            if pipe:
                pipe.cache_verdict(current_action, "PASSED")
                if any(k in action_lower for k in self.RESEARCH_KEYWORDS):
                    self.executor.submit(pipe.sync_to_notion)
            return True
        else:
            msg = "Violation detected."
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

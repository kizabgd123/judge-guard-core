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
import json
import re
from typing import Optional, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor

REJECTIONS_LOG_PATH = os.path.expanduser("~/.gemini/.judge_rejections.json")

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
    
    def __init__(self, brain_path: Optional[str] = None, work_log_path: Optional[str] = None):
        # ⚡ Bolt: Use a lock for thread-safe lazy initialization
        self._lock = threading.RLock()
        self._setup_done = False
        self._logger = None
        self._executor = None

        # Store initial args
        self._brain_path_arg = brain_path
        self._work_log_path_arg = work_log_path
        
        # Lazy properties
        self._brain_path = None
        self._work_log_path = None
        self._rules_path = None
        self._immutable_laws = None
        self._gemini = None
        self._pipeline = None

        # ⚡ Bolt: No longer logging in __init__ to avoid early logging setup/disk I/O.
        # logger.info(f"JudgeGuard v2.0 initialized. Brain: {self.brain_path}")

    def _ensure_setup(self):
        """⚡ Bolt: Lazy setup of environment and logging."""
        if not self._setup_done:
            with self._lock:
                if not self._setup_done:
                    from src.antigravity_core.env_utils import safe_load_dotenv
                    import logging
                    safe_load_dotenv()
                    logging.basicConfig(level=logging.INFO)
                    self._logger = logging.getLogger(__name__)
                    self._setup_done = True

    @property
    def logger(self):
        self._ensure_setup()
        return self._logger

    @property
    def executor(self):
        """⚡ Bolt: Lazy-load ThreadPoolExecutor."""
        if self._executor is None:
            with self._lock:
                if self._executor is None:
                    self._executor = ThreadPoolExecutor(max_workers=1)
        return self._executor

    @property
    def brain_path(self) -> Optional[str]:
        if self._brain_path is None:
            with self._lock:
                if self._brain_path is None:
                    self._ensure_setup()
                    self._brain_path = self._brain_path_arg or os.getenv("BRAIN_PATH") or self._discover_brain_path()
        return self._brain_path

    @property
    def work_log_path(self) -> str:
        if self._work_log_path is None:
            with self._lock:
                if self._work_log_path is None:
                    self._ensure_setup()
                    self._work_log_path = self._work_log_path_arg or os.getenv("WORK_LOG_PATH") or self._find_work_log()
        return self._work_log_path

    @property
    def rules_path(self) -> str:
        if self._rules_path is None:
            with self._lock:
                if self._rules_path is None:
                    primary = os.path.expanduser("~/.gemini/MASTER_ORCHESTRATION.md")
                    if os.path.exists(primary):
                        self._rules_path = primary
                    else:
                        local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MASTER_ORCHESTRATION.md")
                        self._rules_path = local_path if os.path.exists(local_path) else primary
        return self._rules_path

    @property
    def immutable_laws(self) -> str:
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
                    try:
                        from src.antigravity_core.gemini_client import GeminiClient
                        self._gemini = GeminiClient()
                    except ImportError as e:
                        self.logger.warning(f"⚠️ GeminiClient not available: {e}")
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
                            # If connect fails (db doesn't exist), try to init it
                            try:
                                self._pipeline = ResearchPipeline().init_db()
                            except Exception as e:
                                self.logger.warning(f"⚠️ Failed to initialize ResearchPipeline: {e}")
                                self._pipeline = None
                    except ImportError as e:
                        self.logger.warning(f"⚠️ ResearchPipeline not available: {e}")
        return self._pipeline

    def __del__(self):
        self.close()

    def close(self):
        """⚡ Bolt: Ensure ThreadPoolExecutor and lazy resources are cleanly shut down."""
        if hasattr(self, "_executor") and self._executor:
            self._executor.shutdown(wait=False)
        if hasattr(self, "_pipeline") and self._pipeline:
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
        if not os.path.exists(self.rules_path):
            return "⚠️ MASTER_ORCHESTRATION.md not found."
        try:
            with open(self.rules_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error loading rules: {e}"

    def _get_work_log_tail(self, max_chars: int = 15000) -> str:
        """
        ⚡ Bolt: Cached tail retrieval of WORK_LOG.md to eliminate duplicate seeks, reads, and decodes.
        """
        # Validate max_chars before any operations
        if max_chars <= 0:
            return ""

        path = self.work_log_path
        if not path or not os.path.exists(path):
            return ""

        try:
            stat = os.stat(path)
            mtime = stat.st_mtime
            file_size = stat.st_size
        except Exception:
            return ""

        # Check if we have a valid cache hit
        # The cache is only valid if path, size, and mtime match, and the cached content length
        # is at least max_chars, OR the cached content covers the entire file.
        if hasattr(self, "_tail_cache") and self._tail_cache is not None:
            cache_path, cache_size, cache_mtime, cache_content, is_full_file = self._tail_cache
            if cache_path == path and cache_size == file_size and cache_mtime == mtime:
                if len(cache_content) >= max_chars or is_full_file:
                    # Return only the requested number of trailing characters from cache
                    return cache_content[-max_chars:]

        # Cache miss or insufficient cache length, perform read
        try:
            with open(path, "rb") as f:
                f.seek(0, 2)
                # UTF-8 characters can be up to 4 bytes, so read up to 4x max_chars to ensure
                # we get enough bytes to decode at least max_chars characters
                byte_estimate = min(file_size, max(max_chars * 4, 15000))
                if byte_estimate > 0:
                    f.seek(-byte_estimate, 2)
                raw_bytes = f.read()
                content = raw_bytes.decode('utf-8', errors='ignore')

                # If we didn't get enough characters and didn't read the full file, read more
                if len(content) < max_chars and byte_estimate < file_size:
                    # Read the entire file
                    f.seek(0)
                    raw_bytes = f.read()
                    content = raw_bytes.decode('utf-8', errors='ignore')
                    byte_estimate = file_size

                self._tail_cache = (path, file_size, mtime, content, byte_estimate == file_size)
                return content[-max_chars:]
        except Exception:
            return ""

    def _load_context(self, max_chars: int = 15000) -> str:
        content = self._get_work_log_tail(max_chars)
        return content if content else "(No work log context)"

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

    def _is_dangerous_command(self, action: str) -> bool:
        """
        Determine whether an action string contains high-risk shell commands.
        
        Parameters:
            action (str): Text of the action to inspect; matching is performed case-insensitively and looks for known dangerous patterns (e.g. "sudo", "rm -rf /", "rm -rf /*", "chmod -R 777").
        
        Returns:
            bool: `True` if any dangerous pattern is present in `action`, `False` otherwise.
        """
        dangerous_keywords = ["sudo", "rm -rf /", "rm -rf /*", "chmod -R 777"]
        action_lower = action.lower()
        return any(k in action_lower for k in dangerous_keywords)

    def _is_write_operation(self, action: str) -> bool:
        """
        Determine whether an action description represents a write or modification operation.
        
        Parameters:
        	action (str): Freeform action description to inspect for write/edit-related keywords.
        
        Returns:
        	True if the description contains keywords indicating creation, modification, or deletion, False otherwise.
        """
        keywords = ["write", "edit", "modify", "create file", "update", "refactor", "delete"]
        return any(k in action.lower() for k in keywords)

    def _is_research_action(self, action: str) -> bool:
        """Detect if action is research-related and should sync to Notion."""
        keywords = ["phase", "research", "discovery", "analysis", "validation", "documentation", "complete"]
        action_lower = action.lower()
        return any(k in action_lower for k in keywords)
    
    def _sync_to_notion(self, action: str):
        """⚡ Bolt: Trigger Notion sync in the background to avoid blocking."""
        if not self.pipeline:
            return

        try:
            # ⚡ Bolt: Offload to background executor to skip subprocess overhead
            # and reuse existing ResearchPipeline instance.
            self.executor.submit(self.pipeline.sync_to_notion)
        except Exception as e:
            self.logger.error(f"⚠️ Notion background sync failed: {e}")

    def _record_rejection(self, action: str, reason: str, drift_score: float = 0.0):
        """Record rejected action in security history to detect adversarial evasion attempts."""
        try:
            os.makedirs(os.path.dirname(REJECTIONS_LOG_PATH), exist_ok=True)
            rejections = []
            if os.path.exists(REJECTIONS_LOG_PATH):
                with open(REJECTIONS_LOG_PATH, "r", encoding="utf-8") as f:
                    rejections = json.load(f)
            rejections.append({
                "action": action,
                "timestamp": time.time(),
                "reason": reason,
                "drift_score": drift_score
            })
            rejections = rejections[-20:]
            with open(REJECTIONS_LOG_PATH, "w", encoding="utf-8") as f:
                json.dump(rejections, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to record rejection: {e}")

    def _detect_constitutional_evasion(self, action: str) -> Tuple[bool, str]:
        """
        Detect if an action string is an evasive echo of constitutional boilerplate
        or Golden Snapshot constants designed to circumvent semantic drift scoring.
        """
        action_clean = action.strip()
        action_lower = action_clean.lower()

        # 1. Exact or near-verbatim match of PROJECT_ESSENCE phrases
        evasive_phrases = [
            "autonomous self-improving ai agent system",
            "golden snapshot",
            "standard of truth",
            "user control the user is the ultimate authority",
            "safety no destructive actions without verification",
            "clean plugin-based architecture for agents",
            "clean, plugin-based architecture for agents",
            "mobile-vibe-coding: enforce '.cursorrules'",
        ]

        norm_action = re.sub(r'[^\w\s]', ' ', action_lower)
        for phrase in evasive_phrases:
            norm_phrase = re.sub(r'[^\w\s]', ' ', phrase)
            if norm_phrase in norm_action:
                has_tech_spec = bool(re.search(r'(\.[\w]{1,4}\b|/|--|\bhttp\b|\bgit\b|\bpytest\b|\bnpm\b|\bpython\b|\btest_\b)', action_lower))
                if not has_tech_spec:
                    return True, f"Evasion Detected: Contains constitutional boilerplate ('{phrase}') without concrete operational specification."

        # 2. Token overlap with PROJECT_ESSENCE
        essence_words = set(re.findall(r'\b[a-z]{4,}\b', PROJECT_ESSENCE.lower()))
        action_words = set(re.findall(r'\b[a-z]{4,}\b', action_lower))

        if len(action_words) >= 6:
            overlap = len(essence_words.intersection(action_words))
            ratio = overlap / len(action_words)
            has_tech_spec = bool(re.search(r'(\.[\w]{1,4}\b|/|--|\bhttp\b|\bgit\b|\bpytest\b|\bnpm\b|\bpython\b|\btest_\b)', action_lower))
            if ratio >= 0.60 and not has_tech_spec:
                return True, f"Evasion Detected: {ratio:.0%} word overlap with Golden Snapshot constants. Concrete operative action required."

        return False, ""

    def _check_adversarial_substitution(self, current_action: str) -> Tuple[bool, str]:
        """
        Detect if an agent was recently blocked on an action (within 180s)
        and is now attempting to bypass the block by submitting a sanitized action.
        """
        if not os.path.exists(REJECTIONS_LOG_PATH):
            return False, ""
        try:
            with open(REJECTIONS_LOG_PATH, "r", encoding="utf-8") as f:
                rejections = json.load(f)
            if not rejections:
                return False, ""
            last_rej = rejections[-1]
            now = time.time()
            age = now - last_rej.get("timestamp", 0)
            if age < 180:
                blocked_action = last_rej.get("action", "")
                sensitive_words = ["deploy", "linkedin", "publish", "post", "social", "delete", "root", "database", "wipe"]
                had_sensitive = any(w in blocked_action.lower() for w in sensitive_words)
                curr_has_sensitive = any(w in current_action.lower() for w in sensitive_words)

                if had_sensitive and not curr_has_sensitive:
                    return True, (
                        f"Adversarial Substitution Block: Action '{blocked_action[:40]}...' was blocked {age:.0f}s ago. "
                        f"Submitting sanitized action '{current_action[:40]}...' without resolving the block is prohibited."
                    )
        except Exception:
            pass
        return False, ""

    def _check_work_log(self, action: str) -> bool:
        """
        Check if WORK_LOG.md was recently updated (within last 120 seconds)
        AND enforce strict parity between WORK_LOG.md intent and the action submitted.
        """
        if not self.work_log_path or not os.path.exists(self.work_log_path):
            self.logger.error("🛑 WORK_LOG.md not found. Required for action verification.")
            print("🛑 WORK_LOG.md not found. Update required before action.")
            return False

        mtime = os.path.getmtime(self.work_log_path)
        now = time.time()
        age_seconds = now - mtime

        if age_seconds >= 120:
            self.logger.warning(f"WORK_LOG.md is stale ({age_seconds:.1f}s old). Action must be logged recently.")
            print("🛑 WORK_LOG.md not updated recently. Required format:")
            print('   echo "🟡 Starting [ACTION]" >> WORK_LOG.md')
            return False

        try:
            tail = self._get_work_log_tail(2000)
            lines = [l.strip() for l in tail.splitlines() if l.strip()]

            latest_starting = None
            for line in reversed(lines):
                if '🟡' in line or 'starting' in line.lower():
                    latest_starting = line
                    break

            if not latest_starting:
                self.logger.warning("WORK_LOG.md does not contain '🟡' or 'Starting' indicators.")
                print("🛑 WORK_LOG.md does not contain an active '🟡 Starting' entry.")
                return False

            clean_logged = re.sub(r'^[🟡\s*\-]*(?:starting:?\s*)', '', latest_starting, flags=re.IGNORECASE).strip()
            clean_logged = re.sub(r'\s+at\s+\d{4}-\d{2}-\d{2}[T\s].*$', '', clean_logged, flags=re.IGNORECASE).strip()

            norm_logged = re.sub(r'[^\w\s]', '', clean_logged.lower()).strip()
            norm_action = re.sub(r'[^\w\s]', '', action.lower()).strip()

            logged_words = set(norm_logged.split())
            action_words = set(norm_action.split())

            is_match = False
            if norm_logged in norm_action or norm_action in norm_logged:
                is_match = True
            elif logged_words and action_words:
                overlap = len(logged_words.intersection(action_words))
                min_len = min(len(logged_words), len(action_words))
                if min_len > 0 and (overlap / min_len >= 0.50):
                    is_match = True

            if not is_match:
                msg = (
                    f"🛑 JudgeGuard: WORK_LOG PARITY VIOLATION!\n"
                    f"   Logged in WORK_LOG.md: '{clean_logged}'\n"
                    f"   Submitted for verification: '{action}'\n"
                    f"   Action description must match the active WORK_LOG entry."
                )
                self.logger.error(msg)
                print(msg)
                return False

            return True

        except Exception as e:
            self.logger.error(f"⚠️ Error reading WORK_LOG.md: {e}")
            return False

    # ------------------------------------------------------------------
    # Ground Truth Manifest — prevents context rot in long sessions
    # ------------------------------------------------------------------

    def _get_ground_truth_manifest(self) -> str:
        """
        Build a Ground Truth Manifest by combining the PROJECT_ESSENCE constant
        with the latest CONTINUITY.md state.

        This manifest is injected into every Layer 3 prompt to ensure that the
        rules of engagement are always present even in long, context-eroding sessions.

        Returns:
            str: Combined manifest text (always non-empty — falls back to
                 PROJECT_ESSENCE alone if CONTINUITY.md is unreadable).
        """
        sections = ["=== PROJECT ESSENCE (Golden Snapshot) ===", PROJECT_ESSENCE]

        # Attempt to pull the active goal from CONTINUITY.md
        continuity_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cm", "CONTINUITY.md"),
            os.path.join(os.path.expanduser("~"), "judge", "judge-guard-core", ".cm", "CONTINUITY.md"),
        ]
        for path in continuity_paths:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    # Extract only the Active Goal + Key Decisions sections (token-light)
                    relevant = []
                    capture = False
                    for line in content.splitlines():
                        if line.startswith("## Active Goal") or line.startswith("## Key Decisions"):
                            capture = True
                        elif line.startswith("## ") and capture:
                            capture = False
                        if capture:
                            relevant.append(line)
                    if relevant:
                        sections.append("\n=== ACTIVE CONTINUITY (Working Memory) ===")
                        sections.append("\n".join(relevant[:30]))  # cap at 30 lines
                    break
                except Exception as e:
                    self.logger.warning(f"Ground Truth Manifest: Could not read CONTINUITY.md: {e}")

        return "\n".join(sections)

    # ------------------------------------------------------------------
    # Self-Healing Loop
    # ------------------------------------------------------------------

    def retry_with_guidance(
        self,
        action: str,
        reason: str,
        max_retries: int = 2,
    ) -> dict:
        """
        Self-Healing Loop: given a rejected action and the rejection reason,
        attempt to guide the actor toward a revised, compliant action.

        This implements the Actor-Judge feedback cycle from AGENT_TAMING_GUIDE.md:
            while attempt < max_retries:
                result = actor.act(context)
                if judge.verify(result): return result
                context['feedback'] = judge.get_reason()

        Args:
            action: The original rejected action description.
            reason: The human-readable rejection reason from JudgeGuard.
            max_retries: Maximum revision attempts (default: 2).

        Returns:
            dict with keys:
              - retry (bool): True if a viable revision was produced.
              - revised_action (str): Suggested revised action (present when retry=True).
              - reason (str): Explanation of the outcome.
        """
        self._ensure_setup()

        # Hard-blocked actions — no retry possible
        if self._is_dangerous_command(action):
            return {
                "retry": False,
                "reason": "Action is categorically blocked (Layer 00 — dangerous command). No revision possible.",
            }

        # Try to produce a guidance-based revision
        manifest = self._get_ground_truth_manifest()
        prompt = f"""You are a Self-Healing Agent Advisor.

An action was REJECTED by JudgeGuard for the following reason:
  REASON: {reason}

ORIGINAL ACTION: {action}

GROUND TRUTH MANIFEST (project constraints):
{manifest[:2000]}

TASK:
Suggest a REVISED version of the action that:
1. Achieves the same underlying goal
2. Complies with the Ground Truth Manifest
3. Has a drift score below 0.40

Reply with ONLY the revised action text (1-2 sentences). If no compliant revision is possible, reply exactly: NO_REVISION_POSSIBLE
"""

        for attempt in range(1, max_retries + 1):
            try:
                if not self.gemini or not getattr(self.gemini, "has_keys", False):
                    # Offline: produce a heuristic guidance message
                    heuristic = (
                        f"[Heuristic guidance] Revise '{action}' to focus on "
                        "agent safety, code quality, or system transparency — "
                        "core project values — rather than the rejected goal."
                    )
                    return {
                        "retry": True,
                        "revised_action": heuristic,
                        "reason": f"Offline heuristic guidance (attempt {attempt}/{max_retries}).",
                    }

                raw = self.gemini.generate_content(
                    prompt,
                    generation_config={"max_output_tokens": 120},
                )

                if not raw or "NO_REVISION_POSSIBLE" in raw.upper():
                    continue  # try next attempt

                revised = raw.strip()
                return {
                    "retry": True,
                    "revised_action": revised,
                    "reason": f"Self-healing guidance produced on attempt {attempt}/{max_retries}.",
                }

            except Exception as e:
                self.logger.warning(f"Self-healing attempt {attempt} failed: {e}")

        return {
            "retry": False,
            "reason": f"Self-healing exhausted {max_retries} attempts without a viable revision.",
        }

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
        # Ensure we have environment and logger
        self._ensure_setup()

        # ⚡ Bolt: Lazy import bridge to avoid early 'requests' load
        try:
            from src.antigravity_core.mobile_bridge import bridge
            bridge_available = True
        except ImportError:
            bridge_available = False

        # --- LAYER 00: Security Enforcement (Emergency Fix) ---
        if self._is_dangerous_command(current_action):
            msg = "Security Violation: Action contains forbidden dangerous commands (sudo/root deletion)."
            self.logger.error(f"Layer 00 Block: {msg}")
            self._record_rejection(current_action, msg)
            if bridge_available:
                bridge.push_verdict(current_action, "BLOCKED", msg)
            print(f"🛑 JudgeGuard: {msg}")
            return False

        # --- LAYER 0.01: Constitutional Evasion & Echo Detection ---
        is_evasive, evasion_msg = self._detect_constitutional_evasion(current_action)
        if is_evasive:
            self.logger.error(f"Layer 0.01 Block: {evasion_msg}")
            self._record_rejection(current_action, evasion_msg)
            if bridge_available:
                bridge.push_verdict(current_action, "BLOCKED", evasion_msg)
            print(f"🛑 JudgeGuard: {evasion_msg}")
            return False

        # --- LAYER 0.02: Adversarial Substitution Detection ---
        is_sub, sub_msg = self._check_adversarial_substitution(current_action)
        if is_sub:
            self.logger.error(f"Layer 0.02 Block: {sub_msg}")
            self._record_rejection(current_action, sub_msg)
            if bridge_available:
                bridge.push_verdict(current_action, "BLOCKED", sub_msg)
            print(f"🛑 JudgeGuard: {sub_msg}")
            return False

        # --- LAYER 0: Work Log Enforcement & Strict Parity ---
        # ⚡ Bolt: Fast-fail before expensive context loading/LLM calls
        if not self._check_work_log(current_action):
            self._record_rejection(current_action, "Work log parity or freshness check failed.")
            return False

        # --- LAYER 0.1: Verdict Caching (⚡ Bolt) ---
        # Caching is disabled for all actions to prevent bypass via stale approvals.
        # This ensures every action is freshly evaluated against the latest policies.
        # (If needed in the future, caching can be reintroduced with strict cryptographic binding.)

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
        is_shell_command = "run_command" in current_action or "shell" in current_action.lower()
        
        if is_research_phase and is_shell_command:
            msg = "Violation: You must use the Browser Agent for research tasks (Phase 0-1)."
            self.logger.warning(f"Layer 1 Block: {msg}")
            self._record_rejection(current_action, msg)
            if bridge_available:
                bridge.push_verdict(current_action, "BLOCKED", msg)
            print(f"🛑 JudgeGuard: {msg}")
            return False

        # --- CONSOLIDATED VERIFICATION (⚡ Bolt: Merge Layer 3 and Standard) ---
        is_write = self._is_write_operation(current_action)
        self.logger.info(f"Consolidated Verification (Write: {is_write})...")

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

        # Inject Ground Truth Manifest into criteria for context-rot prevention
        ground_truth = self._get_ground_truth_manifest()
        criteria_parts.append(f"\n5. GROUND TRUTH MANIFEST (always-active rules):\n{ground_truth[:1500]}")
        criteria = "\n".join(criteria_parts)

        judge = BlockJudge(criteria, client=self.gemini)
        result = judge.evaluate_with_score(f"ACTION: {current_action}")

        passed = result["passed"]
        drift_score = result.get("drift_score", 0.0)
        reason = result.get("reason", "")

        print(f"📊 Drift Score: {drift_score:.2f} / 1.00  (threshold: 0.40)")
        self.logger.info(f"Drift Score: {drift_score:.4f} | Passed: {passed} | Reason: {reason}")

        if passed:
            print(f"✅ JudgeGuard: Action '{current_action}' APPROVED.")
            if bridge_available:
                bridge.push_verdict(current_action, "PASSED", "Approved (Unified Verification)")

            # 🎫 Layer 4: Issue Cryptographic Single-Use Execution Ticket
            try:
                from src.antigravity_core.ticket_vault import get_ticket_vault
                vault = get_ticket_vault()
                ticket = vault.issue_ticket(current_action, ttl_seconds=60)
                ticket_id = ticket.get("ticket_id")
                print(f"🎫 JudgeGuard: Execution Ticket issued -> {ticket_id} (TTL: 60s)")
                os.environ["JUDGE_EXECUTION_TICKET"] = ticket_id
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to issue execution ticket: {e}")

            # ⚡ Bolt: Cache verdict ONLY for read/safe operations
            if not is_write and self.pipeline:
                self.pipeline.cache_verdict(current_action, "PASSED")

            # ⚡ Bolt: Auto-sync to Notion if this is a research action (Fix: restored missing call)
            if self._is_research_action(current_action):
                self._sync_to_notion(current_action)
            
            return True
        else:
            msg = f"Violation detected (Master Orchestration or Project Essence). Drift: {drift_score:.2f}"
            self._record_rejection(current_action, msg, drift_score)
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

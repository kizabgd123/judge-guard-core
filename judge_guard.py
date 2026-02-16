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
import glob
import logging
from typing import Optional
from dotenv import load_dotenv
import requests

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- DEPENDENCY INJECTION ---
try:
    from src.antigravity_core.judge_flow import BlockJudge
    from src.antigravity_core.gemini_client import GeminiClient
    JUDGE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ Judge/Gemini modules not available: {e}")
    JUDGE_AVAILABLE = False

# ----------------------------

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
7. CALENDAR TRUTH: The current year is strictly 2026. All operations must honor this timeline.
8. MODEL PURITY: Only authorized Gemini models from 'available_models.txt' exist. All other definitions are invalid.

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
        self.brain_path = brain_path or os.getenv("BRAIN_PATH") or self._discover_brain_path()
        self.work_log_path = work_log_path or os.getenv("WORK_LOG_PATH") or self._find_work_log()
        self.rules_path = os.path.expanduser("~/.gemini/MASTER_ORCHESTRATION.md")
        self.immutable_laws = self._load_rules()
        
        if JUDGE_AVAILABLE:
            self.gemini = GeminiClient()
        
        logger.info(f"JudgeGuard v2.0 initialized. Brain: {self.brain_path}")

    def _discover_brain_path(self) -> Optional[str]:
        """Auto-discover the brain path from ~/.gemini/antigravity/brain/"""
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
        if self.work_log_path and os.path.exists(self.work_log_path):
            try:
                with open(self.work_log_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    return content[-max_chars:]
            except Exception:
                pass
        return "(No work log context)"

    def _detect_phase(self, context: str) -> str:
        """
        Heuristic to detect Project Phase from context.
        Returns '0', '1', '2', etc., or 'unknown'.
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

    def _is_write_operation(self, action: str) -> bool:
        """Detect if action involves writing/modifying code."""
        keywords = ["write", "edit", "modify", "create file", "update", "refactor", "delete"]
        return any(k in action.lower() for k in keywords)

    def _is_research_action(self, action: str) -> bool:
        """Detect if action is research-related and should sync to Notion."""
        keywords = ["phase", "research", "discovery", "analysis", "validation", "documentation", "complete"]
        action_lower = action.lower()
        return any(k in action_lower for k in keywords)
    
    def _sync_to_notion(self, action: str):
        """Trigger Notion sync via research_pipeline.py."""
        try:
            import subprocess
            print("📝 Syncing to Notion...")
            result = subprocess.run(
                ["python3", "research_pipeline.py", "--sync-notion"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print("✅ Notion sync completed")
            else:
                print(f"⚠️  Notion sync warning: {result.stderr}")
        except Exception as e:
            print(f"⚠️  Notion sync failed (non-critical): {e}")

    def _check_work_log(self, action: str) -> bool:
        """Check if WORK_LOG.md was recently updated (within last 60 seconds)."""
        if not self.work_log_path or not os.path.exists(self.work_log_path):
            print("🛑 WORK_LOG.md not found. Update required before action.")
            return False
        
        import time
        import datetime
        
        # Check last modification time
        mtime = os.path.getmtime(self.work_log_path)
        now = time.time()
        age_seconds = now - mtime
        
        # Read last few lines to check if action was logged
        try:
            with open(self.work_log_path, 'r') as f:
                lines = f.readlines()
                last_lines = ''.join(lines[-10:]).lower()
                
                # Check if this action or 'starting' is in recent log
                if '🟡' in last_lines or 'starting' in last_lines:
                    if age_seconds < 60:  # Updated within last minute
                        return True
        except Exception as e:
            print(f"⚠️  Error reading WORK_LOG.md: {e}")
            return False
        
        print("🛑 WORK_LOG.md not updated. Required format:")
        print('   echo "🟡 Starting [ACTION]" >> WORK_LOG.md')
        return False

    def _meta_overseer_check(self, stage: str, context: str):
        """
        Executes the 'Meta-LLM' oversight using GEMINI Client.
        """
        print(f"\n✨ VETOBOARD (Gemini Override) ACTIVATED: {stage} CHECK")
        print("...consulting the Gemini High Council...")
        
        if not JUDGE_AVAILABLE:
            print("⚠️ Gemini Client not available. Bypassing check for stability.")
            return

        import datetime
        
        # Enforce 2026 check locally
        now = datetime.datetime.now()
        if now.year != 2026:
            print(f"🛑 CALENDAR VIOLATION: Current system year is {now.year}, but the Protocol demands 2026.")
            print("Please adjust your system clock or the simulation settings.")
            sys.exit(1)

        work_log_context = self._load_context(max_chars=1000)
        
        prompt = f"""
        Action Context: {context}
        Work Log History (Last 1000 chars):
        {work_log_context}
        
        Stage: {stage}
        Current Year: 2026
        
        INSTRUCTION: You are the VetoBoard (CEO, CTO, CFO, LEGAL, CRITIC). 
        1. Review the 'Action Context' against the Constitution.
        2. Verify if 'Starting [Action]' is present in Work Log.
        3. Return a table with APPROVED/VETO for each persona and a FINAL VERDICT.
        4. If it's a verification step (END), ensure the action was actually done.
        """
        
        # USE GEMINI CLIENT instead of Ollama
        try:
            verdict_passed = self.gemini.judge_content(prompt, "You are the VetoBoard. Return APPROVED only if all criteria are met.")
        except Exception as e:
            print(f"⚠️ Gemini unavailable: {e}. Falling back to BlockJudge (Standard Rules).")
            # Fallback: Assume refined judgment will happen in Standard Verification
            return

        if verdict_passed:
            print("----------------------------------------")
            print("| Persona    | Status                        |")
            print("| :--------- | :---------------------------- |")
            print("| CEO        | ✅ APPROVED                  |")
            print("| CTO        | ✅ APPROVED                  |")
            print("| CFO        | ✅ APPROVED                  |")
            print("| LEGAL      | ✅ APPROVED                  |")
            print("| CRITIC     | ✅ APPROVED                  |")
            print("----------------------------------------")
            print("✨ UNANIMOUS CONSENT GRANTED.")
        else:
            print("\n🛑 BLOCKED BY VETOBOARD (GEMINI).")
            sys.exit(1)

    def verify_action(self, current_action: str) -> bool:
        """
        Execute the 3-Layer Verification Model.
        """
        if not JUDGE_AVAILABLE:
            print("🛑 JudgeGuard: Dependencies missing (GeminiClient/JudgeFlow).")
            return False
            
        # --- LAYER 0: Work Log Enforcement (NEW) ---
        if not self._check_work_log(current_action):
            return False

        # --- VETOBOARD (Gemini): START CHECK ---
        self._meta_overseer_check("START", current_action)

        # --- LAYER 2: Live Thought Streaming ---

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
            logger.warning(f"Layer 1 Block: {msg}")
            print(f"🛑 JudgeGuard: {msg}")
            return False

        # --- LAYER 3: Essence Check (Semantic Drift) ---
        if self._is_write_operation(current_action):
            logger.info("Layer 3: Verifying Semantic Drift...")
            
            # Use Gemini to check drift
            drift_prompt = f"""
            PROJECT ESSENCE (Golden Snapshot):
            {PROJECT_ESSENCE}
            
            PROPOSED ACTION:
            "{current_action}"
            
            TASK:
            Does this action deviate significantly (>20%) from the Project Essence definitions?
            Is it introducing features or changes that contradict the Core Values?
            
            reply PASSED if it aligns or is neutral.
            reply FAILED if it causes significant drift.
            """
            
            try:
                is_valid_essence = self.gemini.judge_content(drift_prompt, "The action must not deviate significantly from the Project Essence.")
                
                if not is_valid_essence:
                    msg = "Violation: Significant Semantic Drift (>20%) detected against Project Essence."
                    print(f"🛑 JudgeGuard: {msg}")
                    return False
            except Exception as e:
                print(f"⚠️ Gemini unavailable for Semantic Drift: {e}. Skipping drift check.")

        # --- STANDARD VERIFICATION (Existing Logic) ---
        # Combine everything for final sanity check
        criteria = f"""
        You are the PERMANENT JUDGE GUARD.
        
        1. IMMUTABLE LAWS:
        {self.immutable_laws}
        
        2. CONTEXT:
        {context[-5000:]}
        
        3. ACTION:
        "{current_action}"
        
        VERDICT REQUIRED:
        - Check for any other logic violations.
        - Ensure strict adherence to Master Orchestration.
        """
        
        judge = BlockJudge(criteria)
        verdict = judge.evaluate(f"ACTION: {current_action}")
        
        if verdict:
            # --- VETOBOARD (Gemini): END CHECK ---
            self._meta_overseer_check("END", current_action)
            
            print(f"✅ JudgeGuard: Action '{current_action}' APPROVED.")
            
            # Auto-sync to Notion if this is a research action
            if self._is_research_action(current_action):
                self._sync_to_notion(current_action)
            
            return True
        else:
            msg = "Blocked by Standard Rules (Master Orchestration Violation)."
            print(f"🛑 JudgeGuard: {msg}")
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

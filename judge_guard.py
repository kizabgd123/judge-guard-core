"""
JudgeGuard - The Permanent Guardian of the Antigravity System.
Verifies every critical step against the 'Standard of Truth'.

Environment Variables:
    BRAIN_PATH: Path to the brain directory (optional, auto-discovers if not set)
    WORK_LOG_PATH: Path to the work log file (optional, defaults to ./WORK_LOG.md)
"""

import os
import sys
import glob
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Graceful import with fallback
try:
    from src.antigravity_core.judge_flow import BlockJudge, JudgeFlowBlock
    JUDGE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ BlockJudge not available: {e}")
    JUDGE_AVAILABLE = False
    BlockJudge = None


class JudgeGuard:
    """
    The Permanent Guardian of the Antigravity System.
    Verifies every critical step against the 'Standard of Truth'.
    """
    
    def __init__(self, brain_path: Optional[str] = None, work_log_path: Optional[str] = None):
        """
        Initialize JudgeGuard with configurable paths.
        
        Args:
            brain_path: Override for brain directory path
            work_log_path: Override for work log file path
        """
        # Priority: argument > env var > auto-discovery
        self.brain_path = brain_path or os.getenv("BRAIN_PATH") or self._discover_brain_path()
        self.work_log_path = work_log_path or os.getenv("WORK_LOG_PATH") or self._find_work_log()
        
        # Rules file path
        # Fallback to global MASTER_ORCHESTRATION if local brain rules missing
        self.rules_path = os.path.expanduser("~/.gemini/MASTER_ORCHESTRATION.md")
        
        # Load the immutable laws
        self.immutable_laws = self._load_rules()
        
        logger.info(f"JudgeGuard initialized. Brain: {self.brain_path}, WorkLog: {self.work_log_path}")

    def _discover_brain_path(self) -> Optional[str]:
        """Auto-discover the brain path from ~/.gemini/antigravity/brain/"""
        try:
            base_path = os.path.expanduser("~/.gemini/antigravity/brain")
            if not os.path.exists(base_path):
                logger.warning(f"Brain base path not found: {base_path}")
                return None
            
            # Find the most recently modified brain directory (UUID format)
            brain_dirs = glob.glob(os.path.join(base_path, "*-*-*-*-*"))
            if not brain_dirs:
                logger.warning("No brain directories found")
                return None
            
            # Return most recently modified
            latest = max(brain_dirs, key=os.path.getmtime)
            logger.info(f"Auto-discovered brain path: {latest}")
            return latest
            
        except Exception as e:
            logger.error(f"Error discovering brain path: {e}")
            return None

    def _find_work_log(self) -> str:
        """Find WORK_LOG.md in current directory or parent directories."""
        search_paths = [
            os.getcwd(),
            os.path.dirname(os.path.abspath(__file__)),
            os.path.expanduser("~/Desktop/JEDNOOOOOOOOOOOOOOOOOOM"),
        ]
        
        for path in search_paths:
            work_log = os.path.join(path, "WORK_LOG.md")
            if os.path.exists(work_log):
                return work_log
        
        # Default fallback
        return os.path.join(os.getcwd(), "WORK_LOG.md")

    def _load_rules(self) -> str:
        """Safely load the immutable rules."""
        if not self.rules_path:
            return "⚠️ BRAIN_PATH not configured. Rules not loaded."
        
        try:
            if os.path.exists(self.rules_path):
                with open(self.rules_path, "r", encoding="utf-8") as f:
                    return f.read()
            else:
                logger.warning(f"Rules file not found: {self.rules_path}")
                return "⚠️ GOAL_SETTING_RULES.md not found. Operating without rules."
        except IOError as e:
            logger.error(f"Error reading rules: {e}")
            return f"❌ ERROR loading rules: {e}"

    def _load_context(self, max_chars: int = 2000) -> str:
        """Safely load recent work log context."""
        try:
            if self.work_log_path and os.path.exists(self.work_log_path):
                with open(self.work_log_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    return content[-max_chars:] if len(content) > max_chars else content
            return "(No work log found)"
        except IOError as e:
            logger.error(f"Error reading work log: {e}")
            return f"(Error reading work log: {e})"

    def verify_action(self, current_action: str) -> bool:
        """
        Verifies if the CURRENT ACTION is compliant with the GOLDEN RULES and WORKFLOW.
        
        Args:
            current_action: Description of the action to verify
            
        Returns:
            True if action passes verification, False otherwise
        """
        if not JUDGE_AVAILABLE:
            logger.error("❌ BlockJudge not available. Cannot verify action.")
            print("🛑 JudgeGuard: BlockJudge module not available. Install dependencies.")
            return False

        log_context = self._load_context()

        criteria = f"""
        You are the PERMANENT JUDGE GUARD.
        
        1. THE IMMUTABLE LAWS (Expert Wisdom):
        {self.immutable_laws}
        
        2. CONTEXT (Recent Work Log):
        {log_context}
        
        3. THE ACTION TO JUDGE:
        "{current_action}"
        
        VERDICT REQUIRED:
        - Does this action violate any Rule (e.g., 10/90, 48h, Written Inscription)?
        - Is it a logical next step?
        - Is the 'Definition of Done' met if this action claims completion?
        
        CRITICAL: Check if the Work Log shows readiness for this action.
        If proposing "Phase X", the Log must show "Phase X-1 Complete" or "Starting Phase X".
        
        Output 'PASSED' only if strict compliance is observed.
        Output 'FAILED' and the reason if not.
        """
        
        try:
            judge = BlockJudge(criteria)
            verdict = judge.evaluate(f"ACTION: {current_action}")
            
            if verdict:
                print(f"✅ JudgeGuard: Action '{current_action}' APPROVED.")
                return True
            else:
                print(f"🛑 JudgeGuard: Action '{current_action}' BLOCKED.")
                return False
                
        except Exception as e:
            logger.error(f"Error during verification: {e}")
            print(f"❌ JudgeGuard Error: {e}")
            return False


def main():
    """CLI entry point for JudgeGuard."""
    if len(sys.argv) < 2:
        print("Usage: python3 judge_guard.py '<action_description>'")
        print("\nEnvironment Variables:")
        print("  BRAIN_PATH     - Path to brain directory")
        print("  WORK_LOG_PATH  - Path to WORK_LOG.md")
        sys.exit(1)
        
    action = sys.argv[1]
    guard = JudgeGuard()
    
    if not guard.verify_action(action):
        sys.exit(1)


if __name__ == "__main__":
    main()

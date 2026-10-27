import logging
from typing import Dict, Any, Callable, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from src.antigravity_core.gemini_client import GeminiClient

# Drift threshold from AGENT_TAMING_GUIDE.md and Phase 2 decision matrix
DRIFT_THRESHOLD = 0.40


class BlockJudge:
    """
    Evaluates content using Real Gemini AI.
    """
    def __init__(self, criteria: str, client: Optional[GeminiClient] = None):
        self.criteria = criteria
        # ⚡ Bolt: Allow dependency injection of GeminiClient to avoid redundant initialization
        self.client = client or GeminiClient()

    def evaluate(self, content: str) -> bool:
        """
        Calls Gemini to judge the content.
        """
        logger.info(f"Judging context against criteria: {self.criteria}")
        return self.client.judge_content(content, self.criteria)

    def evaluate_with_score(self, content: str) -> Dict[str, Any]:
        """
        Structured verdict combining pass/fail, numeric drift score, and reason.

        Extends evaluate() with an explicit drift_score (0.0–1.0) produced by
        DriftScorer. If drift_score > DRIFT_THRESHOLD (0.40), the verdict is
        forced to failed regardless of the LLM verdict.

        Args:
            content: The action/content string to evaluate.

        Returns:
            dict with keys:
              - passed (bool): True if action is approved.
              - drift_score (float): 0.0 (aligned) → 1.0 (total drift).
              - reason (str): Human-readable explanation.
        """
        # --- Drift Score ---
        drift_score = 0.0
        try:
            from src.antigravity_core.drift_scorer import DriftScorer
            from judge_guard import PROJECT_ESSENCE
            scorer = DriftScorer(client=self.client)
            drift_score = scorer.score(action=content, essence=PROJECT_ESSENCE)
        except Exception as e:
            logger.warning(f"BlockJudge: DriftScorer unavailable ({e}), defaulting drift_score=0.0")

        # --- Hard drift rejection ---
        if drift_score > DRIFT_THRESHOLD:
            reason = (
                f"Action exceeds drift threshold ({drift_score:.2f} > {DRIFT_THRESHOLD}). "
                "Semantic content diverges too far from project essence."
            )
            logger.warning(f"BlockJudge: Drift rejection — {reason}")
            return {"passed": False, "drift_score": drift_score, "reason": reason}

        # --- Standard LLM/deterministic verdict ---
        try:
            passed = self.client.judge_content(content, self.criteria)
        except Exception as e:
            logger.error(f"BlockJudge: judge_content failed ({e}), defaulting to False")
            passed = False

        if passed:
            reason = f"Action approved. Drift score: {drift_score:.2f} (within threshold)."
        else:
            reason = "Action failed criteria check (Immutable Laws or Project Essence)."

        return {"passed": passed, "drift_score": drift_score, "reason": reason}

    def generate_report(self, content: str) -> str:
        """
        Generates a detailed audit report combining criteria and content.
        """
        logger.info("Generating detailed audit report...")
        full_prompt = f"{self.criteria}\n\nUSER ACTION/CONTEXT: {content}"
        return self.client.generate_content(full_prompt)

class JudgeFlowBlock:
    """
    A self-correcting workflow block.
    Executes an action, judges the result, and retries if necessary.
    """
    def __init__(self, action_agent: Callable[[Dict[str, Any]], str], judge_agent: BlockJudge, max_retries: int = 3):
        self.action = action_agent
        self.judge = judge_agent
        self.max_retries = max_retries

    def execute(self, context: Dict[str, Any]) -> str:
        """
        Executes the block with self-correction loop.
        """
        for attempt in range(1, self.max_retries + 1):
            logger.info(f"Attempt {attempt}/{self.max_retries}")
            
            try:
                result = self.action(context)
                
                if self.judge.evaluate(result):
                    logger.info("JudgeFlow: Content PASSED verification.")
                    return result
                
                logger.warning("JudgeFlow: Content FAILED verification.")
                # Add feedback to context for next attempt
                context['feedback'] = f"Attempt {attempt} failed criteria: {self.judge.criteria}"
                
            except Exception as e:
                logger.error(f"Error during execution: {e}")
                context['feedback'] = f"Error: {str(e)}"

        raise Exception(f"JudgeFlowBlock failed after {self.max_retries} retries.")

# Example usage function
def create_block(action_func: Callable, criteria: str) -> JudgeFlowBlock:
    judge = BlockJudge(criteria)
    return JudgeFlowBlock(action_func, judge)

import logging
from typing import Dict, Any, Callable, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from src.antigravity_core.gemini_client import GeminiClient

class BlockJudge:
    """
    Evaluates content using Real Gemini AI.
    """
    def __init__(self, criteria: str):
        self.criteria = criteria
        self.client = GeminiClient()

    def evaluate(self, content: str) -> bool:
        """
        Calls Gemini to judge the content.
        """
        logger.info(f"Judging context against criteria: {self.criteria}")
        return self.client.judge_content(content, self.criteria)

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

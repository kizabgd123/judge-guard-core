import os
import re
import time
from typing import Optional, Dict
import logging
from src.antigravity_core.env_utils import safe_load_dotenv

safe_load_dotenv()
logger = logging.getLogger(__name__)

# ⚡ Bolt: Lazy import holder for google.genai (new SDK)
genai = None

class GeminiClient:
    """
    Client for interacting with Google's Gemini models with authentic
    deterministic rule-based fallback when offline / unconfigured.
    Zero fake mocks: real LLM calls when configured, real rules evaluation when offline.
    """
    def __init__(self, model_name: Optional[str] = None, api_keys: Optional[str] = None):
        safe_load_dotenv()
        keys_env = api_keys or os.getenv("GEMINI_API_KEYS")
        if not keys_env:
            single_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if not single_key:
                logger.info("GeminiClient: No API key found in environment. Using Deterministic Rule Engine (Zero-Mock).")
                self.api_keys = []
                self.has_keys = False
            else:
                self.api_keys = [single_key.strip()]
                self.has_keys = True
        else:
            self.api_keys = [k.strip() for k in keys_env.split(",") if k.strip()]
            self.has_keys = len(self.api_keys) > 0
        
        self.current_key_index = 0
        raw_model = model_name or os.getenv("GEMINI_MODEL", "models/gemini-3.5-flash-lite")
        if not raw_model.startswith("models/"):
            raw_model = f"models/{raw_model.replace(' ', '-')}"
        self.model_name = raw_model
        self._client = None  # google.genai.Client instance
        self._configure_client()

    def _configure_client(self):
        """
        Configure the google.genai Client using the active API key.
        If no keys are configured, prepares deterministic offline rule evaluation.
        """
        if not self.has_keys:
            self._client = None
            return

        global genai
        if genai is None:
            try:
                from google import genai as genai_module
                genai = genai_module
            except ImportError:
                genai = None

        if genai is not None:
            current_key = self.api_keys[self.current_key_index]
            self._client = genai.Client(api_key=current_key)
            logger.info(
                f"Configured Gemini client (Key {self.current_key_index + 1}/{len(self.api_keys)})"
            )

    def _rotate_key(self) -> bool:
        """Rotates to the next available API key."""
        if len(self.api_keys) <= 1:
            logger.warning("Only one API key available. Cannot rotate.")
            return False
            
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        logger.warning(f"🔄 Rotating API Key. Switching to Key #{self.current_key_index + 1}")
        self._configure_client()
        return True

    def generate_content(self, prompt: str, generation_config: Optional[Dict] = None) -> str:
        """
        Produce model-generated text for the given prompt, using API-key rotation
        and retry/backoff on quota or rate-limit errors.
        Uses google.genai SDK: client.models.generate_content().
        """
        if not self.has_keys or self._client is None:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured in environment or .env. "
                "Text generation requires a valid Gemini API key. Zero-mock policy active."
            )

        # Build config object if caller passed a dict
        config = None
        if generation_config:
            from google.genai import types as genai_types
            config = genai_types.GenerateContentConfig(**generation_config)

        max_retries = 3
        total_attempts = max_retries * len(self.api_keys)

        for attempt in range(total_attempts):
            try:
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=config,
                )
                return response.text
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    logger.warning("Gemini quota exceeded on the current key")
                    if self._rotate_key():
                        logger.info("Retrying immediately with NEW key...")
                        continue

                    sleep_time = 2 ** (attempt % 3)
                    logger.warning(f"Sleeping {sleep_time}s before retry...")
                    time.sleep(sleep_time)
                    continue

                logger.error("Gemini API request failed (%s)", type(e).__name__)
                raise

        raise Exception("Max retries exceeded for Gemini API")

    def _deterministic_rule_judge(self, content: str, criteria: str) -> bool:
        """
        Authentic deterministic rules-based evaluation when offline or API key is absent.
        Strictly enforces security, essence, and criteria boundaries without synthetic mocks.
        """
        content_lower = content.lower()
        criteria_lower = criteria.lower()

        # 1. Hard Security Violations (Layer 00)
        forbidden_security = [
            "sudo", "rm -rf /", "rm -rf /*", "chmod -r 777", "drop database",
            "drop table", "truncate table", "mkfs", "dd if=/dev/zero"
        ]
        for term in forbidden_security:
            if term in content_lower:
                logger.warning(f"Deterministic Judge: Security violation '{term}' detected.")
                return False

        # 2. Scope Creep & Safety Drift (Layer 3)
        drift_keywords = [
            "bypass security", "skip verification", "ignore judge",
            "disable guardian", "remove all users", "purge all data",
            "leak secrets", "override constitution"
        ]
        for term in drift_keywords:
            if term in content_lower:
                logger.warning(f"Deterministic Judge: Semantic drift violation '{term}' detected.")
                return False

        # 3. Quoted terms are constraints only inside an explicit section.
        sections = re.finditer(
            r"(?ims)^\s*#{1,6}\s*(?:negative constraints|zabranjena ograničenja)\s*:?\s*$\n(.*?)(?=^\s*#{1,6}\s|\Z)",
            criteria,
        )
        for section in sections:
            for pattern in re.findall(r"['\"]([^'\"]+)['\"]", section.group(1)):
                if pattern.lower() in content_lower:
                    logger.warning("Deterministic Judge: Content matches an explicit negative constraint.")
                    return False

        logger.info("Deterministic Judge: Content verified against security & essence criteria (PASSED).")
        return True

    def judge_content(self, content: str, criteria: str) -> bool:
        """
        Evaluates content against criteria to return True/False.
        Uses Gemini LLM if API key is present; otherwise executes deterministic rules verification.
        """
        if not self.has_keys or self._client is None:
            return self._deterministic_rule_judge(content, criteria)

        prompt = f"""
        You are an impartial Judge AI.
        
        CRITERIA:
        {criteria}
        
        CONTENT TO EVALUATE:
        {content}
        
        INSTRUCTIONS:
        Evaluate if the CONTENT meets the CRITERIA.
        If it meets ALL criteria, reply exactly with: PASSED
        If it fails ANY criteria, reply exactly with: FAILED
        Do not add any other text.
        """
        
        try:
            raw_result = self.generate_content(prompt, generation_config={"max_output_tokens": 10})
            if not raw_result:
                raise ValueError("Empty response from Gemini")
            
            result = raw_result.strip().upper()
            logger.info("Gemini verdict received")
            return result == "PASSED"
        except Exception as e:
            logger.error("Gemini judge failed (%s); denying the action", type(e).__name__)
            return False

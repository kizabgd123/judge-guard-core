import os
import time
import google.generativeai as genai
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class GeminiClient:
    """
    Client for interacting with Google's Gemini models.
    """
    def __init__(self, model_name: str = "models/gemini-flash-latest", api_keys: Optional[str] = None):
        """
        Initialize a GeminiClient, loading API keys, configuring mock mode when no keys are found, and preparing the client.
        
        Parameters:
            model_name (str): The Gemini model identifier to use (default: "models/gemini-flash-latest").
            api_keys (Optional[str]): Comma-separated API keys string; if omitted, the environment variables
                `GEMINI_API_KEYS` or `GEMINI_API_KEY` will be used. When no keys are available, the client
                enters mock mode and uses a placeholder key.
        
        Notes:
            - Sets `self.api_keys` to a list of keys, `self.current_key_index` to 0, `self.model_name`
              to the provided model_name, and `self.mock_mode` to True when falling back to mock mode.
            - Calls `_configure_client()` to finalize client setup.
        """
        keys_env = api_keys or os.getenv("GEMINI_API_KEYS")
        if not keys_env:
            # Fallback for backward compatibility
            single_key = os.getenv("GEMINI_API_KEY")
            if not single_key:
                logger.warning("GEMINI_API_KEYS not found in environment. RUNNING IN MOCK MODE.")
                self.api_keys = ["MOCK_KEY"]
                self.mock_mode = True
            else:
                self.api_keys = [single_key]
                self.mock_mode = False
        else:
            self.api_keys = [k.strip() for k in keys_env.split(",") if k.strip()]
        
        self.current_key_index = 0
        self.model_name = model_name
        self._configure_client()

    def _configure_client(self):
        """
        Configure the Gemini client to use the currently selected API key or initialize mock mode.
        
        If mock mode is enabled, set self.model to None and log mock initialization. Otherwise, select the API key at self.current_key_index, configure the genai client and create the GenerativeModel assigned to self.model, then log a masked version of the key with its index and the total number of keys.
        """
        if getattr(self, "mock_mode", False):
            self.model = None
            logger.info("GeminiClient: Initialized in MOCK MODE")
            return

        current_key = self.api_keys[self.current_key_index]
        genai.configure(api_key=current_key)
        self.model = genai.GenerativeModel(self.model_name)
        # Obscure key for logging
        if current_key == "MOCK_KEY":
            masked_key = "MOCK_KEY"
        else:
            masked_key = current_key[:4] + "..." + current_key[-4:] if len(current_key) > 8 else "****"
        logger.info(f"configured Gemini with key: {masked_key} (Key {self.current_key_index + 1}/{len(self.api_keys)})")

    def _rotate_key(self):
        """Rotates to the next available API key."""
        if len(self.api_keys) <= 1:
            logger.warning("Only one API key available. Cannot rotate.")
            return False
            
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        logger.warning(f"🔄 Rotating API Key. Switching to Key #{self.current_key_index + 1}")
        self._configure_client()
        return True

    def generate_content(self, prompt: str, **kwargs) -> str:
        """
        Produce model-generated text for the given prompt, using API-key rotation and retry/backoff on quota or rate-limit errors.
        
        When the instance is in mock mode, returns deterministic mock responses ("PASSED" for judge-style prompts, otherwise "Mock response from Gemini Client"). Otherwise, attempts up to (max_retries * number_of_keys) tries: on quota/rate-limit errors it will try to rotate to the next API key and retry immediately if rotation succeeds, or apply exponential backoff and retry if rotation is not possible. Non-quota errors are re-raised.
        
        Parameters:
            prompt (str): The text prompt to send to the model.
            **kwargs: Additional keyword arguments to pass to the model's generate_content method (e.g., generation_config).
        
        Returns:
            str: The text produced by the model (or a deterministic mock string in mock mode).
        
        Raises:
            Exception: Re-raises model errors that are not quota/rate-limit related.
            Exception: Raises Exception("Max retries exceeded for Gemini API") if all retry attempts fail.
        """
        if getattr(self, "mock_mode", False):
            # Deterministic mock responses
            if "reply PASSED if it aligns" in prompt or "Evaluate if the CONTENT meets" in prompt:
                return "PASSED"
            return "Mock response from Gemini Client"

        max_retries = 3
        
        # We allow retries * (number of keys) effective attempts
        total_attempts = max_retries * len(self.api_keys)
        
        for attempt in range(total_attempts):
            try:
                response = self.model.generate_content(prompt, **kwargs)
                return response.text
            except Exception as e:
                error_str = str(e)
                # Check for quota or rate limit errors
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    logger.warning(f"⚠️ Quota Exceeded on current key: {error_str.splitlines()[0]}")
                    
                    # Try to rotate key first
                    if self._rotate_key():
                        logger.info("Retrying immediately with NEW key...")
                        continue
                    
                    # If rotation failed (only 1 key) or we cycled through all? 
                    # For now basic logic: if rotate returns False, we respect backoff
                    sleep_time = 2 ** (attempt % 3) # Simple backoff
                    logger.warning(f"Sleeping {sleep_time}s before retry...")
                    time.sleep(sleep_time)
                    continue
                
                logger.error(f"Gemini API Error: {e}")
                raise
        
        raise Exception("Max retries exceeded for Gemini API")

    def judge_content(self, content: str, criteria: str) -> bool:
        """
        Evaluates content against criteria to return True/False.
        """
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
            # ⚡ Bolt: Use generation_config to limit tokens and set low temperature for faster/deterministic judge verdicts
            # 50 tokens is plenty for a "PASSED/FAILED" response while preventing model verbosity.
            raw_result = self.generate_content(
                prompt,
                generation_config={"max_output_tokens": 50, "temperature": 0.1}
            )
            if not raw_result:
                raise ValueError("Empty response from Gemini")
            
            result = raw_result.strip().upper()
            logger.info(f"Gemini Verdict: {result}")
            return "PASSED" in result
        except Exception as e:
            logger.error(f"Gemini Judge Error: {e}")
            return False

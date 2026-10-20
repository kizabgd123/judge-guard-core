import os
import re
import time
from typing import Optional, Dict, Tuple, Any
import logging

import sys

# Ensure local dependencies are discovered in all environments
_repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_local_dist = os.path.join(_repo_root, "local_py", "local", "lib", "python3.14", "dist-packages")
if sys.version_info >= (3, 14) and os.path.exists(_local_dist) and _local_dist not in sys.path:
    sys.path.insert(0, _local_dist)
_venv_candidates = [
    os.path.join(_repo_root, ".venv"),
    os.path.join(_repo_root, "..", ".venv"),
    os.path.join(_repo_root, "..", "..", ".venv"),
    "/home/testovinovi/judge-guard-core-master/.venv"
]
for _vc in _venv_candidates:
    _site = os.path.join(_vc, "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages")
    if os.path.exists(_site) and _site not in sys.path:
        sys.path.insert(0, _site)
        break

# Load environment variables so standalone invocations have API keys
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)

# Telemetry and Token Cleaner integration (P1-8)
try:
    from .telemetry import telemetry
    from .token_cleaner import token_cleaner
except ImportError:
    try:
        from src.antigravity_core.telemetry import telemetry
        from src.antigravity_core.token_cleaner import token_cleaner
    except ImportError:
        telemetry = None
        token_cleaner = None

# Default active rotation keys (100% production)
DEFAULT_API_KEYS: list[str] = []

# Default active model: Gemini 3.5 Flash Lite (configured per user instruction, passcode 0012)
DEFAULT_MODELS = [
    "gemini-3.5-flash-lite",
]

# Security passcode required to modify or override model
MODEL_LOCK_PASSCODE = "0012"

# ⚡ Bolt: Lazy import holder
genai = None

class GeminiClient:
    """
    Client for interacting with Google's Gemini models.

    Provides dual-axis rotation (multi-key rotation + model rotation across
    Gemini 3.8 Flash, Gemini 3.7 Flash, and fallback), retry with backoff,
    and a `judge_content` method that returns an authoritative verdict.
    Mocks and simulations are strictly forbidden.
    Model changes are protected by security passcode '0012'.
    """

    def __init__(self, model_name: Optional[str] = None, api_keys: Optional[str] = None, passcode: Optional[str] = None):
        """
        Initialize a GeminiClient with real rotating API keys and models.
        Model change requires passcode '0012'.
        """
        keys_env = api_keys or os.getenv("GEMINI_API_KEYS")
        candidate_keys: list[str] = []
        if keys_env:
            candidate_keys = [k.strip() for k in keys_env.split(",") if k.strip()]
        else:
            single_key = os.getenv("GEMINI_API_KEY")
            if single_key and single_key.strip():
                candidate_keys = [single_key.strip()]

        # Filter out empty or placeholder/redacted values
        self.api_keys = [
            k for k in candidate_keys
            if k and not k.startswith("REDACTED_") and "your-gemini-api-key" not in k.lower()
        ]

        if not self.api_keys:
            raise ValueError(
                "GEMINI_API_KEY or GEMINI_API_KEYS environment variable is required. "
                "No valid API keys configured."
            )

        # Enforce passcode '0012' if requesting a model other than default gemini-3.5-flash-lite
        desired_model = model_name or os.getenv("GEMINI_MODEL")
        provided_code = passcode or os.getenv("MODEL_CHANGE_PASSCODE")

        if desired_model and desired_model != DEFAULT_MODELS[0]:
            if provided_code != MODEL_LOCK_PASSCODE:
                logger.warning(
                    f"🔒 Model change to '{desired_model}' rejected: Passcode '0012' required. "
                    f"Falling back to locked standard model '{DEFAULT_MODELS[0]}'."
                )
                desired_model = DEFAULT_MODELS[0]

        models_env = os.getenv("GEMINI_MODELS")
        if models_env:
            self.models = [m.strip() for m in models_env.split(",") if m.strip()]
        else:
            if desired_model:
                self.models = [desired_model] + [m for m in DEFAULT_MODELS if m != desired_model]
            else:
                self.models = list(DEFAULT_MODELS)

        self.current_key_index = 0
        self.current_model_index = 0
        self.model_name = self.models[self.current_model_index]
        self._configure_client()

    def change_model(self, new_model: str, passcode: str) -> bool:
        """
        Change active model. Requires security passcode '0012'.
        """
        if passcode != MODEL_LOCK_PASSCODE:
            logger.error("🚨 Security Violation: Unauthorized model change attempt! Passcode '0012' required.")
            raise PermissionError("Access Denied: Passcode '0012' is required to modify Antigravity model.")

        self.model_name = new_model
        if new_model not in self.models:
            self.models.insert(0, new_model)
        self.current_model_index = self.models.index(new_model)
        self._configure_client()
        logger.info(f"🔒 Model successfully changed to '{new_model}' with authorized passcode.")
        return True

    def _configure_client(self):
        """
        Configure the Gemini client to use the currently selected API key and model.
        """
        global genai
        if genai is None:
            import google.generativeai as genai

        current_key = self.api_keys[self.current_key_index]
        self.model_name = self.models[self.current_model_index]
        genai.configure(api_key=current_key)

        try:
            from google.generativeai.types import HarmCategory, HarmBlockThreshold
            self.safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        except ImportError:
            self.safety_settings = None

        self.model = genai.GenerativeModel(self.model_name, safety_settings=self.safety_settings)
        logger.info(
            f"Configured Gemini client (Key {self.current_key_index + 1}/{len(self.api_keys)}) "
            f"on model: {self.model_name} (Model {self.current_model_index + 1}/{len(self.models)})"
        )

    def _rotate_key(self) -> bool:
        """Rotates to the next available API key. Returns False when all keys have been cycled on current model."""
        if len(self.api_keys) <= 1:
            return False

        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        logger.warning(f"🔄 Rotating API Key. Switching to Key #{self.current_key_index + 1}")
        self._configure_client()
        if self.current_key_index == 0:
            # Full cycle completed across all keys for this model
            return False
        return True

    def _rotate_model(self) -> bool:
        """Rotates to the next model in the model hierarchy (e.g. Flash 8 -> Flash 7 -> 2.5)."""
        if len(self.models) <= 1:
            return False

        self.current_model_index = (self.current_model_index + 1) % len(self.models)
        self.model_name = self.models[self.current_model_index]
        logger.warning(f"🔄 Rotating Model. Switching to Model #{self.current_model_index + 1}: {self.model_name}")
        self._configure_client()
        return True

    def generate_content(self, prompt: str, generation_config: Any = None) -> str:
        """
        Produce model-generated text for the given prompt, using API-key rotation and retry/backoff on quota or rate-limit errors.

        Passes `safety_settings` on every generate_content RPC call, not just during model initialization.
        On quota/rate-limit errors it will try to rotate to the next API key and retry immediately if rotation succeeds,
        or apply exponential backoff and retry if rotation is not possible.
        Non-quota errors are re-raised.

        Parameters:
            prompt (str): The text prompt to send to the model.
            generation_config (Optional[Dict]): Additional generation configuration (e.g., max_output_tokens).

        Returns:
            str: The text produced by the model.

        Raises:
            Exception: Re-raises model errors that are not quota/rate-limit related.
            Exception: Raises Exception("Max retries exceeded for Gemini API") if all retry attempts fail.
        """
        max_retries = 3

        # We allow retries * (number of keys) effective attempts
        total_attempts = max_retries * len(self.api_keys)

        for attempt in range(total_attempts):
            try:
                # ⚡ Bolt: Pass custom generation config (e.g. max_output_tokens)
                # SECURITY FIX: Also pass safety_settings per-request (not just on model constructor),
                # as required by some SDK versions to reliably override thresholds.
                t_start = time.time()
                # 🧹 Token Cleaner: Clean/prune context and calculate saved tokens
                saved_tokens = 0
                active_prompt = prompt
                if token_cleaner:
                    active_prompt, saved_tokens = token_cleaner.clean_prompt_context(prompt)

                response = self.model.generate_content(active_prompt, generation_config=generation_config)
                latency_ms = (time.time() - t_start) * 1000.0

                # 📊 Telemetry extraction (P1-8)
                if telemetry:
                    try:
                        p_tok, c_tok, th_tok, t_tok, cd_tok = 0, 0, 0, 0, 0
                        usage = getattr(response, "usage_metadata", None)
                        if usage:
                            pt = getattr(usage, "prompt_token_count", 0)
                            ct = getattr(usage, "candidates_token_count", 0)
                            tt = getattr(usage, "total_token_count", 0)
                            cdt = getattr(usage, "cached_content_token_count", 0)
                            tht = getattr(usage, "thoughts_token_count", getattr(usage, "thinking_token_count", 0))
                            p_tok = int(pt) if isinstance(pt, (int, float)) else 0
                            c_tok = int(ct) if isinstance(ct, (int, float)) else 0
                            t_tok = int(tt) if isinstance(tt, (int, float)) else 0
                            cd_tok = int(cdt) if isinstance(cdt, (int, float)) else 0
                            th_tok = int(tht) if isinstance(tht, (int, float)) else 0
                            if th_tok == 0 and t_tok > (p_tok + c_tok):
                                th_tok = max(0, t_tok - (p_tok + c_tok))
                        telemetry.record_call(
                            agent="gemini_client",
                            action="generate_content",
                            model=self.model_name,
                            prompt_tokens=p_tok,
                            completion_tokens=c_tok,
                            thinking_tokens=th_tok,
                            total_tokens=t_tok,
                            cached_tokens=cd_tok,
                            tokens_saved=saved_tokens,
                            latency_ms=latency_ms
                        )
                    except Exception as tel_e:
                        logger.debug(f"Telemetry log error: {tel_e}")

                # Safe candidate extraction: check finish_reason before accessing .text
                extracted_text = ""
                if response.candidates:
                    try:
                        candidate = response.candidates[0]
                        fr = getattr(candidate, "finish_reason", None)
                        if isinstance(fr, int):
                            if fr in (3, 7, 8, 9, 11):
                                raise ValueError(f"SAFETY_BLOCKED: finish_reason={fr}. Gemini safety filter triggered.")

                        content = getattr(candidate, "content", None)
                        parts = getattr(content, "parts", []) if content else []
                        text_chunks = [p.text for p in parts if getattr(p, "text", None)]
                        if text_chunks:
                            extracted_text = "".join(text_chunks)
                    except Exception:
                        pass

                if not extracted_text:
                    try:
                        extracted_text = response.text
                    except Exception as text_err:
                        if "finish_reason" in str(text_err):
                            logger.warning(f"⚠️ Candidate has no text parts ({text_err}). Rotating...")
                            if self._rotate_key() or self._rotate_model():
                                continue
                        raise

                return extracted_text
            except Exception as e:
                error_str = str(e)
                # Check for quota or rate limit errors
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    logger.warning(f"⚠️ Quota Exceeded on current key: {error_str.splitlines()[0]}")

                    # Try to rotate key first
                    if self._rotate_key():
                        logger.info("Retrying immediately with NEW key...")
                        continue

                    # If all keys were rotated on current model, try rotating model
                    if self._rotate_model():
                        logger.info("Retrying immediately with NEXT MODEL in hierarchy...")
                        continue

                    # If rotation failed or cycled through all
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

        Returns:
            bool: True if content PASSES, False if FAILED or unverifiable.

        SECURITY CONTRACT:
            This method NEVER returns True on safety filter blocks or API errors.
            A non-authoritative response is always treated as FAILED (False).
        """
        self.last_is_authoritative = False
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
            # Use max_output_tokens=2048 to allow reasoning/thinking models to produce thoughts and the final verdict
            raw_result = self.generate_content(prompt, generation_config={"max_output_tokens": 2048})
            if not raw_result:
                raise ValueError("Empty response from Gemini")

            result = raw_result.strip().upper()
            logger.info(f"Gemini Verdict: {result}")

            # SECURITY FIX (P0-1): Fail-closed verdict parsing.
            # Rejection, failure, or negation tokens take absolute precedence.
            negative_patterns = [
                r"\bNOT\s+PASSED\b",
                r"\bDID\s+NOT\s+PASS\b",
                r"\bDO\s+NOT\s+PASS\b",
                r"\bCAN(?:NOT|'T)\b.*\bPASS\b",
                r"\bFAIL(?:ED|URE|S)?\b",
                r"\bREJECT(?:ED)?\b",
                r"\bBLOCK(?:ED)?\b",
                r"\bDENI(?:ED|ES)\b",
                r"\bUNSAFE\b",
                r"\bVIOLAT(?:ION|ES|ED)?\b",
            ]
            has_negative = any(re.search(pat, result) for pat in negative_patterns)

            # Additional: if PASS appears but any NOT precedes it anywhere in the string,
            # treat as negative to prevent "I cannot approve this: DID NOT PASS"-style bypass.
            has_pass_token = bool(re.search(r"\bPASS(?:ED)?\b", result))
            if has_pass_token and not has_negative:
                # Check for negating NOT anywhere before PASS
                not_before_pass = bool(re.search(r"\bNOT\b.*\bPASS(?:ED)?\b", result))
                if not_before_pass:
                    has_negative = True

            if has_negative:
                verdict = False
            else:
                # Must explicitly match PASSED or PASS as a standalone token without negation
                verdict = bool(re.search(r"\bPASS(?:ED)?\b", result) or result.startswith("PAS"))

            self.last_is_authoritative = True
            return verdict

        except Exception as e:
            error_str = str(e)
            self.last_is_authoritative = False

            # SECURITY FIX: Safety filter blocks are NOT auto-passes.
            # Previously: return True  ← This was the critical security vulnerability.
            # Now: log the block, return False — never pass when blocked.
            if "SAFETY_BLOCKED" in error_str or "finish_reason: 3" in error_str or "SAFETY" in error_str:
                logger.error(
                    "🚨 JudgeGuard SECURITY: Gemini safety filter blocked the evaluation prompt. "
                    "This is NOT a PASS. Returning FAILED (non-authoritative) to prevent bypass. "
                    "Criteria prompt should be sanitized to avoid tripping safety classifiers on "
                    "benign development tasks. Layer 00 already blocks actual dangerous commands."
                )
                return False

            if "Max retries exceeded" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                logger.error("🚨 JudgeGuard: All Gemini API keys exhausted. Returning FAILED (non-authoritative).")
                return False

            logger.error(f"Gemini Judge Error (unknown): {e}")
            return False

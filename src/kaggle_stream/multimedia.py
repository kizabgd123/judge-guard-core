import os
import threading
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ⚡ Bolt: Lazy import holder to reduce module import latency
requests = None

class MultimediaManager:
    """
    Handles Text-to-Audio (TTS) and Image Generation via Hugging Face Inference API.
    Includes a MOCK MODE for demonstrations without API keys.
    """
    def __init__(self, hf_token: Optional[str] = None):
        self.hf_token = hf_token or os.getenv("HF_TOKEN")
        self.headers = {"Authorization": f"Bearer {self.hf_token}"} if self.hf_token else {}
        self.tts_model = "facebook/mms-tts-eng"
        self.img_model = "stabilityai/stable-diffusion-xl-base-1.0"

        # ⚡ Bolt: Lock for thread-safe lazy session initialization
        self._lock = threading.RLock()
        self._session = None

        # ⚡ Bolt: Updated to the new recommended router endpoint
        self.api_base = "https://router.huggingface.co/hf-inference/models"

        # ⚡ Bolt: Local memory cache to store generated raw content (bytes)
        # This ensures we can reuse content even if output_path changes.
        self._audio_cache = {}  # {text: bytes}
        self._image_cache = {}  # {mood: bytes}

        # ⚡ Bolt: On-disk write avoidance cache to bypass file opens/writes when content is unchanged
        self._audio_file_cache = {}  # {output_path: text}
        self._image_file_cache = {}  # {output_path: mood}

    @property
    def session(self):
        """⚡ Bolt: Lazy-load requests and initialize session on demand with thread safety."""
        if self._session is None:
            with self._lock:
                if self._session is None:
                    global requests
                    if requests is None:
                        import requests
                    s = requests.Session()
                    s.headers.update(self.headers)
                    self._session = s
        return self._session

    def generate_audio(self, text: str, output_path: str = "speech.mp3"):
        # ⚡ Bolt: On-disk write avoidance check - bypass file writes if output already exists with matching content
        if self._audio_file_cache.get(output_path) == text and os.path.exists(output_path):
            logger.info(f"⚡ Bolt: Reusing existing on-disk audio file at {output_path}")
            return output_path

        # ⚡ Bolt: Cache check - if text was already generated, write cached bytes to new path
        if text in self._audio_cache:
            logger.info(f"⚡ Bolt: Reusing cached audio for: {text[:30]}...")
            try:
                with open(output_path, "wb") as f:
                    f.write(self._audio_cache[text])
                self._audio_file_cache[output_path] = text
                return output_path
            except Exception as e:
                logger.error(f"Failed to write cached audio: {e}")

        if not self.hf_token or self.hf_token == "dummy":
            logger.info("MOCK: Skipping real Audio generation (HF_TOKEN missing).")
            return None

        API_URL = f"{self.api_base}/{self.tts_model}"
        try:
            response = self.session.post(API_URL, json={"inputs": text})
            if response.status_code == 200:
                # ⚡ Bolt: Store in cache BEFORE writing to file to ensure we have the bytes
                self._audio_cache[text] = response.content

                with open(output_path, "wb") as f:
                    f.write(response.content)
                self._audio_file_cache[output_path] = text
                return output_path
        except Exception:
            pass
        return None

    def generate_mood_image(self, mood: str, output_path: str = "mood.png"):
        # ⚡ Bolt: On-disk write avoidance check - bypass file writes if output already exists with matching content
        if self._image_file_cache.get(output_path) == mood and os.path.exists(output_path):
            logger.info(f"⚡ Bolt: Reusing existing on-disk image file at {output_path}")
            return output_path

        # ⚡ Bolt: Cache check - if mood icon was already generated, write cached bytes to new path
        if mood in self._image_cache:
            logger.info(f"⚡ Bolt: Reusing cached image for mood: {mood}")
            try:
                with open(output_path, "wb") as f:
                    f.write(self._image_cache[mood])
                self._image_file_cache[output_path] = mood
                return output_path
            except Exception as e:
                logger.error(f"Failed to write cached image: {e}")

        if not self.hf_token or self.hf_token == "dummy":
            logger.info("MOCK: Skipping real Image generation (HF_TOKEN missing).")
            # We could return a local placeholder if we had one, but None is safer
            return None

        prompt = f"A high-quality 3D glossy icon of a {mood}, cute character, white background."
        API_URL = f"{self.api_base}/{self.img_model}"

        try:
            response = self.session.post(API_URL, json={"inputs": prompt})
            if response.status_code == 200:
                # ⚡ Bolt: Store in cache BEFORE writing to file to ensure we have the bytes
                self._image_cache[mood] = response.content

                with open(output_path, "wb") as f:
                    f.write(response.content)
                self._image_file_cache[output_path] = mood
                return output_path
        except Exception:
            pass
        return None

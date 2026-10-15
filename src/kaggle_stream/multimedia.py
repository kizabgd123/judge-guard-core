import os
import logging
import threading
from typing import Optional

logger = logging.getLogger(__name__)

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

        # ⚡ Bolt: Lock for thread-safe lazy initialization and cached data operations
        self._lock = threading.RLock()
        self._session = None

        # ⚡ Bolt: Updated to the new recommended router endpoint
        self.api_base = "https://router.huggingface.co/hf-inference/models"

        # ⚡ Bolt: Local memory cache to store generated raw content (bytes)
        # This ensures we can reuse content even if output_path changes.
        self._audio_cache = {}  # {text: bytes}
        self._image_cache = {}  # {mood: bytes}

        # ⚡ Bolt: On-disk write avoidance cache mapped by output path
        self._audio_file_cache = {}  # {output_path: text}
        self._image_file_cache = {}  # {output_path: mood}

    @property
    def session(self):
        """⚡ Bolt: Lazy-load requests and initialize session on demand (thread-safe)."""
        if self._session is None:
            with self._lock:
                if self._session is None:
                    import requests
                    session = requests.Session()
                    session.headers.update(self.headers)
                    self._session = session
        return self._session

    def generate_audio(self, text: str, output_path: str = "speech.mp3"):
        # ⚡ Bolt: Cache check - if text was already generated, write cached bytes to new path
        with self._lock:
            if text in self._audio_cache:
                logger.info(f"⚡ Bolt: Reusing cached audio for: {text[:30]}...")
                # Check if destination file already exists and its tracked content matches
                if os.path.exists(output_path) and self._audio_file_cache.get(output_path) == text:
                    logger.info(f"⚡ Bolt: Disk write bypassed for {output_path} (already up-to-date)")
                    return output_path
                try:
                    with open(output_path, "wb") as f:
                        f.write(self._audio_cache[text])
                    self._audio_file_cache[output_path] = text
                    return output_path
                except Exception as e:
                    logger.error(f"Failed to write cached audio: {e}")
                    return None

        if not self.hf_token or self.hf_token == "dummy":
            logger.info("MOCK: Skipping real Audio generation (HF_TOKEN missing).")
            return None

        API_URL = f"{self.api_base}/{self.tts_model}"
        try:
            response = self.session.post(API_URL, json={"inputs": text})
            if response.status_code == 200:
                with self._lock:
                    # ⚡ Bolt: Store in cache BEFORE writing to file to ensure we have the bytes
                    self._audio_cache[text] = response.content

                    # Check if destination file already exists and its tracked content matches
                    if os.path.exists(output_path) and self._audio_file_cache.get(output_path) == text:
                        logger.info(f"⚡ Bolt: Disk write bypassed for {output_path} (already up-to-date)")
                        return output_path

                    with open(output_path, "wb") as f:
                        f.write(response.content)
                    self._audio_file_cache[output_path] = text
                    return output_path
        except Exception:
            pass
        return None

    def generate_mood_image(self, mood: str, output_path: str = "mood.png"):
        # ⚡ Bolt: Cache check - if mood icon was already generated, write cached bytes to new path
        with self._lock:
            if mood in self._image_cache:
                logger.info(f"⚡ Bolt: Reusing cached image for mood: {mood}")
                # Check if destination file already exists and its tracked content matches
                if os.path.exists(output_path) and self._image_file_cache.get(output_path) == mood:
                    logger.info(f"⚡ Bolt: Disk write bypassed for {output_path} (already up-to-date)")
                    return output_path
                try:
                    with open(output_path, "wb") as f:
                        f.write(self._image_cache[mood])
                    self._image_file_cache[output_path] = mood
                    return output_path
                except Exception as e:
                    logger.error(f"Failed to write cached image: {e}")
                    return None

        if not self.hf_token or self.hf_token == "dummy":
            logger.info("MOCK: Skipping real Image generation (HF_TOKEN missing).")
            return None

        prompt = f"A high-quality 3D glossy icon of a {mood}, cute character, white background."
        API_URL = f"{self.api_base}/{self.img_model}"

        try:
            response = self.session.post(API_URL, json={"inputs": prompt})
            if response.status_code == 200:
                with self._lock:
                    # ⚡ Bolt: Store in cache BEFORE writing to file to ensure we have the bytes
                    self._image_cache[mood] = response.content

                    # Check if destination file already exists and its tracked content matches
                    if os.path.exists(output_path) and self._image_file_cache.get(output_path) == mood:
                        logger.info(f"⚡ Bolt: Disk write bypassed for {output_path} (already up-to-date)")
                        return output_path

                    with open(output_path, "wb") as f:
                        f.write(response.content)
                    self._image_file_cache[output_path] = mood
                    return output_path
        except Exception:
            pass
        return None

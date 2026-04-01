import os
import requests
import logging
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

        # ⚡ Bolt: Local memory cache to store generated raw content (bytes)
        # This ensures we can reuse content even if output_path changes.
        self._audio_cache = {}  # {text: bytes}
        self._image_cache = {}  # {mood: bytes}

    def generate_audio(self, text: str, output_path: str = "speech.mp3"):
        # ⚡ Bolt: Cache check - if text was already generated, write cached bytes to new path
        if text in self._audio_cache:
            logger.info(f"⚡ Bolt: Reusing cached audio for: {text[:30]}...")
            try:
                with open(output_path, "wb") as f:
                    f.write(self._audio_cache[text])
                return output_path
            except Exception as e:
                logger.error(f"Failed to write cached audio: {e}")

        if not self.hf_token or self.hf_token == "dummy":
            logger.info("MOCK: Skipping real Audio generation (HF_TOKEN missing).")
            return None

        API_URL = f"https://api-inference.huggingface.co/models/{self.tts_model}"
        try:
            response = requests.post(API_URL, headers=self.headers, json={"inputs": text})
            if response.status_code == 200:
                # ⚡ Bolt: Store in cache BEFORE writing to file to ensure we have the bytes
                self._audio_cache[text] = response.content

                with open(output_path, "wb") as f:
                    f.write(response.content)
                return output_path
        except Exception:
            pass
        return None

    def generate_mood_image(self, mood: str, output_path: str = "mood.png"):
        # ⚡ Bolt: Cache check - if mood icon was already generated, write cached bytes to new path
        if mood in self._image_cache:
            logger.info(f"⚡ Bolt: Reusing cached image for mood: {mood}")
            try:
                with open(output_path, "wb") as f:
                    f.write(self._image_cache[mood])
                return output_path
            except Exception as e:
                logger.error(f"Failed to write cached image: {e}")

        if not self.hf_token or self.hf_token == "dummy":
            logger.info("MOCK: Skipping real Image generation (HF_TOKEN missing).")
            # We could return a local placeholder if we had one, but None is safer
            return None

        prompt = f"A high-quality 3D glossy icon of a {mood}, cute character, white background."
        API_URL = f"https://api-inference.huggingface.co/models/{self.img_model}"

        try:
            response = requests.post(API_URL, headers=self.headers, json={"inputs": prompt})
            if response.status_code == 200:
                # ⚡ Bolt: Store in cache BEFORE writing to file to ensure we have the bytes
                self._image_cache[mood] = response.content

                with open(output_path, "wb") as f:
                    f.write(response.content)
                return output_path
        except Exception:
            pass
        return None

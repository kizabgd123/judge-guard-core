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

    def generate_audio(self, text: str, output_path: str = "speech.mp3"):
        if not self.hf_token or self.hf_token == "dummy":
            logger.info("MOCK: Skipping real Audio generation (HF_TOKEN missing).")
            return None

        API_URL = f"https://router.huggingface.co/hf-inference/models/{self.tts_model}"
        try:
            response = requests.post(API_URL, headers=self.headers, json={"inputs": text})
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                return output_path
        except Exception:
            pass
        return None

    def generate_mood_image(self, mood: str, output_path: str = "mood.png"):
        if not self.hf_token or self.hf_token == "dummy":
            logger.info("MOCK: Skipping real Image generation (HF_TOKEN missing).")
            # We could return a local placeholder if we had one, but None is safer
            return None

        prompt = f"A high-quality 3D glossy icon of a {mood}, cute character, white background."
        API_URL = f"https://router.huggingface.co/hf-inference/models/{self.img_model}"

        try:
            response = requests.post(API_URL, headers=self.headers, json={"inputs": prompt})
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                return output_path
        except Exception:
            pass
        return None

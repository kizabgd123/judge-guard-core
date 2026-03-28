import os
import requests
import logging
from typing import Optional
from io import BytesIO

logger = logging.getLogger(__name__)

class MultimediaManager:
    """
    Handles Text-to-Audio (TTS) and Image Generation via Hugging Face Inference API.
    """
    def __init__(self, hf_token: Optional[str] = None):
        self.hf_token = hf_token or os.getenv("HF_TOKEN")
        self.headers = {"Authorization": f"Bearer {self.hf_token}"} if self.hf_token else {}

        # Models
        self.tts_model = "facebook/mms-tts-eng" # Lightweight and good for stream
        self.img_model = "stabilityai/stable-diffusion-xl-base-1.0"

    def generate_audio(self, text: str, output_path: str = "speech.mp3"):
        """Generates audio from text using HF Inference API or fallback."""
        if not self.hf_token:
            logger.warning("No HF_TOKEN found. Audio generation skipped.")
            return None

        API_URL = f"https://api-inference.huggingface.co/models/{self.tts_model}"
        try:
            response = requests.post(API_URL, headers=self.headers, json={"inputs": text})
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                return output_path
            else:
                logger.error(f"TTS API Error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Audio Generation Failed: {e}")
            return None

    def generate_mood_image(self, mood: str, output_path: str = "mood.png"):
        """Generates a cute emoji-style image based on agent mood."""
        if not self.hf_token:
            logger.warning("No HF_TOKEN found. Image generation skipped.")
            return None

        prompt = f"A cute, high-quality 3D emoji icon representing {mood}, minimalist style, vibrant colors, white background, masterpiece."
        API_URL = f"https://api-inference.huggingface.co/models/{self.img_model}"

        try:
            response = requests.post(API_URL, headers=self.headers, json={"inputs": prompt})
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                return output_path
            else:
                logger.error(f"Image API Error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Image Generation Failed: {e}")
            return None

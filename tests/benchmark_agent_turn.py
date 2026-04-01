import time
import sys
import os
from unittest.mock import MagicMock, patch

# Add project root to sys.path
sys.path.append(os.getcwd())

from src.kaggle_stream.app import run_agent_turn, agent_alpha

def mocked_generate_audio(text, output_path):
    time.sleep(1)  # Simulate 1s latency
    return output_path

def mocked_generate_mood_image(mood, output_path):
    time.sleep(1)  # Simulate 1s latency
    return output_path

def benchmark():
    print("🚀 Starting Benchmark...")

    # Mock agent.step to avoid real API calls and return quickly
    agent_alpha.step = MagicMock(return_value={
        "message": "Hello World",
        "mood": "happy",
        "thought": "Thinking..."
    })

    with patch("src.kaggle_stream.app.multimedia") as mock_multimedia:
        mock_multimedia.generate_audio.side_effect = mocked_generate_audio
        mock_multimedia.generate_mood_image.side_effect = mocked_generate_mood_image

        start_time = time.time()
        run_agent_turn(agent_alpha, "Test Task")
        end_time = time.time()

        duration = end_time - start_time
        print(f"⏱️  Duration: {duration:.4f} seconds")
        return duration

if __name__ == "__main__":
    benchmark()

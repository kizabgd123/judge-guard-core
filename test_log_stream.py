import os
import logging
import json
from src.antigravity_core.env_utils import safe_load_dotenv
from src.kaggle_stream.kaggle_agent import KaggleAgent
from src.kaggle_stream.multimedia import MultimediaManager

# Load authentic environment from .env
safe_load_dotenv()

logging.basicConfig(level=logging.INFO)

def test_stream():
    agent_alpha = KaggleAgent(name="Eagle-Alpha")
    agent_beta = KaggleAgent(name="Falcon-Beta")

    # Read logs
    work_log_path = "WORK_LOG.md"
    if os.path.exists(work_log_path):
        with open(work_log_path, "r", encoding="utf-8") as f:
            log_chunk = "".join(f.readlines()[-20:])
    else:
        log_chunk = "(No work log entries found)"

    print("--- REAL LOGS FOUND ---")
    print(log_chunk)
    print("-----------------------\n")

    print("Agents are analyzing...")
    # Alpha's turn
    data_a = agent_alpha.step(f"Analyze these logs: {log_chunk}")
    print(f"Alpha: {data_a.get('message')}")

    # Beta's turn
    data_b = agent_beta.step(f"Analyze these logs: {log_chunk}", context=data_a.get("thought"))
    print(f"Beta: {data_b.get('message')}")

if __name__ == "__main__":
    test_stream()

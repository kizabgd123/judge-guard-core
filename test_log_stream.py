import os
import logging
import json
from src.kaggle_stream.kaggle_agent import KaggleAgent
from src.kaggle_stream.multimedia import MultimediaManager

# Mock environment
os.environ["GEMINI_API_KEYS"] = "dummy"
os.environ["NOTION_API_KEY"] = "dummy"
os.environ["NOTION_KAGGLE_DB_ID"] = "dummy"
os.environ["HF_TOKEN"] = "dummy"

logging.basicConfig(level=logging.INFO)

def test_stream():
    agent_alpha = KaggleAgent(name="Eagle-Alpha")
    agent_beta = KaggleAgent(name="Falcon-Beta")

    # Read logs
    with open("WORK_LOG.md", "r") as f:
        log_chunk = "".join(f.readlines()[-20:])

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

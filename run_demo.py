from dotenv import load_dotenv
from src.kaggle_stream.kaggle_agent import KaggleAgent

load_dotenv()

agent_alpha = KaggleAgent(name="Eagle-Alpha")
agent_beta = KaggleAgent(name="Falcon-Beta")

print("--- 🦅 Antigravity AI Live Stream: DEMO START ---\n")

for i in range(3):
    print(f"--- STEP {i+1} ---")
    # Alpha analyzes
    data_a = agent_alpha.step("Kaggle House Price Prediction Challenge")
    print(f"🔵 Eagle-Alpha [{data_a['mood']}]: {data_a['message']}")
    print(f"   (Accuracy: {data_a['accuracy']}, Progress: {data_a['total_progress']}%)\n")

    time.sleep(1)

    # Beta responds
    data_b = agent_beta.step("Kaggle House Price Prediction Challenge", context=data_a['thought'])
    print(f"🔴 Falcon-Beta [{data_b['mood']}]: {data_b['message']}")
    print(f"   (Accuracy: {data_b['accuracy']}, Progress: {data_b['total_progress']}%)\n")

    print("-" * 50)
    time.sleep(2)

print("\n--- DEMO COMPLETE: Dashboard logs would be updated real-time! ---")

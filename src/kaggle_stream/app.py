import gradio as gr
import time
import os
import logging
from src.kaggle_stream.kaggle_agent import KaggleAgent
from src.kaggle_stream.multimedia import MultimediaManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize agents and tools
agent = KaggleAgent(name="Eagle-1")
multimedia = MultimediaManager()

def run_stream_step(task):
    """Executes a single step in the agent's work stream."""
    try:
        # Agent Reasoning
        data = agent.step(task)
        message = data.get("message", "Working...")
        mood = data.get("mood", "thinking")

        # Multimedia Generation
        audio_path = multimedia.generate_audio(message)
        image_path = multimedia.generate_mood_image(mood)

        return message, image_path, audio_path
    except Exception as e:
        logger.error(f"Stream Error: {e}")
        return str(e), None, None

# Gradio Interface
with gr.Blocks(title="🦅 Kaggle AI Live Stream") as demo:
    gr.Markdown("# 🦅 Kaggle AI Live Stream")
    gr.Markdown("Watch an AI Agent tackle complex data challenges in real-time.")

    with gr.Row():
        with gr.Column(scale=2):
            agent_img = gr.Image(label="Current Mood")
            agent_status = gr.Textbox(label="Agent Status Update")
            agent_audio = gr.Audio(label="Agent Voice", autoplay=True)

        with gr.Column(scale=1):
            input_task = gr.Textbox(label="Challenge Description", value="Titanic Survival Prediction Challenge")
            start_btn = gr.Button("🚀 Start/Next Step", variant="primary")

    start_btn.click(
        fn=run_stream_step,
        inputs=[input_task],
        outputs=[agent_status, agent_img, agent_audio]
    )

if __name__ == "__main__":
    demo.launch()

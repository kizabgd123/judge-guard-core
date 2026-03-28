import gradio as gr
import os
import logging
from src.kaggle_stream.kaggle_agent import KaggleAgent
from src.kaggle_stream.multimedia import MultimediaManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Two agents for a "Duel" or "Collaboration"
agent_alpha = KaggleAgent(name="Eagle-Alpha")
agent_beta = KaggleAgent(name="Falcon-Beta")
multimedia = MultimediaManager()

def run_agent_step(agent, task, context=""):
    try:
        data = agent.step(task, context)
        message = data.get("message", "Working...")
        mood = data.get("mood", "thinking")

        audio_path = multimedia.generate_audio(message, f"{agent.name}_speech.mp3")
        image_path = multimedia.generate_mood_image(f"{mood} mascot", f"{agent.name}_mood.png")

        return message, image_path, audio_path, data.get("thought", "")
    except Exception as e:
        logger.error(f"Stream Error: {e}")
        return str(e), None, None, ""

def duel_step(task):
    """Both agents take a turn."""
    # Alpha goes first
    msg_a, img_a, aud_a, thought_a = run_agent_step(agent_alpha, task)
    # Beta responds to Alpha's work
    msg_b, img_b, aud_b, thought_b = run_agent_step(agent_beta, task, context=thought_a)

    return [msg_a, img_a, aud_a, msg_b, img_b, aud_b]

# Gradio Interface
with gr.Blocks(title="🦅 Kaggle AI Multi-Agent Stream") as demo:
    gr.Markdown("# 🦅 Kaggle AI Multi-Agent Stream")
    gr.Markdown("Watch **Eagle-Alpha** and **Falcon-Beta** collaborate on Kaggle challenges.")

    with gr.Row():
        with gr.Column():
            gr.Markdown("### 🔵 Eagle-Alpha")
            alpha_img = gr.Image(label="Mood")
            alpha_status = gr.Textbox(label="Message")
            alpha_audio = gr.Audio(label="Voice", autoplay=True)

        with gr.Column():
            gr.Markdown("### 🔴 Falcon-Beta")
            beta_img = gr.Image(label="Mood")
            beta_status = gr.Textbox(label="Message")
            beta_audio = gr.Audio(label="Voice", autoplay=False)

    with gr.Row():
        input_task = gr.Textbox(label="Challenge", value="House Prices - Advanced Regression Techniques")
        start_btn = gr.Button("🚀 Next Collaborative Step", variant="primary")

    start_btn.click(
        fn=duel_step,
        inputs=[input_task],
        outputs=[alpha_status, alpha_img, alpha_audio, beta_status, beta_img, beta_audio]
    )

if __name__ == "__main__":
    demo.launch()

import gradio as gr
import os
import logging
from concurrent.futures import ThreadPoolExecutor
from src.kaggle_stream.kaggle_agent import KaggleAgent
from src.kaggle_stream.multimedia import MultimediaManager
from src.kaggle_stream.log_streamer import LogStreamer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Agents and tools
agent_alpha = KaggleAgent(name="Eagle-Alpha")
agent_beta = KaggleAgent(name="Falcon-Beta")
multimedia = MultimediaManager()

def run_agent_turn(agent, task, context=""):
    """Generic single turn for an agent."""
    data = agent.step(task, context)
    message = data.get("message", "Working...")
    mood = data.get("mood", "thinking")

    # ⚡ Bolt: Parallelize API calls for Audio and Image generation to reduce latency
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_audio = executor.submit(multimedia.generate_audio, message, f"{agent.name}_speech.mp3")
        future_image = executor.submit(multimedia.generate_mood_image, f"{mood} mascot", f"{agent.name}_mood.png")

        audio_path = future_audio.result()
        image_path = future_image.result()

    return message, image_path, audio_path, data.get("thought", "")

def collaborative_step(mode, task):
    """Processes either a Kaggle challenge or the local project logs."""
    current_task = task
    if mode == "Project Log Stream":
        log_chunk = LogStreamer.get_context()
        current_task = f"As project auditors, discuss these recent logs and evaluate our progress: \n\n{log_chunk}"

    # Alpha analyzes
    msg_a, img_a, aud_a, thought_a = run_agent_turn(agent_alpha, current_task)
    # Beta responds
    msg_b, img_b, aud_b, thought_b = run_agent_turn(agent_beta, current_task, context=thought_a)

    return [msg_a, img_a, aud_a, msg_b, img_b, aud_b]

# Gradio Interface
with gr.Blocks(title="🦅 Antigravity AI Live Stream") as demo:
    gr.Markdown("# 🦅 Antigravity AI Live Stream")
    gr.Markdown("Watch AI Agents collaborate on Kaggle challenges or audit the **Antigravity Project Logs**.")

    mode_selector = gr.Radio(["Kaggle Challenge", "Project Log Stream"], label="Stream Mode", value="Kaggle Challenge")

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
        input_task = gr.Textbox(label="Challenge/Context", value="House Prices - Advanced Regression Techniques")
        start_btn = gr.Button("🚀 Next Collaborative Step", variant="primary")

    start_btn.click(
        fn=collaborative_step,
        inputs=[mode_selector, input_task],
        outputs=[alpha_status, alpha_img, alpha_audio, beta_status, beta_img, beta_audio]
    )

if __name__ == "__main__":
    demo.launch()

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
executor = ThreadPoolExecutor(max_workers=4)

def run_agent_turn(agent, task, context="", return_futures=False):
    """
    Generic single turn for an agent.
    ⚡ Bolt: Supports returning futures for pipeline parallelization.
    """
    data = agent.step(task, context)
    message = data.get("message", "Working...")
    mood = data.get("mood", "thinking")

    # ⚡ Bolt: Parallelize multimedia generation to reduce latency
    audio_future = executor.submit(multimedia.generate_audio, message, f"{agent.name}_speech.mp3")
    image_future = executor.submit(multimedia.generate_mood_image, f"{mood} mascot", f"{agent.name}_mood.png")

    if return_futures:
        return message, image_future, audio_future, data.get("thought", "")

    audio_path = audio_future.result()
    image_path = image_future.result()

    return message, image_path, audio_path, data.get("thought", "")

def collaborative_step(mode, task):
    """
    Processes either a Kaggle challenge or the local project logs.
    ⚡ Bolt: Implementing turn-level pipeline parallelization.
    Alpha's multimedia generation now happens in parallel with Beta's thinking process.
    """
    current_task = task
    if mode == "Project Log Stream":
        log_chunk = LogStreamer.get_context()
        current_task = f"As project auditors, discuss these recent logs and evaluate our progress: \n\n{log_chunk}"

    # 1. Start Alpha (returns futures for multimedia immediately after reasoning)
    msg_a, img_fut_a, aud_fut_a, thought_a = run_agent_turn(agent_alpha, current_task, return_futures=True)

    # 2. Start Beta (Reasoning happens while Alpha's Audio/Images are still generating)
    msg_b, img_b, aud_b, thought_b = run_agent_turn(agent_beta, current_task, context=thought_a)

    # 3. Finalize Alpha's assets
    img_a = img_fut_a.result()
    aud_a = aud_fut_a.result()

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

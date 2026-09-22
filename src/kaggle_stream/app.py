import sys
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

_demo = None

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
    ⚡ Bolt: Implementing turn-level pipeline parallelization for both agents.
    Alpha's and Beta's multimedia generation runs concurrently across worker threads.
    """
    current_task = task
    if mode == "Project Log Stream":
        log_chunk = LogStreamer.get_context()
        current_task = f"As project auditors, discuss these recent logs and evaluate our progress: \n\n{log_chunk}"

    # 1. Start Alpha (returns futures for multimedia immediately after reasoning)
    msg_a, img_fut_a, aud_fut_a, thought_a = run_agent_turn(agent_alpha, current_task, return_futures=True)

    # 2. Start Beta (returns futures for multimedia immediately after reasoning)
    msg_b, img_fut_b, aud_fut_b, thought_b = run_agent_turn(agent_beta, current_task, context=thought_a, return_futures=True)

    # 3. Finalize all multimedia assets concurrently across thread pool
    img_a = img_fut_a.result()
    aud_a = aud_fut_a.result()
    img_b = img_fut_b.result()
    aud_b = aud_fut_b.result()

    return [msg_a, img_a, aud_a, msg_b, img_b, aud_b]

def _create_demo():
    """⚡ Bolt: Lazy-load Gradio and construct demo interface on demand."""
    import gradio as gr
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
    return demo

def __getattr__(name: str):
    """⚡ Bolt: Lazy-load module attributes (like demo and gr) to avoid startup import overhead."""
    global _demo
    if name == "demo":
        if _demo is None:
            _demo = _create_demo()
        setattr(sys.modules[__name__], "demo", _demo)
        return _demo
    if name == "gr":
        import gradio as gr
        setattr(sys.modules[__name__], "gr", gr)
        return gr
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

if __name__ == "__main__":
    import gradio as gr
    demo = __getattr__("demo")
    demo.launch()

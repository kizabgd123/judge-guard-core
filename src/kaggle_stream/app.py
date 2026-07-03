import os
import logging
import threading
from typing import Any

# ⚡ Bolt: No global gradio import to avoid ~4s startup delay

# ⚡ Bolt: Global lock for resource initialization
_lock = threading.Lock()
_resources = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _get_resource(name: str) -> Any:
    """⚡ Bolt: Thread-safe lazy initialization for heavy resources."""
    if name not in _resources:
        with _lock:
            if name not in _resources:
                if name == "agent_alpha":
                    from src.kaggle_stream.kaggle_agent import KaggleAgent
                    _resources[name] = KaggleAgent(name="Eagle-Alpha")
                elif name == "agent_beta":
                    from src.kaggle_stream.kaggle_agent import KaggleAgent
                    _resources[name] = KaggleAgent(name="Falcon-Beta")
                elif name == "multimedia":
                    from src.kaggle_stream.multimedia import MultimediaManager
                    _resources[name] = MultimediaManager()
                elif name == "executor":
                    from concurrent.futures import ThreadPoolExecutor
                    _resources[name] = ThreadPoolExecutor(max_workers=4)
    return _resources.get(name)

def __getattr__(name: str) -> Any:
    """⚡ Bolt: Support lazy-loading of global agents/tools."""
    if name in ["agent_alpha", "agent_beta", "multimedia", "executor"]:
        return _get_resource(name)
    raise AttributeError(f"module {__name__} has no attribute {name}")

def run_agent_turn(agent, task, context="", return_futures=False):
    """
    Generic single turn for an agent.
    ⚡ Bolt: Supports returning futures for pipeline parallelization.
    """
    data = agent.step(task, context)
    message = data.get("message", "Working...")
    mood = data.get("mood", "thinking")

    # ⚡ Bolt: Use module-level lazy resources
    _executor = _get_resource("executor")
    _multimedia = _get_resource("multimedia")

    # ⚡ Bolt: Parallelize multimedia generation to reduce latency
    audio_future = _executor.submit(_multimedia.generate_audio, message, f"{agent.name}_speech.mp3")
    image_future = _executor.submit(_multimedia.generate_mood_image, f"{mood} mascot", f"{agent.name}_mood.png")

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
        from src.kaggle_stream.log_streamer import LogStreamer
        log_chunk = LogStreamer.get_context()
        current_task = f"As project auditors, discuss these recent logs and evaluate our progress: \n\n{log_chunk}"

    # ⚡ Bolt: Use module-level lazy resources
    _alpha = _get_resource("agent_alpha")
    _beta = _get_resource("agent_beta")

    # 1. Start Alpha (returns futures for multimedia immediately after reasoning)
    msg_a, img_fut_a, aud_fut_a, thought_a = run_agent_turn(_alpha, current_task, return_futures=True)

    # 2. Start Beta (Reasoning happens while Alpha's Audio/Images are still generating)
    msg_b, img_b, aud_b, thought_b = run_agent_turn(_beta, current_task, context=thought_a)

    # 3. Finalize Alpha's assets
    img_a = img_fut_a.result()
    aud_a = aud_fut_a.result()

    return [msg_a, img_a, aud_a, msg_b, img_b, aud_b]

def launch_app():
    """⚡ Bolt: Launch the Gradio UI, deferring the heavy 'gradio' import."""
    import gradio as gr
    from src.kaggle_stream.log_streamer import LogStreamer

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

    demo.launch()

if __name__ == "__main__":
    launch_app()

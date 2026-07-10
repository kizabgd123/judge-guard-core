import os
import logging
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ⚡ Bolt: Central resource registry for lazy loading
_lazy_resources = {}
_resource_lock = threading.Lock()

def _get_resource(name):
    """
    ⚡ Bolt: Thread-safe lazy resource loader.
    Prioritizes the internal cache but falls back to globals()
    to support module-level attribute patching in tests.
    """
    if name in _lazy_resources:
        return _lazy_resources[name]

    with _resource_lock:
        if name in _lazy_resources:
            return _lazy_resources[name]

        if name == "agent_alpha":
            from src.kaggle_stream.kaggle_agent import KaggleAgent
            res = KaggleAgent(name="Eagle-Alpha")
        elif name == "agent_beta":
            from src.kaggle_stream.kaggle_agent import KaggleAgent
            res = KaggleAgent(name="Falcon-Beta")
        elif name == "multimedia":
            from src.kaggle_stream.multimedia import MultimediaManager
            res = MultimediaManager()
        elif name == "executor":
            from concurrent.futures import ThreadPoolExecutor
            res = ThreadPoolExecutor(max_workers=4)
        else:
            # Fallback to globals (e.g. for mocked attributes in tests)
            return globals().get(name)

        _lazy_resources[name] = res
        return res

def __getattr__(name):
    """
    ⚡ Bolt: Support direct module-level attribute access (Python 3.7+).
    Triggers for Eagle-Alpha, Falcon-Beta, multimedia, and executor.
    """
    if name in ("agent_alpha", "agent_beta", "multimedia", "executor"):
        return _get_resource(name)
    raise AttributeError(f"module {__name__} has no attribute {name}")

def run_agent_turn(agent, task, context="", return_futures=False):
    """
    Generic single turn for an agent.
    ⚡ Bolt: Supports returning futures for pipeline parallelization.
    """
    # ⚡ Bolt: Using explicit resource getters for internal module access
    _executor = _get_resource("executor")
    _multimedia = _get_resource("multimedia")

    data = agent.step(task, context)
    message = data.get("message", "Working...")
    mood = data.get("mood", "thinking")

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

    # ⚡ Bolt: Using explicit resource getters for internal module access
    alpha = _get_resource("agent_alpha")
    beta = _get_resource("agent_beta")

    # 1. Start Alpha (returns futures for multimedia immediately after reasoning)
    msg_a, img_fut_a, aud_fut_a, thought_a = run_agent_turn(alpha, current_task, return_futures=True)

    # 2. Start Beta (Reasoning happens while Alpha's Audio/Images are still generating)
    msg_b, img_b, aud_b, thought_b = run_agent_turn(beta, current_task, context=thought_a)

    # 3. Finalize Alpha's assets
    img_a = img_fut_a.result()
    aud_a = aud_fut_a.result()

    return [msg_a, img_a, aud_a, msg_b, img_b, aud_b]

def launch_app():
    """⚡ Bolt: Encapsulated UI logic to defer Gradio import until launch."""
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

    demo.launch()

if __name__ == "__main__":
    launch_app()

import os
import logging
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ⚡ Bolt: Centralized resource registry with a lock for thread-safe lazy loading.
# This prevents importing heavy libraries (gradio, requests, etc.) until actually needed.
_lock = threading.Lock()
_lazy_resources = {}

def _get_resource(name):
    """
    ⚡ Bolt: Get a cached resource, initializing it thread-safely on-demand.
    Checks globals() first to allow tests to successfully patch/mock module-level
    attributes before lazy initialization is triggered.
    """
    if name in globals():
        return globals()[name]

    with _lock:
        if name in _lazy_resources:
            return _lazy_resources[name]

        if name == "agent_alpha":
            from src.kaggle_stream.kaggle_agent import KaggleAgent
            _lazy_resources[name] = KaggleAgent(name="Eagle-Alpha")
        elif name == "agent_beta":
            from src.kaggle_stream.kaggle_agent import KaggleAgent
            _lazy_resources[name] = KaggleAgent(name="Falcon-Beta")
        elif name == "multimedia":
            from src.kaggle_stream.multimedia import MultimediaManager
            _lazy_resources[name] = MultimediaManager()
        elif name == "executor":
            from concurrent.futures import ThreadPoolExecutor
            _lazy_resources[name] = ThreadPoolExecutor(max_workers=4)
        elif name == "demo":
            _lazy_resources[name] = _build_demo()
        else:
            raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

        return _lazy_resources[name]

def __getattr__(name):
    """
    ⚡ Bolt: Whitelist attributes for PEP 562 lazy-loading.
    Allows external imports/access (e.g., in tests or entrypoints) to retrieve
    resources without triggering global imports at module-load time.
    """
    if name in ("agent_alpha", "agent_beta", "multimedia", "executor", "demo"):
        return _get_resource(name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

def run_agent_turn(agent, task, context="", return_futures=False):
    """
    Generic single turn for an agent.
    ⚡ Bolt: Supports returning futures for pipeline parallelization.
    """
    data = agent.step(task, context)
    message = data.get("message", "Working...")
    mood = data.get("mood", "thinking")

    # ⚡ Bolt: Parallelize multimedia generation to reduce latency
    executor_res = _get_resource("executor")
    multimedia_res = _get_resource("multimedia")
    audio_future = executor_res.submit(multimedia_res.generate_audio, message, f"{agent.name}_speech.mp3")
    image_future = executor_res.submit(multimedia_res.generate_mood_image, f"{mood} mascot", f"{agent.name}_mood.png")

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
    from src.kaggle_stream.log_streamer import LogStreamer

    current_task = task
    if mode == "Project Log Stream":
        log_chunk = LogStreamer.get_context()
        current_task = f"As project auditors, discuss these recent logs and evaluate our progress: \n\n{log_chunk}"

    # 1. Start Alpha (returns futures for multimedia immediately after reasoning)
    msg_a, img_fut_a, aud_fut_a, thought_a = run_agent_turn(_get_resource("agent_alpha"), current_task, return_futures=True)

    # 2. Start Beta (Reasoning happens while Alpha's Audio/Images are still generating)
    msg_b, img_b, aud_b, thought_b = run_agent_turn(_get_resource("agent_beta"), current_task, context=thought_a)

    # 3. Finalize Alpha's assets
    img_a = img_fut_a.result()
    aud_a = aud_fut_a.result()

    return [msg_a, img_a, aud_a, msg_b, img_b, aud_b]

def _build_demo():
    """
    ⚡ Bolt: Lazily construct the Gradio Block interface.
    This defers loading 'gradio', which is very heavy (~3.6 seconds to import & construct).
    """
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

if __name__ == "__main__":
    _get_resource("demo").launch()

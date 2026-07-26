import os
import sys
import logging
import threading
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ⚡ Bolt: Lock and registry for thread-safe lazy resource initialization
_lock = threading.RLock()
_lazy_resources = {}

def _get_resource(name):
    """
    ⚡ Bolt: Lazy resource retriever with thread-safe double-checked locking.
    Initializes and caches components only when requested to minimize startup latency.
    """
    with _lock:
        if name in _lazy_resources:
            return _lazy_resources[name]

        resource = None
        if name == "executor":
            # Thread pool for parallelizing multimedia generation
            resource = ThreadPoolExecutor(max_workers=4)

        elif name == "agent_alpha":
            from src.kaggle_stream.kaggle_agent import KaggleAgent
            resource = KaggleAgent(name="Eagle-Alpha")

        elif name == "agent_beta":
            from src.kaggle_stream.kaggle_agent import KaggleAgent
            resource = KaggleAgent(name="Falcon-Beta")

        elif name == "multimedia":
            from src.kaggle_stream.multimedia import MultimediaManager
            resource = MultimediaManager()

        elif name == "demo":
            import gradio as gr

            # Retrieve agents dynamically to trigger module attribute lookup (supports test mocking)
            app_module = sys.modules[__name__]
            alpha = getattr(app_module, "agent_alpha")
            beta = getattr(app_module, "agent_beta")

            with gr.Blocks(title="🦅 Antigravity AI Live Stream") as demo_obj:
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
            resource = demo_obj

        if resource is not None:
            _lazy_resources[name] = resource
            # Bind the resource directly to the module namespace to bypass __getattr__ on future lookups
            setattr(sys.modules[__name__], name, resource)
            return resource

        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

def __getattr__(name):
    """
    ⚡ Bolt: Module-level getattr interface to whitelist lazy variables.
    This defers import of heavy libraries like Gradio until actually requested.
    """
    if name in {"agent_alpha", "agent_beta", "multimedia", "executor", "demo"}:
        return _get_resource(name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

def run_agent_turn(agent, task, context="", return_futures=False):
    """
    Generic single turn for an agent.
    ⚡ Bolt: Supports returning futures for pipeline parallelization.
    """
    data = agent.step(task, context)
    message = data.get("message", "Working...")
    mood = data.get("mood", "thinking")

    # ⚡ Bolt: Access lazy attributes dynamically through the module to ensure correct patching/lazy loading
    app_module = sys.modules[__name__]
    executor_res = getattr(app_module, "executor")
    multimedia_res = getattr(app_module, "multimedia")

    # Parallelize multimedia generation to reduce latency
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
    current_task = task
    if mode == "Project Log Stream":
        from src.kaggle_stream.log_streamer import LogStreamer
        log_chunk = LogStreamer.get_context()
        current_task = f"As project auditors, discuss these recent logs and evaluate our progress: \n\n{log_chunk}"

    # ⚡ Bolt: Access agents dynamically to ensure correct test mocking and thread safety
    app_module = sys.modules[__name__]
    alpha = getattr(app_module, "agent_alpha")
    beta = getattr(app_module, "agent_beta")

    # 1. Start Alpha (returns futures for multimedia immediately after reasoning)
    msg_a, img_fut_a, aud_fut_a, thought_a = run_agent_turn(alpha, current_task, return_futures=True)

    # 2. Start Beta (Reasoning happens while Alpha's Audio/Images are still generating)
    msg_b, img_b, aud_b, thought_b = run_agent_turn(beta, current_task, context=thought_a)

    # 3. Finalize Alpha's assets
    img_a = img_fut_a.result()
    aud_a = aud_fut_a.result()

    return [msg_a, img_a, aud_a, msg_b, img_b, aud_b]

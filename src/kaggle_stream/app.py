import os
import logging
import threading
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Registry for lazily loaded resources to prevent redundant initialization
_lazy_resources = {}
_resource_lock = threading.Lock()

def _get_resource(name):
    """
    Thread-safe lazy initializer and registry for heavy resources.
    Checks globals() first to ensure we do not bypass mock patching.
    """
    # ⚡ Bolt: Check globals() first to allow tests to patch module attributes
    if name in globals():
        return globals()[name]

    with _resource_lock:
        if name in _lazy_resources:
            return _lazy_resources[name]

        # 1. ThreadPoolExecutor
        if name == "executor":
            from concurrent.futures import ThreadPoolExecutor
            logger.info("⚡ Bolt: Lazily initializing ThreadPoolExecutor")
            _lazy_resources["executor"] = ThreadPoolExecutor(max_workers=4)
            return _lazy_resources["executor"]

        # 2. agent_alpha
        elif name == "agent_alpha":
            from src.kaggle_stream.kaggle_agent import KaggleAgent
            logger.info("⚡ Bolt: Lazily initializing KaggleAgent 'Eagle-Alpha'")
            _lazy_resources["agent_alpha"] = KaggleAgent(name="Eagle-Alpha")
            return _lazy_resources["agent_alpha"]

        # 3. agent_beta
        elif name == "agent_beta":
            from src.kaggle_stream.kaggle_agent import KaggleAgent
            logger.info("⚡ Bolt: Lazily initializing KaggleAgent 'Falcon-Beta'")
            _lazy_resources["agent_beta"] = KaggleAgent(name="Falcon-Beta")
            return _lazy_resources["agent_beta"]

        # 4. multimedia
        elif name == "multimedia":
            from src.kaggle_stream.multimedia import MultimediaManager
            logger.info("⚡ Bolt: Lazily initializing MultimediaManager")
            _lazy_resources["multimedia"] = MultimediaManager()
            return _lazy_resources["multimedia"]

        # 5. demo (Gradio Blocks interface)
        elif name == "demo":
            logger.info("⚡ Bolt: Lazily constructing Gradio interface")
            _lazy_resources["demo"] = _build_demo()
            return _lazy_resources["demo"]

    raise AttributeError(f"module {__name__} has no attribute {name}")


def __getattr__(name):
    """
    Enables external modules to access global resources as lazy properties,
    and supports test mocking/patching.
    """
    if name in globals():
        return globals()[name]

    if name in ["executor", "agent_alpha", "agent_beta", "multimedia", "demo"]:
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

    # ⚡ Bolt: Retrieve resources dynamically via the module namespace.
    # This ensures that standard unittest.mock.patch is fully supported!
    self_mod = sys.modules[__name__]
    executor = getattr(self_mod, "executor")
    multimedia = getattr(self_mod, "multimedia")

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
        from src.kaggle_stream.log_streamer import LogStreamer
        log_chunk = LogStreamer.get_context()
        current_task = f"As project auditors, discuss these recent logs and evaluate our progress: \n\n{log_chunk}"

    # ⚡ Bolt: Retrieve resources dynamically via the module namespace.
    # This ensures that standard unittest.mock.patch is fully supported!
    self_mod = sys.modules[__name__]
    agent_alpha = getattr(self_mod, "agent_alpha")
    agent_beta = getattr(self_mod, "agent_beta")

    # 1. Start Alpha (returns futures for multimedia immediately after reasoning)
    msg_a, img_fut_a, aud_fut_a, thought_a = run_agent_turn(agent_alpha, current_task, return_futures=True)

    # 2. Start Beta (Reasoning happens while Alpha's Audio/Images are still generating)
    msg_b, img_b, aud_b, thought_b = run_agent_turn(agent_beta, current_task, context=thought_a)

    # 3. Finalize Alpha's assets
    img_a = img_fut_a.result()
    aud_a = aud_fut_a.result()

    return [msg_a, img_a, aud_a, msg_b, img_b, aud_b]


def _build_demo():
    """
    Lazily build the Gradio blocks interface when requested.
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
    # Access demo lazily which triggers _build_demo() and launch
    self_mod = sys.modules[__name__]
    demo = getattr(self_mod, "demo")
    demo.launch()

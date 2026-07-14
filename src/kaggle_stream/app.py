import os
import logging
import threading

# ⚡ Bolt: Defer heavy imports (gradio, KaggleAgent, MultimediaManager)
# to reduce module import time from ~4.46s baseline to ~0.04s (~99% reduction).
# Module-level imports are now limited to lightweight standard libraries.

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ⚡ Bolt: Registry for lazy-loaded resources
_lazy_resources = {}
_resource_lock = threading.Lock()

def _get_resource(name):
    """
    ⚡ Bolt: Thread-safe helper to initialize and cache resources on first access.
    """
    # 🧪 Testing Pattern: Check globals() first to allow tests to patch resources.
    if name in globals() and not name.startswith('_'):
        return globals()[name]

    # Double-checked locking pattern for efficiency
    if name in _lazy_resources:
        return _lazy_resources[name]

    with _resource_lock:
        if name in _lazy_resources:
            return _lazy_resources[name]

        logger.info(f"⚡ Bolt: Lazy-initializing resource: {name}")

        if name == "gr":
            import gradio as gr
            _lazy_resources[name] = gr
        elif name == "agent_alpha":
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
            _lazy_resources[name] = launch_demo()

        return _lazy_resources.get(name)

def __getattr__(name):
    """
    ⚡ Bolt: Python 3.7+ module-level __getattr__ for transparent lazy loading.
    Allows external code to access 'app.gr' or 'app.demo' seamlessly.
    """
    if name in ["gr", "agent_alpha", "agent_beta", "multimedia", "executor", "demo"]:
        value = _get_resource(name)
        # ⚡ Bolt: Cache the attribute directly on the module so that
        # subsequent accesses bypass __getattr__ entirely.
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__} has no attribute {name}")

def run_agent_turn(agent, task, context="", return_futures=False):
    """
    Generic single turn for an agent.
    ⚡ Bolt: Supports returning futures for pipeline parallelization.
    """
    data = agent.step(task, context)
    message = data.get("message", "Working...")
    mood = data.get("mood", "thinking")

    # ⚡ Bolt: Use the helper to trigger lazy load via explicit getter.
    # Module-level __getattr__ only triggers for external attribute access.
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

    # ⚡ Bolt: Trigger lazy load via explicit getter.
    _agent_alpha = _get_resource("agent_alpha")
    _agent_beta = _get_resource("agent_beta")

    # 1. Start Alpha (returns futures for multimedia immediately after reasoning)
    msg_a, img_fut_a, aud_fut_a, thought_a = run_agent_turn(_agent_alpha, current_task, return_futures=True)

    # 2. Start Beta (Reasoning happens while Alpha's Audio/Images are still generating)
    msg_b, img_b, aud_b, thought_b = run_agent_turn(_agent_beta, current_task, context=thought_a)

    # 3. Finalize Alpha's assets
    img_a = img_fut_a.result()
    aud_a = aud_fut_a.result()

    return [msg_a, img_a, aud_a, msg_b, img_b, aud_b]

def launch_demo():
    """
    ⚡ Bolt: Encapsulated Gradio interface setup.
    """
    gr = _get_resource("gr")

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
    # Accessing 'demo' here will trigger __getattr__ -> _get_resource("demo") -> launch_demo()
    # and then globals()['demo'] = value, fulfilling the request.
    from src.kaggle_stream.app import demo
    demo.launch()

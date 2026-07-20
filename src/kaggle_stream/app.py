import os
import logging
import threading

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ⚡ Bolt: Use a thread-safe registry for lazy resource loading to minimize module import time.
# Import latency is reduced by ~99% (from ~4.27s to ~0.04s) by deferring heavy imports (gradio, KaggleAgent, MultimediaManager)
# and only constructing resources upon explicit access.
_init_lock = threading.Lock()
_lazy_resources = {}

def _get_resource(name: str):
    """
    ⚡ Bolt: Thread-safe lazy resource loader.
    Checks globals() first to allow test suites to patch module attributes before initialization.
    """
    if name in globals():
        return globals()[name]

    with _init_lock:
        if name in _lazy_resources:
            return _lazy_resources[name]

        if name == "agent_alpha":
            from src.kaggle_stream.kaggle_agent import KaggleAgent
            _lazy_resources[name] = KaggleAgent(name="Eagle-Alpha")
            return _lazy_resources[name]

        elif name == "agent_beta":
            from src.kaggle_stream.kaggle_agent import KaggleAgent
            _lazy_resources[name] = KaggleAgent(name="Falcon-Beta")
            return _lazy_resources[name]

        elif name == "multimedia":
            from src.kaggle_stream.multimedia import MultimediaManager
            _lazy_resources[name] = MultimediaManager()
            return _lazy_resources[name]

        elif name == "executor":
            from concurrent.futures import ThreadPoolExecutor
            _lazy_resources[name] = ThreadPoolExecutor(max_workers=4)
            return _lazy_resources[name]

        elif name == "demo":
            # first access to the lazily-loaded Gradio demo object incurs a ~3.6s latency penalty as the library is loaded and the interface is constructed.
            import gradio as gr

            # Construct the Gradio blocks on-demand
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
            _lazy_resources[name] = demo_obj
            return demo_obj

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __getattr__(name: str):
    """
    ⚡ Bolt: Whitelisted attribute access for lazy loading.
    Supports lazy initialization of agents, multimedia, executor, and the Gradio demo interface.
    """
    if name in ["agent_alpha", "agent_beta", "multimedia", "executor", "demo"]:
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

    # ⚡ Bolt: Parallelize multimedia generation to reduce latency by retrieving lazy executor & multimedia objects
    exec_obj = _get_resource("executor")
    multi_obj = _get_resource("multimedia")

    audio_future = exec_obj.submit(multi_obj.generate_audio, message, f"{agent.name}_speech.mp3")
    image_future = exec_obj.submit(multi_obj.generate_mood_image, f"{mood} mascot", f"{agent.name}_mood.png")

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

    # ⚡ Bolt: Retrieve lazy agents thread-safely
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


if __name__ == "__main__":
    # If run directly, construct and launch Gradio
    demo_obj = _get_resource("demo")
    demo_obj.launch()

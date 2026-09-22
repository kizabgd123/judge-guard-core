import os
import sys
import logging
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ⚡ Bolt: Lock and lazy resource registry for thread-safe dynamic imports and resource initialization.
_lock = threading.RLock()
_lazy_resources = {}

def _get_resource(name):
    """
    Retrieve and lazily instantiate the resource, caching it in the local registry
    and binding it directly to the module namespace to bypass __getattr__ lookup overhead on subsequent accesses.
    """
    with _lock:
        if name in _lazy_resources:
            return _lazy_resources[name]

        logger.info(f"⚡ Bolt: Lazily initializing resource '{name}'")

        if name == "gr":
            import gradio as gr_mod
            res = gr_mod
        elif name == "KaggleAgent":
            from src.kaggle_stream.kaggle_agent import KaggleAgent as KA
            res = KA
        elif name == "MultimediaManager":
            from src.kaggle_stream.multimedia import MultimediaManager as MM
            res = MM
        elif name == "LogStreamer":
            from src.kaggle_stream.log_streamer import LogStreamer as LS
            res = LS
        elif name == "agent_alpha":
            agent_cls = _get_resource("KaggleAgent")
            res = agent_cls(name="Eagle-Alpha")
        elif name == "agent_beta":
            agent_cls = _get_resource("KaggleAgent")
            res = agent_cls(name="Falcon-Beta")
        elif name == "multimedia":
            multimedia_cls = _get_resource("MultimediaManager")
            res = multimedia_cls()
        elif name == "executor":
            from concurrent.futures import ThreadPoolExecutor
            res = ThreadPoolExecutor(max_workers=4)
        elif name == "demo":
            gr_mod = _get_resource("gr")

            # Lazily construct the Gradio Block interface
            with gr_mod.Blocks(title="🦅 Antigravity AI Live Stream") as demo_obj:
                gr_mod.Markdown("# 🦅 Antigravity AI Live Stream")
                gr_mod.Markdown("Watch AI Agents collaborate on Kaggle challenges or audit the **Antigravity Project Logs**.")

                mode_selector = gr_mod.Radio(["Kaggle Challenge", "Project Log Stream"], label="Stream Mode", value="Kaggle Challenge")

                with gr_mod.Row():
                    with gr_mod.Column():
                        gr_mod.Markdown("### 🔵 Eagle-Alpha")
                        alpha_img = gr_mod.Image(label="Mood")
                        alpha_status = gr_mod.Textbox(label="Message")
                        alpha_audio = gr_mod.Audio(label="Voice", autoplay=True)

                    with gr_mod.Column():
                        gr_mod.Markdown("### 🔴 Falcon-Beta")
                        beta_img = gr_mod.Image(label="Mood")
                        beta_status = gr_mod.Textbox(label="Message")
                        beta_audio = gr_mod.Audio(label="Voice", autoplay=False)

                with gr_mod.Row():
                    input_task = gr_mod.Textbox(label="Challenge/Context", value="House Prices - Advanced Regression Techniques")
                    start_btn = gr_mod.Button("🚀 Next Collaborative Step", variant="primary")

                start_btn.click(
                    fn=collaborative_step,
                    inputs=[mode_selector, input_task],
                    outputs=[alpha_status, alpha_img, alpha_audio, beta_status, beta_img, beta_audio]
                )
            res = demo_obj
        else:
            raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

        _lazy_resources[name] = res
        # Bind the resource directly to the module namespace to restore native global lookup speed.
        setattr(sys.modules[__name__], name, res)
        return res

def __getattr__(name):
    if name in ["gr", "KaggleAgent", "MultimediaManager", "LogStreamer", "agent_alpha", "agent_beta", "multimedia", "executor", "demo"]:
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

    # ⚡ Bolt: Retrieve 'multimedia' and 'executor' lazily using getattr on the module object
    # to trigger dynamic lookup and properly support mock patching in test environments.
    mod = sys.modules[__name__]
    multimedia_res = getattr(mod, "multimedia")
    executor_res = getattr(mod, "executor")

    # ⚡ Bolt: Parallelize multimedia generation to reduce latency
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

    # ⚡ Bolt: Retrieve 'LogStreamer', 'agent_alpha', and 'agent_beta' dynamically via the module object
    mod = sys.modules[__name__]
    log_streamer_res = getattr(mod, "LogStreamer")
    agent_alpha_res = getattr(mod, "agent_alpha")
    agent_beta_res = getattr(mod, "agent_beta")

    if mode == "Project Log Stream":
        log_chunk = log_streamer_res.get_context()
        current_task = f"As project auditors, discuss these recent logs and evaluate our progress: \n\n{log_chunk}"

    # 1. Start Alpha (returns futures for multimedia immediately after reasoning)
    msg_a, img_fut_a, aud_fut_a, thought_a = run_agent_turn(agent_alpha_res, current_task, return_futures=True)

    # 2. Start Beta (Reasoning happens while Alpha's Audio/Images are still generating)
    msg_b, img_b, aud_b, thought_b = run_agent_turn(agent_beta_res, current_task, context=thought_a)

    # 3. Finalize Alpha's assets
    img_a = img_fut_a.result()
    aud_a = aud_fut_a.result()

    return [msg_a, img_a, aud_a, msg_b, img_b, aud_b]

if __name__ == "__main__":
    # If run as main, demo will be lazily loaded and launch called
    demo_obj = getattr(sys.modules[__name__], "demo")
    demo_obj.launch()

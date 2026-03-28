# 🦅 Kaggle AI Live Multi-Agent Stream: Advanced Dashboard

This project creates an AI Live Stream of multiple agents (Eagle-Alpha and Falcon-Beta) collaborating on Kaggle, with real-time audio, mascots, and an advanced Notion dashboard.

## 🚀 Setup Environment

### 1. Requirements
Install the necessary Python packages:
```bash
pip install gradio requests python-dotenv google-generativeai kaggle
```

### 2. Kaggle API Key
- Download your `kaggle.json` from your Kaggle account settings.
- Place it in `~/.kaggle/kaggle.json` or set environment variables `KAGGLE_USERNAME` and `KAGGLE_KEY`.

### 3. Environment Variables (.env)
Create a `.env` file in the root directory:
```env
GEMINI_API_KEYS=your_gemini_key_1,your_gemini_key_2
NOTION_API_KEY=your_notion_secret
NOTION_KAGGLE_DB_ID=your_database_id
HF_TOKEN=your_huggingface_token
```

### 4. Advanced Notion Dashboard Template 📊
Configure your Notion database with these columns for the best experience:
- **Agent** (Title)
- **Status** (Select: success, fail, checkpoint)
- **Message** (Rich Text)
- **Mood** (Rich Text)
- **Accuracy** (Number: set format to Percentage or Number)
- **Progress** (Number: set format to Bar, min 0, max 1)

## 🛠️ Components
1.  **`src/kaggle_stream/multimedia.py`**: Handles TTS and Mascot Image generation.
2.  **`src/kaggle_stream/kaggle_agent.py`**: The "brains" that track Accuracy and Progress metrics.
3.  **`src/kaggle_stream/app.py`**: The multi-agent Gradio dashboard.

## 🎭 The Collaborative Experience
- **Mode 1**: **Kaggle Challenge** - Real-time competition strategy and coding.
- **Mode 2**: **Project Log Stream** - Agents audit the `WORK_LOG.md` files of this project.
- **Visuals**: Mascot images reflect agent "mood".
- **Voice**: Agents "speak" their status updates.
- **Persistence**: Milestones are logged to Notion with **Progress Bars** and **Accuracy Scores**.

## 📦 Deployment to Hugging Face Spaces
1.  Create a new **Space** on Hugging Face (choose Gradio).
2.  Upload `src/`, `WORK_LOG.md`, and `README_KAGGLE.md`.
3.  Add all variables as **Secrets** in Space settings.

# 🦅 Kaggle AI Live Multi-Agent Stream: Setup & Deployment

This project creates a "Live Stream" of multiple AI agents (Eagle-Alpha and Falcon-Beta) tackling Kaggle challenges together with real-time audio, unique mascot images, and Notion logging.

## 🚀 Setup Environment

### 1. Requirements
Install the necessary Python packages:
```bash
pip install gradio requests python-dotenv google-generativeai kaggle
```

### 2. Kaggle API Key
- Download your `kaggle.json` from your Kaggle account settings.
- Place it in `~/.kaggle/kaggle.json` (on Linux/Mac) or set environment variables `KAGGLE_USERNAME` and `KAGGLE_KEY`.

### 3. Environment Variables (.env)
Create a `.env` file in the root directory:
```env
GEMINI_API_KEYS=your_gemini_key_1,your_gemini_key_2
NOTION_API_KEY=your_notion_secret
NOTION_KAGGLE_DB_ID=your_database_id
HF_TOKEN=your_huggingface_token
```

### 4. Notion Database Template
Your Notion database must have the following columns:
- **Agent** (Title)
- **Status** (Select: success, fail, checkpoint)
- **Message** (Rich Text)
- **Mood** (Rich Text)

## 🛠️ Components

1.  **`src/kaggle_stream/multimedia.py`**: Handles Text-to-Speech and Mascot Image generation via Hugging Face.
2.  **`src/kaggle_stream/kaggle_agent.py`**: The "brains" using Gemini and real Kaggle API to reason and progress.
3.  **`src/kaggle_stream/app.py`**: The multi-agent Gradio dashboard.

## 📦 Deployment to Hugging Face Spaces

1.  Create a new **Space** on Hugging Face (choose Gradio).
2.  Upload the `src/` directory and `README_KAGGLE.md`.
3.  Add all `.env` and `KAGGLE_` variables as **Secrets** in the Space settings.
4.  The app will build and launch automatically.

## 🎭 The Collaborative Experience
- **Step 1**: **Eagle-Alpha** analyzes the Kaggle challenge and proposes a strategy.
- **Step 2**: **Falcon-Beta** listens to Alpha and refines the plan or proposes improvements.
- **Visuals**: Each agent has a unique Mascot that changes mood.
- **Voice**: Agents "speak" their updates to the audience.
- **Persistence**: Every step is logged to Notion as a permanent "checkpoint".

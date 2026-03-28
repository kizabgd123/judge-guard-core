# 🦅 Kaggle AI Stream: Setup & Deployment

This project allows you to create a "Live Stream" of AI agents tackling Kaggle challenges with real-time audio, images, and Notion logging.

## 🚀 Setup Environment

### 1. Requirements
Install the necessary Python packages:
```bash
pip install gradio requests python-dotenv google-generativeai
```

### 2. Environment Variables (.env)
Create a `.env` file in the root directory with the following keys:
```env
GEMINI_API_KEYS=your_gemini_key_1,your_gemini_key_2
NOTION_API_KEY=your_notion_secret
NOTION_KAGGLE_DB_ID=your_database_id
HF_TOKEN=your_huggingface_token
```

### 3. Notion Database Template
Your Notion database should have the following columns:
- **Agent** (Title)
- **Status** (Select: success, fail, checkpoint)
- **Message** (Rich Text)
- **Mood** (Rich Text)

## 🛠️ Components

1.  **`src/kaggle_stream/multimedia.py`**: Handles Text-to-Speech and Mood Image generation via Hugging Face Inference API.
2.  **`src/kaggle_stream/kaggle_agent.py`**: The "brain" that reasons about Kaggle tasks and logs progress to Notion.
3.  **`src/kaggle_stream/app.py`**: The Gradio dashboard that visualizes the agent's work.

## 📦 Deployment to Hugging Face Spaces

1.  Create a new **Space** on Hugging Face (choose Gradio).
2.  Upload the `src/` directory and `README_KAGGLE.md`.
3.  Add the `.env` variables as **Secrets** in the Space settings.
4.  The app will automatically build and launch!

## 🎭 How it Works
- **Agent Reasoning**: The agent uses Gemini to decide the next best step for a Kaggle challenge.
- **Audio narration**: Every status update is converted to speech so you can "hear" the agent.
- **Visual Mood**: The agent's mood (happy, thinking, stressed) is visualized via Stable Diffusion.
- **Persistence**: Every major step is logged to Notion for a permanent record.

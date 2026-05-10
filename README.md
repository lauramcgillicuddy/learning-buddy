---
title: Learning Buddy 🌸
emoji: 🌸
colorFrom: pink
colorTo: purple
sdk: gradio
sdk_version: "4.40.0"
app_file: app.py
pinned: false
license: mit
short_description: Your AI-powered study companion — chat, quiz, and learn
---

# 🌸 Learning Buddy

An AI-powered study companion that can teach you anything — or become a specialist in *your* material.

## Features

- **💬 Chat** — ask anything, get clear explanations
- **🎓 Quiz** — generates and evaluates questions from your documents
- **📚 Knowledge Base** — upload PDFs, notes, or paste a URL to make the AI an expert on your specific content (your thesis, lecture notes, papers...)
- **🗣️ Voice** — optional British female voice output (Google TTS or ElevenLabs)
- **🤖 Reachy Mini** — physical robot animations when running locally

## Getting started

1. Go to **⚙️ Settings** and paste your API key for whichever AI provider you have
2. Optionally add a voice key for spoken responses
3. Start chatting — no documents needed, it works on general knowledge out of the box
4. Upload your own documents in **📚 Knowledge Base** to quiz yourself on specific material

## API Keys

| Service | Where to get it | Required? |
|---|---|---|
| **Gemini** (recommended) | [aistudio.google.com](https://aistudio.google.com) → Get API key | Pick one AI |
| **Anthropic** | [console.anthropic.com](https://console.anthropic.com) | provider |
| **OpenAI** | [platform.openai.com](https://platform.openai.com) | |
| **Google TTS** | Same key as Gemini | Optional (voice) |
| **ElevenLabs** | [elevenlabs.io](https://elevenlabs.io) | Optional (voice) |

## Running locally (with Reachy Mini)

```bash
git clone https://huggingface.co/spaces/your-username/learning-buddy
cd learning-buddy
pip install -r requirements-robot.txt
cp .env.example .env  # fill in your keys
python main.py ui
```

## Open source

MIT licensed. Built with [Gradio](https://gradio.app), [ChromaDB](https://www.trychroma.com), and your choice of AI provider.

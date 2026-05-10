"""Gradio web UI for Learning Buddy — pastel theme, HuggingFace Spaces compatible."""

import os
import io
import threading
import gradio as gr

# ── Pastel theme ──────────────────────────────────────────────────────────────
theme = gr.themes.Soft(
    primary_hue=gr.themes.colors.pink,
    secondary_hue=gr.themes.colors.purple,
    neutral_hue=gr.themes.colors.zinc,
    font=gr.themes.GoogleFont("DM Sans"),
).set(
    body_background_fill="#FFF5F7",
    body_background_fill_dark="#FFF5F7",
    block_background_fill="#FFFFFF",
    block_border_color="#F8C8D4",
    button_primary_background_fill="#F4A7B9",
    button_primary_background_fill_hover="#EF7FA0",
    button_primary_text_color="#FFFFFF",
    button_secondary_background_fill="#E8D5F5",
    button_secondary_background_fill_hover="#D8B4F8",
    button_secondary_text_color="#5B21B6",
    input_background_fill="#FFF0F5",
    input_border_color="#F4A7B9",
    slider_color="#F4A7B9",
)

CSS = """
h1 { color: #be185d !important; }
h3 { color: #7c3aed !important; }
.tab-nav button { font-weight: 600; }
.tab-nav button.selected { color: #be185d !important; border-bottom-color: #F4A7B9 !important; }
.welcome-box { background: linear-gradient(135deg, #FFF0F5, #F3E8FF); border-radius: 12px; padding: 1.2rem; border: 1px solid #F4A7B9; }
footer { display: none !important; }
"""

WELCOME = """
<div class="welcome-box">
<b>Welcome! 🌸</b> I can teach you <i>anything</i> using my general knowledge — no setup needed.<br>
Upload your own documents (thesis, notes, papers) in the <b>📚 Knowledge Base</b> tab to make me an expert on <i>your</i> material.<br>
Add your API keys in <b>⚙️ Settings</b> and optionally enable voice responses.
</div>
"""


# ── Env / config helpers ──────────────────────────────────────────────────────

def _env_path() -> str:
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".env"))


def _save_env(**kwargs) -> None:
    path = _env_path()
    existing: dict[str, str] = {}
    if os.path.exists(path):
        for line in open(path).readlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                existing[k.strip()] = v.strip()
    existing.update({k: v for k, v in kwargs.items() if v})
    with open(path, "w") as f:
        for k, v in existing.items():
            f.write(f"{k}={v}\n")


def _reload_config():
    import importlib, config
    importlib.reload(config)


def save_settings(ai_provider, ai_key, ai_model, tts_provider, elevenlabs_key, google_tts_key, voice_choice, reachy_host):
    provider_key_map = {"Gemini": "GEMINI_API_KEY", "Anthropic": "ANTHROPIC_API_KEY", "OpenAI": "OPENAI_API_KEY"}
    updates = {
        "AI_PROVIDER":  ai_provider.lower(),
        "TTS_PROVIDER": tts_provider.lower(),
        "REACHY_HOST":  reachy_host,
    }
    if ai_model.strip():
        updates["AI_MODEL"] = ai_model.strip()
    if ai_key.strip():
        updates[provider_key_map[ai_provider]] = ai_key.strip()
    if elevenlabs_key.strip():
        updates["ELEVENLABS_API_KEY"] = elevenlabs_key.strip()
    if google_tts_key.strip():
        updates["GOOGLE_TTS_KEY"] = google_tts_key.strip()
    if voice_choice:
        key = "ELEVENLABS_VOICE_ID" if tts_provider == "ElevenLabs" else "GOOGLE_TTS_VOICE"
        updates[key] = voice_choice

    _save_env(**updates)
    _reload_config()
    return "✓ Settings saved!"


# ── TTS — returns audio bytes for Gradio's Audio component ───────────────────

def _tts_bytes(text: str) -> bytes | None:
    """Return MP3 bytes or None if TTS is not configured."""
    try:
        import config
        match config.TTS_PROVIDER.lower():
            case "google":
                if not config.GOOGLE_TTS_VOICE:
                    return None
                from google.cloud import texttospeech
                client = texttospeech.TextToSpeechClient()
                resp = client.synthesize_speech(
                    input=texttospeech.SynthesisInput(text=text),
                    voice=texttospeech.VoiceSelectionParams(
                        language_code="en-GB",
                        name=config.GOOGLE_TTS_VOICE,
                    ),
                    audio_config=texttospeech.AudioConfig(
                        audio_encoding=texttospeech.AudioEncoding.MP3,
                    ),
                )
                return resp.audio_content
            case "elevenlabs":
                if not config.ELEVENLABS_API_KEY:
                    return None
                from elevenlabs.client import ElevenLabs
                from elevenlabs import VoiceSettings
                client = ElevenLabs(api_key=config.ELEVENLABS_API_KEY)
                audio = client.text_to_speech.convert(
                    voice_id=config.ELEVENLABS_VOICE_ID,
                    text=text,
                    model_id="eleven_turbo_v2",
                    voice_settings=VoiceSettings(stability=0.55, similarity_boost=0.80),
                    output_format="mp3_22050_32",
                )
                return bytes(audio)
    except Exception:
        return None


def _reachy(fn_name: str, *args):
    """Call a reachy controller function safely in a background thread."""
    try:
        from reachy import controller
        fn = getattr(controller, fn_name, None)
        if fn:
            threading.Thread(target=fn, args=args, daemon=True).start()
    except Exception:
        pass


# ── Chat ──────────────────────────────────────────────────────────────────────

def chat_respond(message, history, use_kb, voice_on):
    if not message.strip():
        return history, "", None

    _reachy("antenna_thinking")

    from ai.client import chat
    reply = chat(message, use_knowledge=use_kb)

    _reachy("antenna_happy")
    history = history + [(message, reply)]
    audio = _tts_bytes(reply) if voice_on else None
    return history, "", (22050, audio) if audio else None


def reset_chat():
    from ai.client import reset_conversation
    reset_conversation()
    return [], "", None


# ── Knowledge base ────────────────────────────────────────────────────────────

def add_file(file, name, tags):
    from knowledge.ingestion import ingest
    from knowledge.store import add_document
    if file is None:
        return "No file selected.", _kb_status()
    label = name.strip() or os.path.basename(file.name)
    chunks, kind = ingest(file.name)
    count = add_document(chunks, source=label, tags=[t.strip() for t in tags.split(",") if t.strip()])
    return f"✓ Added **{label}** — {count} chunks ({kind})", _kb_status()


def add_url(url, name, tags):
    from knowledge.ingestion import ingest
    from knowledge.store import add_document
    if not url.strip():
        return "No URL provided.", _kb_status()
    label = name.strip() or url
    try:
        chunks, kind = ingest(url)
        count = add_document(chunks, source=label, tags=[t.strip() for t in tags.split(",") if t.strip()])
        return f"✓ Added **{label}** — {count} chunks ({kind})", _kb_status()
    except Exception as e:
        return f"Error: {e}", _kb_status()


def remove_doc(source):
    from knowledge.store import delete_source
    removed = delete_source(source)
    msg = f"✓ Removed **{source}** ({removed} chunks)" if removed else f"Nothing found: *{source}*"
    return msg, _kb_status()


def _kb_status() -> str:
    try:
        from knowledge.store import list_sources, count
        sources = list_sources()
        if not sources:
            return "📭 Knowledge base is empty — I'll use my general knowledge to help you!"
        total = count()
        rows = "\n".join(
            f"- **{s['source']}**" + (f" `{s['tags']}`" if s.get("tags") else "")
            for s in sources
        )
        return f"**{total} chunks** across {len(sources)} source(s)\n\n{rows}"
    except Exception:
        return "Knowledge base not initialised yet."


# ── Quiz ──────────────────────────────────────────────────────────────────────

_quiz_state: dict = {}


def start_quiz(topic, count, voice_on):
    from ai.quiz import generate_questions
    try:
        questions = generate_questions(topic=topic or None, count=int(count))
    except ValueError as e:
        return str(e), "", gr.update(visible=False), gr.update(visible=False), None

    _quiz_state.clear()
    _quiz_state.update({"questions": questions, "idx": 0, "score": 0, "answered": 0})
    return *_next_q(voice_on), None


def _next_q(voice_on=False):
    qs = _quiz_state.get("questions", [])
    idx = _quiz_state.get("idx", 0)
    if idx >= len(qs):
        answered = _quiz_state["answered"]
        score = _quiz_state["score"]
        avg = score / answered if answered else 0
        medal = "🌸 Excellent!" if avg >= 8 else "💜 Good effort!" if avg >= 5 else "🌷 Keep practising!"
        summary = f"### Quiz complete!\n**Score: {score}/{answered * 10}** ({avg:.0f}/10 average)\n\n{medal}"
        return summary, "", gr.update(visible=False), gr.update(visible=True)
    q = qs[idx]
    status = f"**Question {idx + 1} of {len(qs)}**"
    audio = _tts_bytes(q["question"]) if voice_on else None
    return status, q["question"], gr.update(visible=True), gr.update(visible=False)


def submit_answer(user_answer, voice_on):
    from ai.quiz import evaluate_answer
    qs = _quiz_state.get("questions", [])
    idx = _quiz_state.get("idx", 0)
    if idx >= len(qs) or not user_answer.strip():
        return *_next_q(voice_on), None, ""

    q = qs[idx]
    result = evaluate_answer(q["question"], q["answer"], user_answer)
    score = result.get("score", 0)
    _quiz_state["score"] = _quiz_state.get("score", 0) + score
    _quiz_state["answered"] = _quiz_state.get("answered", 0) + 1
    _quiz_state["idx"] = idx + 1

    correct = result.get("correct") or score >= 7
    _reachy("antenna_happy" if correct else "antenna_droop")

    feedback = result["feedback"]
    if not correct:
        feedback += f"\n\n*Correct answer: {q['answer']}*"
    feedback_line = ("✓ " if correct else "✗ ") + feedback + f" *(+{score}/10)*"

    status, question, ans_vis, done_vis = _next_q(voice_on)
    combined = f"{feedback_line}\n\n---\n\n{question}" if question else feedback_line
    audio = _tts_bytes(feedback) if voice_on else None
    return status, combined, ans_vis, done_vis, audio, ""


# ── Build UI ──────────────────────────────────────────────────────────────────

def build_ui() -> gr.Blocks:
    with gr.Blocks(theme=theme, css=CSS, title="Learning Buddy 🌸") as demo:

        gr.Markdown("# 🌸 Learning Buddy")
        gr.Markdown("*Your AI-powered study companion*")
        gr.HTML(WELCOME)

        with gr.Tabs():

            # ── Chat ──────────────────────────────────────────────────────────
            with gr.Tab("💬 Chat"):
                chatbot = gr.Chatbot(label="", height=400, bubble_full_width=False)
                audio_out = gr.Audio(label="", autoplay=True, visible=True, show_download_button=False)
                with gr.Row():
                    msg_box = gr.Textbox(placeholder="Ask me anything...", show_label=False, scale=5)
                    send_btn = gr.Button("Send 🌸", variant="primary", scale=1)
                with gr.Row():
                    use_kb = gr.Checkbox(value=True, label="Use my knowledge base")
                    voice_on = gr.Checkbox(value=False, label="Voice responses")
                    reset_btn = gr.Button("Reset chat", variant="secondary")

                send_btn.click(chat_respond, [msg_box, chatbot, use_kb, voice_on], [chatbot, msg_box, audio_out])
                msg_box.submit(chat_respond, [msg_box, chatbot, use_kb, voice_on], [chatbot, msg_box, audio_out])
                reset_btn.click(reset_chat, outputs=[chatbot, msg_box, audio_out])

            # ── Quiz ──────────────────────────────────────────────────────────
            with gr.Tab("🎓 Quiz Me"):
                with gr.Row():
                    quiz_topic = gr.Textbox(placeholder="Topic (optional — blank = anything in knowledge base)", label="Focus topic", scale=3)
                    quiz_count = gr.Slider(minimum=3, maximum=20, value=5, step=1, label="Questions", scale=1)
                quiz_voice = gr.Checkbox(value=False, label="Read questions aloud")
                start_btn = gr.Button("Start quiz ✨", variant="primary")

                quiz_status  = gr.Markdown("")
                quiz_display = gr.Markdown("")
                quiz_audio   = gr.Audio(label="", autoplay=True, visible=False, show_download_button=False)

                with gr.Column(visible=False) as answer_col:
                    answer_box  = gr.Textbox(placeholder="Your answer...", label="Your answer", lines=2)
                    submit_btn  = gr.Button("Submit answer 💜", variant="primary")

                with gr.Column(visible=False) as done_col:
                    restart_btn = gr.Button("New quiz 🌸", variant="secondary")

                start_btn.click(
                    start_quiz,
                    [quiz_topic, quiz_count, quiz_voice],
                    [quiz_status, quiz_display, answer_col, done_col, quiz_audio],
                )
                submit_btn.click(
                    submit_answer,
                    [answer_box, quiz_voice],
                    [quiz_status, quiz_display, answer_col, done_col, quiz_audio, answer_box],
                )
                restart_btn.click(
                    start_quiz,
                    [quiz_topic, quiz_count, quiz_voice],
                    [quiz_status, quiz_display, answer_col, done_col, quiz_audio],
                )

            # ── Knowledge base ────────────────────────────────────────────────
            with gr.Tab("📚 Knowledge Base"):
                kb_display = gr.Markdown(_kb_status())
                gr.Markdown("*Without any documents I'll use my general knowledge — upload your own to make me an expert on your specific material.*")

                gr.Markdown("### ➕ Add documents")
                with gr.Tabs():
                    with gr.Tab("Upload file"):
                        file_input = gr.File(file_types=[".pdf", ".md", ".txt"], label="PDF, Markdown or plain text")
                        with gr.Row():
                            file_name = gr.Textbox(placeholder="Friendly name (optional)", label="Name", scale=2)
                            file_tags = gr.Textbox(placeholder="e.g.  msc, biology", label="Tags", scale=2)
                        file_btn = gr.Button("Add to knowledge base 📎", variant="primary")

                    with gr.Tab("Fetch from URL"):
                        url_input = gr.Textbox(placeholder="https://...", label="URL")
                        with gr.Row():
                            url_name = gr.Textbox(placeholder="Friendly name (optional)", label="Name", scale=2)
                            url_tags = gr.Textbox(placeholder="e.g.  papers, msc", label="Tags", scale=2)
                        url_btn = gr.Button("Fetch & add 🌐", variant="primary")

                kb_msg = gr.Markdown("")
                file_btn.click(add_file, [file_input, file_name, file_tags], [kb_msg, kb_display])
                url_btn.click(add_url,   [url_input, url_name, url_tags],    [kb_msg, kb_display])

                gr.Markdown("### ➖ Remove a document")
                with gr.Row():
                    remove_name = gr.Textbox(placeholder="Exact source name to remove", label="", scale=3)
                    remove_btn  = gr.Button("Remove 🗑️", variant="stop", scale=1)
                remove_msg = gr.Markdown("")
                remove_btn.click(remove_doc, [remove_name], [remove_msg, kb_display])

            # ── Settings ──────────────────────────────────────────────────────
            with gr.Tab("⚙️ Settings"):
                gr.Markdown("### 🤖 AI Provider")
                gr.Markdown("*Pick whichever AI you have a key for — they all work the same way.*")
                with gr.Row():
                    ai_provider = gr.Dropdown(choices=["Gemini", "Anthropic", "OpenAI"], value="Gemini", label="Provider", scale=1)
                    ai_key      = gr.Textbox(placeholder="Paste API key here", label="API Key", type="password", scale=3)
                ai_model = gr.Textbox(placeholder="Optional model override (e.g. gemini-2.0-flash, gpt-4o-mini)", label="Model")

                gr.Markdown("### 🗣️ Voice")
                gr.Markdown("*Optional — leave blank to use text-only mode.*")
                with gr.Row():
                    tts_provider    = gr.Dropdown(choices=["Google", "ElevenLabs"], value="Google", label="TTS Provider", scale=1)
                    elevenlabs_key  = gr.Textbox(placeholder="ElevenLabs API key (if using ElevenLabs)", label="ElevenLabs Key", type="password", scale=2)
                    google_tts_key  = gr.Textbox(placeholder="Google API key (if using Google TTS)", label="Google TTS Key", type="password", scale=2)
                voice_choice = gr.Dropdown(
                    choices=[
                        ("🇬🇧 en-GB-Journey-F — warm, natural RP female", "en-GB-Journey-F"),
                        ("🇬🇧 en-GB-Neural2-C — crisp, elegant RP female", "en-GB-Neural2-C"),
                        ("🇬🇧 en-GB-Neural2-A — softer British female", "en-GB-Neural2-A"),
                        ("Custom / ElevenLabs voice ID", "custom"),
                    ],
                    value="en-GB-Journey-F",
                    label="Voice",
                )

                gr.Markdown("### 🤖 Reachy Mini")
                gr.Markdown("*Only needed if running alongside a physical Reachy Mini.*")
                reachy_host = gr.Textbox(value="reachy.local", label="Reachy hostname / IP")

                save_btn    = gr.Button("Save settings 💾", variant="primary")
                save_status = gr.Markdown("")
                save_btn.click(
                    save_settings,
                    [ai_provider, ai_key, ai_model, tts_provider, elevenlabs_key, google_tts_key, voice_choice, reachy_host],
                    save_status,
                )

    return demo


def launch(share: bool = False):
    try:
        from reachy import controller
        controller.connect()
    except Exception:
        pass

    ui = build_ui()
    ui.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", 7860)),
        share=share,
        show_api=False,
    )

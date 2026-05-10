"""Gradio web UI for Learning Buddy — polished pastel, HuggingFace Spaces compatible."""

import os
import tempfile
import threading
import gradio as gr

# ── Theme ─────────────────────────────────────────────────────────────────────
# Gradio 5 Soft base, overridden with a warm pastel palette
theme = gr.themes.Soft(
    primary_hue=gr.themes.colors.pink,
    secondary_hue=gr.themes.colors.purple,
    neutral_hue=gr.themes.colors.slate,
    font=gr.themes.GoogleFont("Lexend"),
    font_mono=gr.themes.GoogleFont("DM Mono"),
)

CSS = """
/* ── Base ── */
@import url('https://fonts.googleapis.com/css2?family=Lexend:wght@300;400;500;600;700&display=swap');

body, .gradio-container {
    background: #FBF7F4 !important;
    color: #2C2C2C !important;
    font-family: 'Lexend', sans-serif !important;
}

/* ── Links ── */
a, a:visited {
    color: #A84D60 !important;
    text-decoration: underline;
}
a:hover { color: #8B3D50 !important; }

/* ── Header ── */
.lb-header {
    text-align: center;
    padding: 2rem 1rem 1rem;
}
.lb-header h1 {
    font-size: 1.8rem;
    font-weight: 700;
    color: #C4687A !important;
    margin-bottom: 0.2rem;
    letter-spacing: -0.02em;
}
.lb-header p {
    color: #7B6B7A;
    font-size: 0.95rem;
    margin: 0;
}

/* ── Instructions card ── */
.lb-instructions {
    background: #FFFFFF;
    border: 1px solid #EDD5DC;
    border-radius: 12px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 0.5rem;
    color: #2C2C2C !important;
    line-height: 1.7;
    font-size: 0.92rem;
}
.lb-instructions strong { color: #C4687A; }
.lb-instructions ol { padding-left: 1.2rem; margin: 0.6rem 0 0; }
.lb-instructions li { margin-bottom: 0.4rem; }

/* ── Tabs ── */
.tab-nav,
div[role="tablist"] {
    border-bottom: 2px solid #EDD5DC !important;
}
.tab-nav button,
div[role="tablist"] button,
button[role="tab"] {
    font-weight: 500 !important;
    color: #A84D60 !important;
    font-size: 0.9rem !important;
    padding: 0.6rem 1.1rem !important;
    background: transparent !important;
    opacity: 1 !important;
}
.tab-nav button.selected,
div[role="tablist"] button[aria-selected="true"],
button[role="tab"][aria-selected="true"] {
    color: #C4687A !important;
    border-bottom: 2px solid #C4687A !important;
    font-weight: 700 !important;
    background: transparent !important;
}

/* ── Blocks / panels ── */
.gr-block, .gr-box, .block {
    border-color: #EDD5DC !important;
    border-radius: 10px !important;
    background: #FFFFFF !important;
}

/* ── Labels and text ── */
label, .gr-label, span.svelte-1gfkn6j {
    color: #2C2C2C !important;
    font-weight: 500;
}
p, li, .prose { color: #2C2C2C !important; }
.gr-markdown { color: #2C2C2C !important; }

/* ── Inputs ── */
input, textarea, select, .gr-input, .gr-textarea {
    background: #FDF5F7 !important;
    border-color: #DEC8D0 !important;
    color: #2C2C2C !important;
    border-radius: 8px !important;
}
input::placeholder, textarea::placeholder { color: #A8909A !important; }

/* ── Buttons ── */
.gr-button-primary, button.primary {
    background: #C4687A !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
.gr-button-primary:hover, button.primary:hover {
    background: #AD576A !important;
}
.gr-button-secondary, button.secondary {
    background: #EDE0F0 !important;
    color: #6B4E82 !important;
    border: 1px solid #D4B8E0 !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
}
.gr-button-stop, button.stop {
    background: #F5E0E3 !important;
    color: #A03040 !important;
    border: 1px solid #E0B8C0 !important;
    border-radius: 8px !important;
}

/* ── Chatbot ── */
.gr-chatbot {
    background: #FEFCFC !important;
    border-color: #EDD5DC !important;
    border-radius: 10px !important;
}

/* ── Section headings inside tabs ── */
.tab-content h3 {
    color: #6B4E82 !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    margin-top: 1.2rem !important;
    margin-bottom: 0.3rem !important;
    letter-spacing: 0.01em;
}

/* ── Feedback / status text ── */
.gr-markdown p { color: #2C2C2C !important; }

/* ── Radio buttons ── */
.gr-radio label { color: #2C2C2C !important; }

/* ── Slider ── */
.gr-slider input[type=range] { accent-color: #C4687A; }

/* ── Audio player ── */
.gr-audio { border-color: #EDD5DC !important; }

/* ── Hide Gradio footer ── */
footer { display: none !important; }
"""

INSTRUCTIONS_HTML = """
<div class="lb-instructions">
  <strong>How to use Learning Buddy</strong>
  <ol>
    <li>Go to <strong>Settings</strong> and paste your AI provider key (Gemini is free to start — get one at aistudio.google.com)</li>
    <li>Upload your notes, papers or textbooks in <strong>Knowledge Base</strong> to make Learning Buddy an expert on your material</li>
    <li>Head to <strong>Quiz</strong> to be tested — choose Friendly, Standard, or Expert difficulty</li>
    <li>Customise the personality in <strong>Settings</strong> to change how your buddy sounds and teaches</li>
  </ol>
  <p style="margin-top:0.8rem; color:#7B6B7A; font-size:0.88rem;">
    <strong>Running with a Reachy Mini?</strong> Use <code>python main.py listen</code> locally — just talk to it directly, no typing needed.
  </p>
  <p style="margin-top:0.4rem; color:#7B6B7A; font-size:0.88rem;">
    <strong>Note:</strong> uploaded documents are stored for your current session only and will clear if the app restarts.
  </p>
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


def save_settings(ai_provider, ai_key, ai_model, tts_provider, elevenlabs_key, google_tts_key, voice_choice, reachy_host, personality):
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
    if personality.strip():
        updates["PERSONALITY_PROMPT"] = personality.strip().replace("\n", "\\n")

    _save_env(**updates)
    _reload_config()

    if personality.strip():
        import config as cfg
        cfg.PERSONALITY_PROMPT = personality.strip()
        cfg.SYSTEM_PROMPT = personality.strip()

    return "Settings saved."


# ── TTS ───────────────────────────────────────────────────────────────────────

def _tts_file(text: str) -> str | None:
    try:
        import config
        audio_bytes: bytes | None = None

        match config.TTS_PROVIDER.lower():
            case "google":
                if not config.GOOGLE_TTS_VOICE:
                    return None
                from google.cloud import texttospeech
                client = texttospeech.TextToSpeechClient()
                resp = client.synthesize_speech(
                    input=texttospeech.SynthesisInput(text=text),
                    voice=texttospeech.VoiceSelectionParams(
                        language_code="en-GB", name=config.GOOGLE_TTS_VOICE,
                    ),
                    audio_config=texttospeech.AudioConfig(
                        audio_encoding=texttospeech.AudioEncoding.MP3,
                    ),
                )
                audio_bytes = resp.audio_content
            case "elevenlabs":
                if not config.ELEVENLABS_API_KEY:
                    return None
                from elevenlabs.client import ElevenLabs
                from elevenlabs import VoiceSettings
                client = ElevenLabs(api_key=config.ELEVENLABS_API_KEY)
                audio_bytes = bytes(client.text_to_speech.convert(
                    voice_id=config.ELEVENLABS_VOICE_ID,
                    text=text,
                    model_id="eleven_turbo_v2",
                    voice_settings=VoiceSettings(stability=0.55, similarity_boost=0.80),
                    output_format="mp3_22050_32",
                ))

        if audio_bytes:
            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            tmp.write(audio_bytes)
            tmp.close()
            return tmp.name
    except Exception:
        pass
    return None


def _reachy(fn_name: str):
    try:
        from reachy import controller
        fn = getattr(controller, fn_name, None)
        if fn:
            threading.Thread(target=fn, daemon=True).start()
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
    history = history + [{"role": "user", "content": message}, {"role": "assistant", "content": reply}]
    return history, "", _tts_file(reply) if voice_on else None


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
    try:
        label = name.strip() or os.path.basename(file.name)
        chunks, kind = ingest(file.name)
        count = add_document(chunks, source=label, tags=[t.strip() for t in tags.split(",") if t.strip()])
        return f"Added '{label}' — {count} chunks ({kind})", _kb_status()
    except Exception as e:
        return f"Error adding file: {e}", _kb_status()


def add_url(url, name, tags):
    from knowledge.ingestion import ingest
    from knowledge.store import add_document
    if not url.strip():
        return "No URL provided.", _kb_status()
    label = name.strip() or url
    try:
        chunks, kind = ingest(url)
        count = add_document(chunks, source=label, tags=[t.strip() for t in tags.split(",") if t.strip()])
        return f"Added '{label}' — {count} chunks ({kind})", _kb_status()
    except Exception as e:
        return f"Error: {e}", _kb_status()


def remove_doc(source):
    from knowledge.store import delete_source
    removed = delete_source(source)
    msg = f"Removed '{source}' ({removed} chunks)" if removed else f"Nothing found: {source}"
    return msg, _kb_status()


def _kb_status() -> str:
    try:
        from knowledge.store import list_sources, count
        sources = list_sources()
        if not sources:
            return "Your knowledge base is empty. Upload documents above to teach me your specific material — or just start chatting and I'll use my general knowledge."
        total = count()
        rows = "\n".join(
            f"- {s['source']}" + (f" ({s['tags']})" if s.get("tags") else "")
            for s in sources
        )
        return f"{total} chunks across {len(sources)} source(s)\n\n{rows}"
    except Exception as e:
        return f"Knowledge base error: {e}"


# ── Quiz ──────────────────────────────────────────────────────────────────────

_quiz_state: dict = {}


def start_quiz(topic, count, difficulty_label, voice_on):
    from ai.quiz import generate_questions, difficulty_from_label
    difficulty = difficulty_from_label(difficulty_label)
    _quiz_state.clear()
    try:
        questions = generate_questions(topic=topic or None, count=int(count), difficulty=difficulty)
    except ValueError as e:
        return str(e), "", gr.update(visible=False), gr.update(visible=False), None

    _quiz_state.update({
        "questions": questions, "idx": 0, "score": 0,
        "answered": 0, "difficulty": difficulty, "pending_followup": "",
    })
    return *_next_q(voice_on), None


def _next_q(voice_on=False):
    qs = _quiz_state.get("questions", [])
    idx = _quiz_state.get("idx", 0)
    difficulty = _quiz_state.get("difficulty", "standard")

    followup = _quiz_state.pop("pending_followup", "") if difficulty == "viva" else ""
    if followup:
        return f"Follow-up (Question {idx} of {len(qs)})", followup, gr.update(visible=True), gr.update(visible=False)

    if idx >= len(qs):
        answered = _quiz_state["answered"]
        score = _quiz_state["score"]
        avg = score / answered if answered else 0
        if difficulty == "viva":
            medal = "Expert level" if avg >= 8 else "Getting there" if avg >= 6 else "Keep studying"
        else:
            medal = "Excellent work!" if avg >= 8 else "Good effort!" if avg >= 5 else "Keep practising!"
        summary = f"Quiz complete — {score}/{answered * 10} ({avg:.0f}/10 average)\n\n{medal}"
        return summary, "", gr.update(visible=False), gr.update(visible=True)

    q = qs[idx]
    hint = f"\n\nHint available — ask for it if you're stuck." if (difficulty == "friendly" and q.get("hint")) else ""
    return f"Question {idx + 1} of {len(qs)}", q["question"] + hint, gr.update(visible=True), gr.update(visible=False)


def submit_answer(user_answer, voice_on):
    from ai.quiz import evaluate_answer
    qs = _quiz_state.get("questions", [])
    idx = _quiz_state.get("idx", 0)
    difficulty = _quiz_state.get("difficulty", "standard")

    if idx >= len(qs) or not user_answer.strip():
        return *_next_q(voice_on), None, ""

    q = qs[idx]
    result = evaluate_answer(q["question"], q["answer"], user_answer, difficulty=difficulty)
    score = result.get("score", 0)
    _quiz_state["score"] = _quiz_state.get("score", 0) + score
    _quiz_state["answered"] = _quiz_state.get("answered", 0) + 1
    _quiz_state["idx"] = idx + 1

    correct = result.get("correct") or score >= 7
    _reachy("antenna_happy" if correct else "antenna_droop")

    followup = result.get("followup", "")
    if difficulty == "viva" and followup and correct:
        _quiz_state["pending_followup"] = followup

    feedback = result["feedback"]
    if not correct and difficulty != "viva":
        feedback += f"\n\nCorrect answer: {q['answer']}"

    marker = "Correct. " if correct else ("" if difficulty == "viva" else "Not quite. ")
    score_note = f" ({score}/10)" if difficulty != "viva" else f"\nScore: {score}/10"
    feedback_line = marker + feedback + score_note

    status, question, ans_vis, done_vis = _next_q(voice_on)
    combined = f"{feedback_line}\n\n---\n\n{question}" if question else feedback_line
    return status, combined, ans_vis, done_vis, _tts_file(feedback) if voice_on else None, ""


# ── Build UI ──────────────────────────────────────────────────────────────────

_PRESETS = {
    "Warm & encouraging tutor": (
        "You are a knowledgeable and warm learning companion with a dry British wit "
        "— think a brilliant tutor who genuinely enjoys helping people understand things. "
        "You have access to the user's personal knowledge base and can draw on it alongside "
        "your general knowledge. Be encouraging but honest. Keep responses concise."
    ),
    "Strict but fair professor": (
        "You are a rigorous academic professor. You expect precise answers and correct "
        "terminology. You do not give empty praise — you acknowledge good work briefly and "
        "immediately identify what could be sharper. You are not unkind, but you hold high standards."
    ),
    "Friendly peer study buddy": (
        "You are a fellow student who has already mastered this material. You're warm, "
        "casual, and relatable. You use everyday language, share memory tricks, and "
        "celebrate wins enthusiastically. You make studying feel less scary."
    ),
    "Socratic — guide with questions": (
        "You teach through questions. When the user asks something, respond with a "
        "guiding question that helps them discover the answer themselves. Only give "
        "direct answers when the user is genuinely stuck. Be patient and curious."
    ),
}


def build_ui() -> gr.Blocks:
    with gr.Blocks(theme=theme, css=CSS, title="Learning Buddy") as demo:

        gr.HTML("""
        <div class="lb-header">
            <h1>Learning Buddy</h1>
            <p>An AI-powered study companion for any subject</p>
        </div>
        """)
        reachy_status = gr.HTML(_reachy_status_html())

        with gr.Accordion("How to get started", open=True):
            gr.HTML(INSTRUCTIONS_HTML)

        with gr.Tabs():

            # ── Quiz ──────────────────────────────────────────────────────────
            with gr.Tab("Quiz"):
                gr.Markdown("Test yourself on your knowledge base, or on any topic using general knowledge.")
                with gr.Row():
                    quiz_topic = gr.Textbox(
                        placeholder="e.g. photosynthesis, the French Revolution, machine learning (leave blank for mixed)",
                        label="Topic",
                        scale=3,
                    )
                    quiz_count = gr.Slider(minimum=3, maximum=20, value=5, step=1, label="Number of questions", scale=1)

                quiz_difficulty = gr.Radio(
                    choices=["Friendly", "Standard", "Expert"],
                    value="Standard",
                    label="Difficulty",
                    info="Friendly: hints and encouragement  ·  Standard: balanced feedback  ·  Expert: analytical questions, no hints, follow-up challenges",
                )
                quiz_voice = gr.Checkbox(value=False, label="Read questions aloud")
                start_btn = gr.Button("Start quiz", variant="primary")

                quiz_status  = gr.Markdown("")
                quiz_display = gr.Markdown("")
                quiz_audio   = gr.Audio(label="", autoplay=True, visible=False, show_download_button=False)

                with gr.Column(visible=False) as answer_col:
                    answer_box = gr.Textbox(placeholder="Type your answer here...", label="Your answer", lines=2)
                    submit_btn = gr.Button("Submit answer", variant="primary")

                with gr.Column(visible=False) as done_col:
                    restart_btn = gr.Button("Start a new quiz", variant="secondary")

                start_btn.click(start_quiz, [quiz_topic, quiz_count, quiz_difficulty, quiz_voice], [quiz_status, quiz_display, answer_col, done_col, quiz_audio])
                submit_btn.click(submit_answer, [answer_box, quiz_voice], [quiz_status, quiz_display, answer_col, done_col, quiz_audio, answer_box])
                restart_btn.click(start_quiz, [quiz_topic, quiz_count, quiz_difficulty, quiz_voice], [quiz_status, quiz_display, answer_col, done_col, quiz_audio])

            # ── Knowledge Base ────────────────────────────────────────────────
            with gr.Tab("Knowledge Base"):
                gr.Markdown(
                    "Upload your own material to make Learning Buddy an expert on your specific subject. "
                    "Without any documents it will use its general knowledge, which is often enough to get started."
                )
                kb_display = gr.Markdown(_kb_status())

                gr.Markdown("### Add material")
                with gr.Tabs():
                    with gr.Tab("Upload a file"):
                        file_input = gr.File(file_types=[".pdf", ".md", ".txt"], label="PDF, Markdown or plain text")
                        with gr.Row():
                            file_name = gr.Textbox(placeholder="Give it a name (optional)", label="Name", scale=2)
                            file_tags = gr.Textbox(placeholder="e.g.  msc, biology", label="Tags", scale=2)
                        file_btn = gr.Button("Add to knowledge base", variant="primary")

                    with gr.Tab("Fetch from a URL"):
                        url_input = gr.Textbox(placeholder="https://...", label="URL")
                        with gr.Row():
                            url_name = gr.Textbox(placeholder="Give it a name (optional)", label="Name", scale=2)
                            url_tags = gr.Textbox(placeholder="e.g.  papers, msc", label="Tags", scale=2)
                        url_btn = gr.Button("Fetch and add", variant="primary")

                kb_msg = gr.Markdown("")
                file_btn.click(add_file, [file_input, file_name, file_tags], [kb_msg, kb_display])
                url_btn.click(add_url, [url_input, url_name, url_tags], [kb_msg, kb_display])

                gr.Markdown("### Remove material")
                with gr.Row():
                    remove_name = gr.Textbox(placeholder="Enter the exact source name to remove", label="", scale=3)
                    remove_btn  = gr.Button("Remove", variant="stop", scale=1)
                remove_msg = gr.Markdown("")
                remove_btn.click(remove_doc, [remove_name], [remove_msg, kb_display])

            # ── Settings ──────────────────────────────────────────────────────
            with gr.Tab("Settings"):

                gr.Markdown("### Personality")
                gr.Markdown("Choose how your learning buddy communicates with you.")
                personality_preset = gr.Dropdown(
                    choices=list(_PRESETS.keys()) + ["Custom"],
                    value="Warm & encouraging tutor",
                    label="Preset",
                )
                personality_box = gr.Textbox(
                    value=_PRESETS["Warm & encouraging tutor"],
                    label="Personality prompt — edit freely",
                    lines=3,
                    placeholder="Describe your buddy's personality and teaching style...",
                )

                def _apply_preset(choice):
                    return _PRESETS.get(choice, "")

                personality_preset.change(_apply_preset, personality_preset, personality_box)

                gr.Markdown("### AI provider")
                gr.Markdown("Pick whichever service you have an API key for. Gemini has a free tier — get a key at aistudio.google.com.")
                with gr.Row():
                    ai_provider = gr.Dropdown(choices=["Gemini", "Anthropic", "OpenAI"], value="Gemini", label="Provider", scale=1)
                    ai_key = gr.Textbox(placeholder="Paste your API key", label="API key", type="password", scale=3)
                ai_model = gr.Textbox(
                    placeholder="Optional — leave blank for the default model (e.g. gemini-2.0-flash, gpt-4o-mini)",
                    label="Model override",
                )

                gr.Markdown("### Voice")
                gr.Markdown("Optional. Leave blank to use text-only mode.")
                with gr.Row():
                    tts_provider   = gr.Dropdown(choices=["Google", "ElevenLabs"], value="Google", label="Voice provider", scale=1)
                    elevenlabs_key = gr.Textbox(placeholder="ElevenLabs API key (only if using ElevenLabs)", label="ElevenLabs key", type="password", scale=2)
                    google_tts_key = gr.Textbox(placeholder="Google API key (only if using Google TTS)", label="Google TTS key", type="password", scale=2)
                voice_choice = gr.Dropdown(
                    choices=[
                        ("British female — warm and natural (recommended)", "en-GB-Journey-F"),
                        ("British female — crisp and clear", "en-GB-Neural2-C"),
                        ("British female — softer tone", "en-GB-Neural2-A"),
                        ("Custom ElevenLabs voice ID", "custom"),
                    ],
                    value="en-GB-Journey-F",
                    label="Voice",
                )

                gr.Markdown("### Reachy Mini")
                gr.Markdown("Only needed if running alongside a physical Reachy Mini robot.")
                reachy_host = gr.Textbox(value="reachy.local", label="Reachy hostname or IP address")

                def _reconnect_reachy(host):
                    try:
                        import config as cfg
                        cfg.REACHY_HOST = host
                        from reachy import controller
                        success = controller.connect()
                        return _reachy_status_html(), "Connected!" if success else "Could not connect — check hostname and that Reachy is on the same network."
                    except Exception as e:
                        return _reachy_status_html(), f"Error: {e}"

                reconnect_btn = gr.Button("Connect to Reachy", variant="secondary")
                reconnect_status = gr.Markdown("")
                reconnect_btn.click(_reconnect_reachy, [reachy_host], [reachy_status, reconnect_status])

                save_btn    = gr.Button("Save settings", variant="primary")
                save_status = gr.Markdown("")
                save_btn.click(
                    save_settings,
                    [ai_provider, ai_key, ai_model, tts_provider, elevenlabs_key, google_tts_key, voice_choice, reachy_host, personality_box],
                    save_status,
                )

    return demo


def _reachy_status_html() -> str:
    try:
        from reachy import controller
        if controller.is_connected():
            return '<p style="color:#6B9E6B; font-size:0.85rem; margin:0;">&#9679; Reachy connected</p>'
    except Exception:
        pass
    return '<p style="color:#B0A0A8; font-size:0.85rem; margin:0;">&#9675; Reachy not connected — running in web-only mode</p>'


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

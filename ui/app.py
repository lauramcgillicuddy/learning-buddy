"""Gradio web UI for Learning Buddy — pastel theme, runs in Reachy's app panel."""

import os
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
footer { display: none !important; }
"""


# ── Settings helpers ──────────────────────────────────────────────────────────

def _save_env(**kwargs) -> None:
    """Write key=value pairs to .env, creating it if needed."""
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    env_path = os.path.normpath(env_path)
    existing = {}
    if os.path.exists(env_path):
        for line in open(env_path).readlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                existing[k.strip()] = v.strip()
    existing.update({k: v for k, v in kwargs.items() if v})
    with open(env_path, "w") as f:
        for k, v in existing.items():
            f.write(f"{k}={v}\n")


def save_settings(ai_provider, ai_key, ai_model, tts_provider, tts_key, voice_id, reachy_host):
    key_map = {
        "Gemini":    "GEMINI_API_KEY",
        "Anthropic": "ANTHROPIC_API_KEY",
        "OpenAI":    "OPENAI_API_KEY",
    }
    tts_key_map = {
        "Google":     None,   # uses same Google key as Gemini
        "ElevenLabs": "ELEVENLABS_API_KEY",
    }
    updates = {
        "AI_PROVIDER":  ai_provider.lower(),
        "AI_MODEL":     ai_model,
        "TTS_PROVIDER": tts_provider.lower(),
        "REACHY_HOST":  reachy_host,
    }
    if ai_key:
        updates[key_map[ai_provider]] = ai_key
    if tts_provider == "ElevenLabs" and tts_key:
        updates["ELEVENLABS_API_KEY"] = tts_key
    if voice_id:
        updates["ELEVENLABS_VOICE_ID" if tts_provider == "ElevenLabs" else "GOOGLE_TTS_VOICE"] = voice_id

    _save_env(**updates)

    # Reload config so changes take effect without restart
    import importlib, config
    importlib.reload(config)

    return "✓ Settings saved! Changes take effect immediately."


# ── Chat logic ────────────────────────────────────────────────────────────────

def _run_chat(message, history, use_kb):
    from ai.client import chat
    from reachy import controller

    threading.Thread(target=controller.antenna_thinking, daemon=True).start()
    reply = chat(message, use_knowledge=use_kb)
    threading.Thread(target=controller.antenna_happy, daemon=True).start()
    return reply


def chat_respond(message, history, use_kb):
    if not message.strip():
        return history, ""
    reply = _run_chat(message, history, use_kb)
    history = history + [(message, reply)]
    return history, ""


def reset_chat():
    from ai.client import reset_conversation
    reset_conversation()
    return [], ""


# ── Knowledge base ────────────────────────────────────────────────────────────

def add_file(file, name, tags):
    from knowledge.ingestion import ingest
    from knowledge.store import add_document
    if file is None:
        return "No file selected.", refresh_kb()
    label = name.strip() or os.path.basename(file.name)
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    chunks, kind = ingest(file.name)
    count = add_document(chunks, source=label, tags=tag_list)
    return f"✓ Added '{label}' — {count} chunks ({kind})", refresh_kb()


def add_url(url, name, tags):
    from knowledge.ingestion import ingest
    from knowledge.store import add_document
    if not url.strip():
        return "No URL provided.", refresh_kb()
    label = name.strip() or url
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    try:
        chunks, kind = ingest(url)
        count = add_document(chunks, source=label, tags=tag_list)
        return f"✓ Added '{label}' — {count} chunks ({kind})", refresh_kb()
    except Exception as e:
        return f"Error: {e}", refresh_kb()


def remove_doc(source):
    from knowledge.store import delete_source
    removed = delete_source(source)
    if removed:
        return f"✓ Removed '{source}' ({removed} chunks)", refresh_kb()
    return f"Nothing found with name '{source}'", refresh_kb()


def refresh_kb():
    from knowledge.store import list_sources, count
    sources = list_sources()
    if not sources:
        return "Knowledge base is empty — add some documents above!"
    total = count()
    rows = "\n".join(f"• **{s['source']}**  {('`' + s['tags'] + '`') if s.get('tags') else ''}" for s in sources)
    return f"**{total} chunks** across {len(sources)} source(s)\n\n{rows}"


# ── Quiz logic ────────────────────────────────────────────────────────────────

_quiz_state: dict = {}


def start_quiz(topic, count):
    from ai.quiz import generate_questions
    try:
        questions = generate_questions(topic=topic or None, count=int(count))
    except ValueError as e:
        return str(e), "", gr.update(visible=False), gr.update(visible=False)

    _quiz_state.clear()
    _quiz_state.update({"questions": questions, "idx": 0, "score": 0, "answered": 0})
    return _next_question()


def _next_question():
    qs = _quiz_state.get("questions", [])
    idx = _quiz_state.get("idx", 0)
    if idx >= len(qs):
        answered = _quiz_state["answered"]
        score = _quiz_state["score"]
        avg = score / answered if answered else 0
        medal = "🌸 Excellent!" if avg >= 8 else "💜 Good effort!" if avg >= 5 else "🌷 Keep going!"
        result = f"### Quiz complete!\n**Score: {score}/{answered * 10}** — {medal}"
        return result, "", gr.update(visible=False), gr.update(visible=True)
    q = qs[idx]
    status = f"Question {idx + 1} of {len(qs)}"
    return status, q["question"], gr.update(visible=True), gr.update(visible=False)


def submit_answer(user_answer):
    from ai.quiz import evaluate_answer
    from reachy import controller

    qs = _quiz_state.get("questions", [])
    idx = _quiz_state.get("idx", 0)
    if idx >= len(qs) or not user_answer.strip():
        return *_next_question(), ""

    q = qs[idx]
    result = evaluate_answer(q["question"], q["answer"], user_answer)
    score = result.get("score", 0)
    _quiz_state["score"] = _quiz_state.get("score", 0) + score
    _quiz_state["answered"] = _quiz_state.get("answered", 0) + 1
    _quiz_state["idx"] = idx + 1

    if result.get("correct") or score >= 7:
        threading.Thread(target=controller.antenna_happy, daemon=True).start()
        feedback = f"✓ {result['feedback']} *(+{score}/10)*"
    else:
        threading.Thread(target=controller.antenna_droop, daemon=True).start()
        feedback = f"✗ {result['feedback']}\n\n*Correct: {q['answer']}*  *(+{score}/10)*"

    status, question, ans_visible, done_visible = _next_question()
    return status, feedback + "\n\n---\n" + question, ans_visible, done_visible, ""


# ── Build UI ──────────────────────────────────────────────────────────────────

def build_ui() -> gr.Blocks:
    with gr.Blocks(theme=theme, css=CSS, title="Learning Buddy 🌸") as demo:
        gr.Markdown("# 🌸 Learning Buddy")
        gr.Markdown("*Your Reachy-powered study companion*")

        with gr.Tabs():

            # ── Chat ──────────────────────────────────────────────────────────
            with gr.Tab("💬 Chat"):
                chatbot = gr.Chatbot(label="", height=420, bubble_full_width=False)
                with gr.Row():
                    msg_box = gr.Textbox(
                        placeholder="Ask me anything...",
                        show_label=False,
                        scale=5,
                    )
                    send_btn = gr.Button("Send", variant="primary", scale=1)
                with gr.Row():
                    use_kb = gr.Checkbox(value=True, label="Use my knowledge base")
                    reset_btn = gr.Button("Reset conversation", variant="secondary")

                send_btn.click(chat_respond, [msg_box, chatbot, use_kb], [chatbot, msg_box])
                msg_box.submit(chat_respond, [msg_box, chatbot, use_kb], [chatbot, msg_box])
                reset_btn.click(reset_chat, outputs=[chatbot, msg_box])

            # ── Quiz ──────────────────────────────────────────────────────────
            with gr.Tab("🎓 Quiz"):
                with gr.Row():
                    quiz_topic = gr.Textbox(placeholder="Topic (optional — leave blank for anything)", label="Focus topic", scale=3)
                    quiz_count = gr.Slider(minimum=3, maximum=20, value=5, step=1, label="Questions", scale=1)
                start_btn = gr.Button("Start quiz ✨", variant="primary")

                quiz_status = gr.Markdown("")
                quiz_question = gr.Markdown("")
                with gr.Column(visible=False) as answer_col:
                    answer_box = gr.Textbox(placeholder="Your answer...", label="Answer", lines=2)
                    submit_btn = gr.Button("Submit", variant="primary")
                with gr.Column(visible=False) as done_col:
                    restart_btn = gr.Button("New quiz 🌸", variant="secondary")

                start_btn.click(
                    start_quiz,
                    [quiz_topic, quiz_count],
                    [quiz_status, quiz_question, answer_col, done_col],
                )
                submit_btn.click(
                    submit_answer,
                    [answer_box],
                    [quiz_status, quiz_question, answer_col, done_col, answer_box],
                )
                restart_btn.click(
                    start_quiz,
                    [quiz_topic, quiz_count],
                    [quiz_status, quiz_question, answer_col, done_col],
                )

            # ── Knowledge base ────────────────────────────────────────────────
            with gr.Tab("📚 Knowledge Base"):
                kb_display = gr.Markdown(refresh_kb())

                gr.Markdown("### Add a document")
                with gr.Tabs():
                    with gr.Tab("Upload file"):
                        file_input = gr.File(file_types=[".pdf", ".md", ".txt"], label="PDF, Markdown or text")
                        with gr.Row():
                            file_name = gr.Textbox(placeholder="Friendly name (optional)", label="Name", scale=2)
                            file_tags = gr.Textbox(placeholder="e.g. msc, biology", label="Tags", scale=2)
                        file_btn = gr.Button("Add to knowledge base", variant="primary")

                    with gr.Tab("Add URL"):
                        url_input = gr.Textbox(placeholder="https://...", label="URL")
                        with gr.Row():
                            url_name = gr.Textbox(placeholder="Friendly name (optional)", label="Name", scale=2)
                            url_tags = gr.Textbox(placeholder="e.g. papers, msc", label="Tags", scale=2)
                        url_btn = gr.Button("Fetch & add", variant="primary")

                file_status = gr.Markdown("")
                file_btn.click(add_file, [file_input, file_name, file_tags], [file_status, kb_display])
                url_btn.click(add_url, [url_input, url_name, url_tags], [file_status, kb_display])

                gr.Markdown("### Remove a document")
                with gr.Row():
                    remove_name = gr.Textbox(placeholder="Source name to remove", label="", scale=3)
                    remove_btn = gr.Button("Remove", variant="stop", scale=1)
                remove_status = gr.Markdown("")
                remove_btn.click(remove_doc, [remove_name], [remove_status, kb_display])

            # ── Settings ──────────────────────────────────────────────────────
            with gr.Tab("⚙️ Settings"):
                gr.Markdown("### AI Provider")
                with gr.Row():
                    ai_provider = gr.Dropdown(
                        choices=["Gemini", "Anthropic", "OpenAI"],
                        value="Gemini",
                        label="Provider",
                        scale=1,
                    )
                    ai_key = gr.Textbox(
                        placeholder="Paste your API key here",
                        label="API Key",
                        type="password",
                        scale=3,
                    )
                ai_model = gr.Textbox(
                    placeholder="Leave blank for default (e.g. gemini-2.0-flash)",
                    label="Model override (optional)",
                )

                gr.Markdown("### Voice / TTS")
                with gr.Row():
                    tts_provider = gr.Dropdown(
                        choices=["Google", "ElevenLabs"],
                        value="Google",
                        label="TTS Provider",
                        scale=1,
                    )
                    tts_key = gr.Textbox(
                        placeholder="ElevenLabs key (only needed if using ElevenLabs)",
                        label="ElevenLabs API Key",
                        type="password",
                        scale=3,
                    )
                voice_id = gr.Dropdown(
                    choices=[
                        ("en-GB-Journey-F — warm RP British female (recommended)", "en-GB-Journey-F"),
                        ("en-GB-Neural2-C — crisp, elegant British female", "en-GB-Neural2-C"),
                        ("en-GB-Neural2-A — softer British female", "en-GB-Neural2-A"),
                        ("Custom ElevenLabs voice ID", "custom"),
                    ],
                    value="en-GB-Journey-F",
                    label="Voice",
                )

                gr.Markdown("### Robot")
                reachy_host = gr.Textbox(value="reachy.local", label="Reachy hostname / IP")

                save_btn = gr.Button("Save settings 💾", variant="primary")
                save_status = gr.Markdown("")
                save_btn.click(
                    save_settings,
                    [ai_provider, ai_key, ai_model, tts_provider, tts_key, voice_id, reachy_host],
                    save_status,
                )

    return demo


def launch(share: bool = False):
    from reachy import controller
    controller.connect()

    ui = build_ui()
    ui.launch(
        server_name="0.0.0.0",  # visible on local network (Reachy's panel picks this up)
        server_port=7860,
        share=share,
        show_api=False,
    )

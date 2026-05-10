#!/usr/bin/env python3
"""Learning Buddy — entry point.

Commands:
  python main.py ui          → launch the Gradio web UI
  python main.py listen      → voice loop for Reachy (talk to it directly)
  python main.py chat        → terminal text chat
  python main.py quiz        → terminal quiz
  python main.py add <file>  → add a document to the knowledge base
  python main.py list        → list knowledge base
"""

import typer
from cli.interface import app


@app.command("ui")
def launch_ui(
    share: bool = typer.Option(False, "--share", help="Create a public Gradio share link"),
):
    """Launch the web UI (opens in browser / Reachy's app panel)."""
    from ui.app import launch
    launch(share=share)


@app.command("listen")
def listen_mode(
    duration: float = typer.Option(6.0, "--duration", "-d", help="Seconds to listen per turn"),
):
    """Start the voice loop — talk to Reachy directly, no typing needed."""
    from reachy import controller
    from reachy.voice_loop import run

    controller.connect()
    run(duration=duration)


if __name__ == "__main__":
    app()

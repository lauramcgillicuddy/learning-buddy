#!/usr/bin/env python3
"""Learning Buddy — entry point.

Commands:
  python main.py ui          → launch the Gradio web UI (default)
  python main.py chat        → terminal chat
  python main.py quiz        → terminal quiz
  python main.py add <file>  → add a document
  python main.py list        → list knowledge base
"""

import typer
from cli.interface import app

ui_app = typer.Typer()


@app.command("ui")
def launch_ui(
    share: bool = typer.Option(False, "--share", help="Create a public Gradio share link"),
):
    """Launch the web UI (opens in browser / Reachy's app panel)."""
    from ui.app import launch
    launch(share=share)


if __name__ == "__main__":
    app()

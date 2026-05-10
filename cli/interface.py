"""CLI commands for the Learning Buddy."""

from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

app = typer.Typer(help="Learning Buddy — your Reachy-powered study companion.")
console = Console()


@app.command("add")
def add_document(
    source: str = typer.Argument(..., help="Path to PDF/MD/text file, or a URL"),
    tags: str = typer.Option("", "--tags", "-t", help="Comma-separated tags"),
    name: str = typer.Option("", "--name", "-n", help="Friendly name for the source"),
):
    """Add a document or URL to the knowledge base."""
    from knowledge.ingestion import ingest
    from knowledge.store import add_document as store_add

    label = name or source
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    with console.status(f"[cyan]Ingesting {label}...[/cyan]"):
        try:
            chunks, source_type = ingest(source)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    count = store_add(chunks, source=label, tags=tag_list)
    console.print(f"[green]✓[/green] Added [bold]{label}[/bold] — {count} chunks ({source_type})")


@app.command("list")
def list_documents():
    """List all documents in the knowledge base."""
    from knowledge.store import list_sources, count

    sources = list_sources()
    if not sources:
        console.print("[yellow]Knowledge base is empty. Use [bold]buddy add[/bold] to add documents.[/yellow]")
        return

    table = Table(title=f"Knowledge Base ({count()} total chunks)")
    table.add_column("Source", style="cyan")
    table.add_column("Tags")
    for s in sources:
        table.add_row(s["source"], s.get("tags", "") or "—")
    console.print(table)


@app.command("remove")
def remove_document(source: str = typer.Argument(..., help="Source name to remove")):
    """Remove a document from the knowledge base."""
    from knowledge.store import delete_source
    removed = delete_source(source)
    if removed:
        console.print(f"[green]✓[/green] Removed [bold]{source}[/bold] ({removed} chunks)")
    else:
        console.print(f"[yellow]No document found with source: {source}[/yellow]")


@app.command("chat")
def chat_mode(
    voice: bool = typer.Option(False, "--voice", "-v", help="Enable voice input/output"),
    no_knowledge: bool = typer.Option(False, "--no-kb", help="Disable knowledge base context"),
):
    """Start a conversation with your learning buddy."""
    from ai.claude_client import chat, reset_conversation
    from reachy import controller

    use_knowledge = not no_knowledge
    controller.connect()
    reset_conversation()

    console.print(Panel(
        "[bold cyan]Learning Buddy[/bold cyan] — type [bold]/quit[/bold] to exit, [bold]/reset[/bold] to start fresh",
        subtitle="voice mode ON" if voice else "text mode",
    ))

    while True:
        if voice:
            from voice.stt import listen
            controller.listening_pose()
            try:
                user_input = listen()
            except KeyboardInterrupt:
                break
            console.print(f"[dim]You:[/dim] {user_input}")
        else:
            user_input = console.input("[bold cyan]You:[/bold cyan] ").strip()

        if not user_input:
            continue
        if user_input == "/quit":
            break
        if user_input == "/reset":
            reset_conversation()
            console.print("[dim]Conversation reset.[/dim]")
            continue

        with controller.thinking_context():
            with console.status("[cyan]Thinking...[/cyan]"):
                reply = chat(user_input, use_knowledge=use_knowledge)

        console.print(f"[bold green]Buddy:[/bold green] {reply}\n")

        if voice:
            from voice.tts import speak
            speak(reply)
        else:
            # Still do a subtle nod even in text mode if connected
            controller.nod(1)


@app.command("quiz")
def quiz_mode(
    topic: str = typer.Option("", "--topic", "-t", help="Focus topic for questions"),
    count: int = typer.Option(5, "--count", "-c", help="Number of questions"),
    voice: bool = typer.Option(False, "--voice", "-v", help="Enable voice input/output"),
):
    """Quiz yourself on your knowledge base documents."""
    from ai.quiz import generate_questions, evaluate_answer
    from reachy import controller

    controller.connect()

    with console.status("[cyan]Generating questions...[/cyan]"):
        try:
            questions = generate_questions(topic=topic or None, count=count)
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    console.print(Panel(
        f"[bold cyan]Quiz time![/bold cyan] {len(questions)} questions{f' on {topic}' if topic else ''}",
        subtitle="[dim]/skip to skip, /quit to stop[/dim]",
    ))

    total_score = 0
    answered = 0

    for i, q in enumerate(questions, 1):
        console.print(f"\n[bold]Q{i}.[/bold] {q['question']}")

        if voice:
            from voice.tts import speak
            from voice.stt import listen
            speak(q["question"])
            controller.listening_pose()
            user_answer = listen()
            console.print(f"[dim]You:[/dim] {user_answer}")
        else:
            user_answer = console.input("[cyan]Your answer:[/cyan] ").strip()

        if user_answer == "/quit":
            break
        if user_answer == "/skip":
            console.print(f"[dim]Answer: {q['answer']}[/dim]")
            continue

        with console.status("[cyan]Evaluating...[/cyan]"):
            result = evaluate_answer(q["question"], q["answer"], user_answer)

        score = result.get("score", 0)
        total_score += score
        answered += 1

        if result.get("correct") or score >= 7:
            console.print(f"[green]✓ {result['feedback']}[/green] [dim](+{score}/10)[/dim]")
            controller.nod()
            if voice:
                speak(result["feedback"])
        else:
            console.print(f"[red]✗ {result['feedback']}[/red] [dim](+{score}/10)[/dim]")
            console.print(f"[dim]Correct answer: {q['answer']}[/dim]")
            controller.shake()
            if voice:
                speak(result["feedback"])

    if answered:
        avg = total_score / answered
        console.print(f"\n[bold]Score: {total_score}/{answered * 10} ({avg:.0f}/10 average)[/bold]")
        if avg >= 8:
            console.print("[green]Excellent work![/green]")
        elif avg >= 5:
            console.print("[yellow]Good effort — keep revising![/yellow]")
        else:
            console.print("[red]More practice needed. You've got this![/red]")

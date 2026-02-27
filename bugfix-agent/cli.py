from __future__ import annotations

import json
from pathlib import Path

import typer
from rich import print

from agents.orchestrator import Orchestrator

app = typer.Typer(help="Multi-agent bug fixing CLI")


@app.command()
def chat(repo: str = ".") -> None:
    repo_root = str(Path(repo).resolve())
    orchestrator = Orchestrator(repo_root)
    history: list[str] = []

    print("[bold green]BugFix Agent ready. Type 'exit' to quit.[/bold green]")
    while True:
        user = input("you> ").strip()
        if user.lower() in {"exit", "quit"}:
            break
        history.append(f"user: {user}")
        result = orchestrator.run_turn(history, user)
        history.append(f"agent: {json.dumps(result.get('execution', {}))}")
        print("[cyan]Plan:[/cyan]")
        print(json.dumps(result.get("plan", {}), indent=2))
        print("[magenta]Execution:[/magenta]")
        print(json.dumps(result.get("execution", {}), indent=2))


if __name__ == "__main__":
    app()

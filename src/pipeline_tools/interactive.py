"""Interactive shell for pipeline-tools with autocomplete."""

from __future__ import annotations

import sys
from typing import List

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import Style
from rich.console import Console

console = Console()

# All available commands and their subcommands
COMMANDS = {
    "create": ["--interactive", "-c", "--show-code", "-n", "--name", "-t", "--template", "--git", "--git-lfs"],
    "open": ["krita", "blender", "photoshop", "aftereffects", "--list", "-l", "--background", "-b"],
    "doctor": [],
    "shows": ["create", "list", "use", "info", "delete"],
    "assets": ["add", "list", "info", "status", "delete"],
    "shots": ["add", "list", "info", "status", "delete"],
    "tasks": ["list", "add", "complete", "status"],
    "versions": ["list", "info", "latest"],
    "admin": ["config-show", "config-set", "doctor"],
    "help": [],
    "exit": [],
    "quit": [],
}

COMMAND_DESCRIPTIONS = {
    "create": "Create new project",
    "open": "Launch Krita, Blender, etc.",
    "doctor": "Check system setup",
    "shows": "Manage animation shows",
    "assets": "Manage characters, props, environments",
    "shots": "Manage shot sequences",
    "tasks": "Track work tasks",
    "versions": "File version history",
    "admin": "Configure settings",
    "help": "Show help menu",
    "exit": "Exit interactive mode",
    "quit": "Exit interactive mode",
}


class PipelineCompleter(Completer):
    """Autocompleter for pipeline-tools commands."""

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        words = text.split()

        # No words yet - suggest main commands
        if not words or (len(words) == 1 and not text.endswith(" ")):
            current = words[0] if words else ""
            for cmd in COMMANDS.keys():
                if cmd.startswith(current):
                    desc = COMMAND_DESCRIPTIONS.get(cmd, "")
                    yield Completion(
                        cmd,
                        start_position=-len(current),
                        display=f"{cmd:<12} {desc}",
                    )

        # First word complete - suggest subcommands/options
        elif len(words) >= 1:
            main_cmd = words[0]
            current = words[-1] if not text.endswith(" ") else ""

            if main_cmd in COMMANDS:
                for subcmd in COMMANDS[main_cmd]:
                    if subcmd.startswith(current):
                        yield Completion(
                            subcmd,
                            start_position=-len(current),
                        )


def run_interactive():
    """Run interactive shell mode."""
    # Setup
    history = InMemoryHistory()
    completer = PipelineCompleter()
    session = PromptSession(
        history=history,
        completer=completer,
        complete_while_typing=True,
    )

    # Print welcome message
    console.print()
    console.print("╭────────────────────────────────────────────────────────╮", style="cyan")
    console.print("│  [bold cyan]Pipeline Tools[/bold cyan] [dim]Interactive Mode[/dim]              │")
    console.print("│  [dim]Type commands without 'pipeline-tools' prefix[/dim]    │")
    console.print("│  [dim]Press Tab for autocomplete • Type 'help' for menu[/dim] │")
    console.print("│  [dim]Type 'exit' or Ctrl+D to quit[/dim]                    │")
    console.print("╰────────────────────────────────────────────────────────╯", style="cyan")
    console.print()

    # Main loop
    while True:
        try:
            # Get input
            text = session.prompt("pipeline-tools> ", style=Style.from_dict({"prompt": "cyan bold"}))
            text = text.strip()

            if not text:
                continue

            # Handle special commands
            if text in ["exit", "quit"]:
                console.print("[dim]Goodbye![/dim]")
                break

            if text == "help":
                from pipeline_tools.cli import _echo_examples
                _echo_examples()
                continue

            # Execute command
            from pipeline_tools.cli import app

            # Parse the command
            args = text.split()

            try:
                # Run the typer app with the command
                app(args, standalone_mode=False)
            except SystemExit:
                # Typer raises SystemExit, we want to continue the loop
                pass
            except Exception as e:
                console.print(f"[red]Error:[/red] {e}")

        except KeyboardInterrupt:
            # Ctrl+C pressed
            console.print()
            continue

        except EOFError:
            # Ctrl+D pressed
            console.print()
            console.print("[dim]Goodbye![/dim]")
            break

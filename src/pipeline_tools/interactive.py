"""Interactive shell for Pipely with autocomplete."""


from __future__ import annotations

import re
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
    "open": ["krita", "blender", "photoshop", "aftereffects", "pureref", "--list", "-l", "--list-projects", "--project", "-p", "--choose", "-c", "--background", "-b"],
    "project": ["status", "commit", "list"],
    "doctor": [],
    "shows": ["create", "list", "use", "info", "delete"],
    "assets": ["add", "list", "info", "status", "delete"],
    "shots": ["add", "list", "info", "status", "delete"],
    "tasks": ["list", "add", "complete", "status"],
    "versions": ["list", "info", "latest"],
    "admin": ["config-show", "config-set", "doctor"],
    "projects": [],
    "status": [],
    "commit": [],
    "help": [],
    "exit": [],
    "quit": [],
}

COMMAND_DESCRIPTIONS = {
    "create": "Create new project",
    "open": "Launch Krita, Blender, etc.",
    "project": "Check git status and commit changes",
    "doctor": "Check system setup",
    "shows": "Manage animation shows",
    "assets": "Manage characters, props, environments",
    "shots": "Manage shot sequences",
    "tasks": "Track work tasks",
    "versions": "File version history",
    "admin": "Configure settings",
    "projects": "List all available projects",
    "status": "Quick git status for all projects",
    "commit": "Quick commit (prompts for project and message)",
    "help": "Show help menu",
    "exit": "Exit interactive mode",
    "quit": "Exit interactive mode",
}


class PipelineCompleter(Completer):
    """Autocompleter for pipeline-tools commands."""

    def __init__(self):
        self.available_projects = []
        self.available_dccs = []
        self.show_dcc_menu = False

    def update_context(self, projects=None, dccs=None, show_dcc_menu=False):
        """Update context for better completions."""
        if projects is not None:
            self.available_projects = projects
        if dccs is not None:
            self.available_dccs = dccs
        self.show_dcc_menu = show_dcc_menu

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        words = text.split()

        # No words yet - suggest main commands
        if not words or (len(words) == 1 and not text.endswith(" ")):
            current = words[0] if words else ""

            # If DCC menu is active, suggest DCC names and numbers
            if self.show_dcc_menu and self.available_dccs:
                for idx, dcc in enumerate(self.available_dccs, 1):
                    if str(idx).startswith(current) or dcc.startswith(current):
                        yield Completion(
                            dcc,
                            start_position=-len(current),
                            display=f"{idx}. {dcc.capitalize():<15} [Launch app]",
                        )

            # If no DCC menu, suggest project numbers and commands
            else:
                # Suggest project numbers
                if self.available_projects:
                    for idx, proj in enumerate(self.available_projects, 1):
                        if str(idx).startswith(current):
                            yield Completion(
                                str(idx),
                                start_position=-len(current),
                                display=f"{idx}. {proj.name:<25} [Select project]",
                            )

                # Suggest main commands
                for cmd in COMMANDS.keys():
                    if cmd.startswith(current):
                        desc = COMMAND_DESCRIPTIONS.get(cmd, "")
                        yield Completion(
                            cmd,
                            start_position=-len(current),
                            display=f"{cmd:<15} {desc}",
                        )

        # First word complete - suggest subcommands/options
        elif len(words) >= 1:
            main_cmd = words[0]
            current = words[-1] if not text.endswith(" ") else ""

            # Special handling for 'status' command - suggest project numbers
            if main_cmd == "status" and self.available_projects:
                for idx, proj in enumerate(self.available_projects, 1):
                    proj_num = str(idx)
                    if proj_num.startswith(current):
                        yield Completion(
                            proj_num,
                            start_position=-len(current),
                            display=f"{idx}. {proj.name:<25} [Show status]",
                        )

            # Standard subcommand completion
            elif main_cmd in COMMANDS:
                for subcmd in COMMANDS[main_cmd]:
                    if subcmd.startswith(current):
                        # Add helpful descriptions for DCCs
                        if main_cmd == "open" and subcmd in ["krita", "blender", "photoshop", "aftereffects", "pureref"]:
                            display = f"{subcmd.capitalize():<15} [Launch app]"
                        else:
                            display = subcmd

                        yield Completion(
                            subcmd,
                            start_position=-len(current),
                            display=display,
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
    console.print("│      [bold cyan]Pipely[/bold cyan] [dim]- Pipeline management made lovely[/dim]     │")
    console.print("│                                                        │")
    console.print("│  [bold]1.[/bold] Pick a project (or create new)                   │")
    console.print("│  [bold]2.[/bold] Pick an app (Blender, Krita, etc.)               │")
    console.print("│  [bold]3.[/bold] Start creating!                                  │")
    console.print("│                                                        │")
    console.print("│  [bold green]💡 Press TAB to see all options[/bold green]                │")
    console.print("│  [dim]Quick: 'status' | 'commit' | 'projects'[/dim]            │")
    console.print("╰────────────────────────────────────────────────────────╯", style="cyan")
    console.print()

    # Track available projects and DCCs for number selection
    available_projects = []
    available_dccs = []
    current_project = None
    show_dcc_menu = False

    # Auto-show projects menu on startup
    from pathlib import Path
    from pipeline_tools.core.paths import get_creative_root
    from rich.table import Table
    import subprocess

    creative_root = get_creative_root()
    creative_root.mkdir(parents=True, exist_ok=True)

    project_folders = [
        p for p in creative_root.iterdir()
        if p.is_dir() and not p.name.startswith('.')
    ]

    available_projects = project_folders

    # Update completer with initial project list
    completer.update_context(projects=available_projects, show_dcc_menu=False)

    console.print("[bold cyan]STEP 1: Pick Your Project[/bold cyan]")
    console.print()

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Number", style="cyan bold", width=8)
    table.add_column("Project", style="bold")
    table.add_column("Branch", style="dim")

    for idx, proj in enumerate(project_folders, 1):
        # Try to get git branch
        git_dir = proj / '.git'
        branch_info = ""
        if git_dir.exists():
            try:
                result = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    cwd=proj,
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                if result.returncode == 0:
                    branch_name = result.stdout.strip()
                    branch_info = f"[dim]🌿 {branch_name}[/dim]"
            except (subprocess.TimeoutExpired, Exception):
                pass

        table.add_row(f"[cyan]{idx}[/cyan]", proj.name, branch_info)

    # Add "Create New Project" option at the end
    create_option_num = len(project_folders) + 1
    table.add_row(f"[green]{create_option_num}[/green]", "[green]+ Create New Project[/green]", "")

    console.print(table)
    console.print()
    console.print("[dim]→ Type a number or press TAB to see all options[/dim]")
    console.print()

    # Main loop
    while True:
        try:
            # Get input
            raw_text = session.prompt("pipely> ", style=Style.from_dict({"prompt": "cyan bold"}))
            raw_text = raw_text.strip()

            # Split multiple commands pasted at once (newline or semicolon separated)
            commands = [t.strip() for t in re.split(r"[;\\n]+", raw_text) if t.strip()]
            if not commands:
                continue

            exit_session = False

            for text in commands:
                # Allow users to type full commands with the "pipely" prefix (e.g., "pipely tasks list")
                if text.startswith("pipely "):
                    text = text[len("pipely ") :].strip()

                if not text:
                    continue

                # Handle special commands
                if text in ["exit", "quit"]:
                    console.print("[dim]Goodbye![/dim]")
                    exit_session = True
                    break

                if text == "help":
                    from pipeline_tools.cli import _echo_examples
                    _echo_examples()
                    continue

                if text == "status" or text.startswith("status "):
                    # Quick git status for all projects or specific project
                    from pipeline_tools.cli import app
                    from pathlib import Path
                    from pipeline_tools.core.paths import get_creative_root

                    try:
                        parts = text.split()
                        if len(parts) > 1:
                            # Check if it's a number (project selection)
                            if parts[1].isdigit() and available_projects:
                                choice = int(parts[1])
                                if 1 <= choice <= len(available_projects):
                                    project_name = available_projects[choice - 1].name
                                    app(["project", "status", project_name], standalone_mode=False)
                                else:
                                    console.print(f"[red]Invalid project number. Choose 1-{len(available_projects)}[/red]")
                            else:
                                # It's a project name
                                app(["project", "status", parts[1]], standalone_mode=False)
                        else:
                            # Status for all projects
                            app(["project", "status"], standalone_mode=False)
                    except SystemExit:
                        pass
                    except Exception as e:
                        console.print(f"[red]Error:[/red] {e}")
                    console.print()
                    continue

                if text == "commit":
                    # Quick commit with prompts
                    from pipeline_tools.cli import app
                    from pathlib import Path
                    from pipeline_tools.core.paths import get_creative_root

                    creative_root = get_creative_root()
                    project_folders = [
                        p for p in creative_root.iterdir()
                        if p.is_dir() and not p.name.startswith('.') and (p / '.git').exists()
                    ]

                    if not project_folders:
                        console.print("[yellow]No git projects found.[/yellow]")
                        console.print()
                        continue

                    console.print()
                    console.print("[bold cyan]Select project to commit:[/bold cyan]")
                    for idx, proj in enumerate(project_folders, 1):
                        console.print(f"  {idx}. {proj.name}")
                    console.print()

                    try:
                        choice = int(input("Project number: ").strip())
                        if 1 <= choice <= len(project_folders):
                            project_name = project_folders[choice - 1].name
                            app(["project", "commit", project_name], standalone_mode=False)
                        else:
                            console.print("[red]Invalid selection[/red]")
                    except (ValueError, KeyboardInterrupt):
                        console.print("\n[yellow]Cancelled[/yellow]")
                    except SystemExit:
                        pass
                    except Exception as e:
                        console.print(f"[red]Error:[/red] {e}")
                    console.print()
                    continue

                if text == "projects":
                    # List all available projects
                    from pathlib import Path
                    from pipeline_tools.core.paths import get_creative_root
                    from rich.table import Table
                    import subprocess

                    creative_root = get_creative_root()
                    creative_root.mkdir(parents=True, exist_ok=True)

                    project_folders = [
                        p for p in creative_root.iterdir()
                        if p.is_dir() and not p.name.startswith('.')
                    ]

                    # Store projects for number selection
                    available_projects = project_folders
                    # Reset DCC menu state
                    show_dcc_menu = False
                    available_dccs = []

                    # Update completer to show project suggestions
                    completer.update_context(projects=available_projects, dccs=[], show_dcc_menu=False)

                    console.print()
                    console.print("[bold cyan]STEP 1: Pick Your Project[/bold cyan]")
                    console.print()

                    table = Table(show_header=False, box=None, padding=(0, 2))
                    table.add_column("Number", style="cyan bold", width=8)
                    table.add_column("Project", style="bold")
                    table.add_column("Branch", style="dim")

                    for idx, proj in enumerate(project_folders, 1):
                        # Try to get git branch
                        git_dir = proj / '.git'
                        branch_info = ""
                        if git_dir.exists():
                            try:
                                result = subprocess.run(
                                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                                    cwd=proj,
                                    capture_output=True,
                                    text=True,
                                    timeout=1
                                )
                                if result.returncode == 0:
                                    branch_name = result.stdout.strip()
                                    branch_info = f"[dim]🌿 {branch_name}[/dim]"
                            except (subprocess.TimeoutExpired, Exception):
                                pass

                        table.add_row(f"[cyan]{idx}[/cyan]", proj.name, branch_info)

                    # Add "Create New Project" option at the end
                    create_option_num = len(project_folders) + 1
                    table.add_row(f"[green]{create_option_num}[/green]", "[green]+ Create New Project[/green]", "")

                    console.print(table)
                    console.print()
                    console.print("[dim]→ Type a number or press TAB to see all options[/dim]")
                    console.print()
                    continue

                # Check if input is a number or matches a DCC name
                choice = None
                if text.isdigit():
                    choice = int(text)
                elif show_dcc_menu and available_dccs:
                    # Check if text matches a DCC name (case insensitive)
                    text_lower = text.lower()
                    for idx, dcc in enumerate(available_dccs, 1):
                        if dcc.lower() == text_lower:
                            choice = idx
                            break

                if choice is not None:
                    # If we're showing DCC menu, launch the selected DCC
                    if show_dcc_menu and available_dccs:
                        if 1 <= choice <= len(available_dccs):
                            dcc_name = available_dccs[choice - 1]

                            # Build command
                            cmd_args = ["open", dcc_name, "--background"]
                            if current_project:
                                cmd_args.extend(["--project", current_project])

                            console.print()
                            console.print("[bold cyan]STEP 3: Start Creating![/bold cyan]")
                            console.print()

                            from pipeline_tools.cli import app
                            try:
                                app(cmd_args, standalone_mode=False)
                            except SystemExit:
                                pass
                            except Exception as e:
                                console.print(f"[red]Error:[/red] {e}")

                            console.print()
                            console.print("[dim]Type 'projects' to work on another project[/dim]")
                            console.print()

                            # Reset menus
                            show_dcc_menu = False
                            available_dccs = []

                            # Update completer back to project mode
                            completer.update_context(dccs=[], show_dcc_menu=False)
                        else:
                            console.print()
                            console.print(f"[red]❌ Invalid selection. Choose 1-{len(available_dccs)}[/red]")
                            console.print()
                        continue

                    # Otherwise, it's project selection
                    elif available_projects is not None:
                        # Check if user selected "Create New Project" option
                        create_option_num = len(available_projects) + 1

                        if choice == create_option_num:
                            # User wants to create a new project
                            console.print()
                            console.print("[bold cyan]🆕 Create New Project[/bold cyan]")
                            console.print()

                            from pipeline_tools.cli import app
                            try:
                                # Run the create command in interactive mode
                                app(["create", "--interactive"], standalone_mode=False)
                            except SystemExit:
                                pass
                            except Exception as e:
                                console.print(f"[red]Error:[/red] {e}")

                            # After creating, refresh the project list
                            console.print()
                            console.print("[dim]Type 'projects' to see your new project[/dim]")
                            console.print()
                            continue

                        elif 1 <= choice <= len(available_projects):
                            selected_project = available_projects[choice - 1]
                            current_project = selected_project.name

                            console.print()
                            console.print(f"[green]✓ Project:[/green] [bold]{current_project}[/bold]")
                            console.print()

                            # Show DCC menu
                            console.print("[bold cyan]STEP 2: Pick Your App[/bold cyan]")
                            console.print()

                            from pipeline_tools.tools.dcc_launcher.launcher import DCC_PATHS, get_dcc_executable
                            from rich.table import Table

                            # Build list of installed DCCs
                            installed_dccs = []
                            for dcc in sorted(DCC_PATHS.keys()):
                                if get_dcc_executable(dcc):
                                    installed_dccs.append(dcc)

                            if not installed_dccs:
                                console.print("[yellow]⚠ No DCCs found installed[/yellow]")
                                console.print()
                                continue

                            available_dccs = installed_dccs
                            show_dcc_menu = True

                            # Update completer to show DCC suggestions
                            completer.update_context(dccs=available_dccs, show_dcc_menu=True)

                            table = Table(show_header=False, box=None, padding=(0, 2))
                            table.add_column("Number", style="cyan bold", width=8)
                            table.add_column("Application", style="bold")

                            for idx, dcc in enumerate(installed_dccs, 1):
                                table.add_row(f"[cyan]{idx}[/cyan]", dcc.capitalize())

                            console.print(table)
                            console.print()
                            console.print("[dim]→ Type a number or press TAB to see all options[/dim]")
                            console.print()
                        else:
                            console.print()
                            console.print(f"[red]❌ Invalid selection. Choose 1-{create_option_num}[/red]")
                            console.print()
                        continue

                # If we get here, it's not a recognized command
                # Allow advanced users to still type commands if they want
                # Forward known commands to the Typer CLI so artists can stay in interactive mode
                passthrough_cmds = {
                    "open", "create", "doctor", "project", "assets", "shots",
                    "tasks", "shows", "versions", "admin",
                }

                if any(text.startswith(cmd + " ") or text == cmd for cmd in passthrough_cmds):
                    from pipeline_tools.cli import app
                    args = text.split()

                    # Auto-add project to 'open' commands if a project is selected
                    if args and args[0] == "open" and current_project:
                        if "--project" not in args and "-p" not in args:
                            args.extend(["--project", current_project])

                    try:
                        app(args, standalone_mode=False)
                    except SystemExit:
                        pass
                    except Exception as e:
                        console.print(f"[red]Error:[/red] {e}")
                else:
                    console.print()
                    console.print("[yellow]Not sure what to do?[/yellow]")
                    console.print("  • Type [bold cyan]'projects'[/bold cyan] to see all your projects")
                    console.print("  • Type [bold cyan]'status'[/bold cyan] to check git status")
                    console.print("  • Type [bold cyan]'commit'[/bold cyan] to commit changes")
                    console.print("  • Type [bold cyan]a number[/bold cyan] to select from the menu")
                    console.print("  • Type [bold cyan]'help'[/bold cyan] for advanced commands")
                    console.print()

            if exit_session:
                break

        except KeyboardInterrupt:
            # Ctrl+C pressed
            console.print()
            continue

        except EOFError:
            # Ctrl+D pressed
            console.print()
            console.print("[dim]Goodbye![/dim]")
            break

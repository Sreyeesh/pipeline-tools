"""Interactive shell for Pipely with autocomplete."""


from __future__ import annotations

import re
import sys
import shlex
from typing import List

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.table import Table

from pipeline_tools.tools.project_creator.templates import TEMPLATES

console = Console()

PASSTHROUGH_CMDS = {
    "open", "create", "doctor", "project", "assets", "shots",
    "tasks", "shows", "versions", "admin", "workspace", "workfiles",
}

PREFIX_ALIASES = {"pipely", "pipley", "piply"}


def _split_user_commands(raw_text: str, passthrough_cmds: set[str]) -> list[str]:
    """
    Split pasted input into individual commands.

    Rules:
    - Normalize separators (semicolons -> newlines).
    - Insert a newline before any subsequent top-level command token (helps when paste loses newlines) but
      avoid splitting on tokens that are only subcommands (like 'create' after 'shows').
    - Split on newlines (handles Windows CRLF).
    - Within each chunk, if another known command token appears, start a new command.
    """
    # Normalize common separators
    normalized = raw_text.replace(";", "\n")

    # Only split before top-level commands (not subcommands like "create" of "shows")
    subcommand_tokens = set()
    for subs in COMMANDS.values():
        subcommand_tokens.update(subs)
    top_level_tokens = [cmd for cmd in passthrough_cmds if cmd not in subcommand_tokens]

    # Force a newline before any subsequent passthrough command (when pastes collapse newlines)
    cmd_pattern = r"(?<!^)\s+(?=(" + "|".join(re.escape(cmd) for cmd in top_level_tokens) + r")\b)"
    normalized = re.sub(cmd_pattern, "\n", normalized)

    commands: list[str] = []
    for chunk in re.split(r"[\r\n]+", normalized):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            tokens = shlex.split(chunk)
        except ValueError:
            tokens = chunk.split()
        if not tokens:
            continue

        current: list[str] = []
        for tok in tokens:
            current_main = current[0] if current else None
            # Avoid splitting when 'tok' is actually a subcommand/flag of the current main command
            is_sub_of_current = current_main in COMMANDS and tok in COMMANDS[current_main]
            if current and tok in passthrough_cmds and not is_sub_of_current:
                commands.append(" ".join(current))
                current = [tok]
            else:
                current.append(tok)
        if current:
            commands.append(" ".join(current))
    return commands


def _normalize_shorthand_command(parts: list[str]) -> list[str]:
    """
    Allow artist-friendly shorthand like:
    'shows create DMO \"Demo\" animation_short' -> adds required flags.
    """
    if len(parts) >= 3 and parts[0] == "shows" and parts[1] == "create":
        has_flags = any(p.startswith("-") for p in parts[2:])
        if has_flags:
            return parts

        show_code = parts[2]
        name_tokens = parts[3:]
        template = None
        if name_tokens and name_tokens[-1] in TEMPLATES:
            template = name_tokens.pop()
        if not name_tokens:
            return parts
        name = " ".join(name_tokens)

        normalized = ["shows", "create", "-c", show_code, "-n", name]
        if template:
            normalized.extend(["-t", template])
        return normalized

    return parts


def _workspace_summary(show_code: str | None = None) -> None:
    """
    Print a compact workspace summary for the current show.
    """
    from pipeline_tools.core import db

    data = db.load_db()
    code = show_code or data.get("current_show")
    if not code:
        console.print("[yellow]No current show. Use 'shows use -c CODE' first.[/yellow]")
        return
    show = data.get("shows", {}).get(code)
    if not show:
        console.print(f"[yellow]Show '{code}' not found in DB.[/yellow]")
        return

    shots = [s for s in data.get("shots", {}).values() if s.get("show_code") == code]
    assets = [a for a in data.get("assets", {}).values() if a.get("show_code") == code]
    versions = [v for v in data.get("versions", {}).values() if v.get("show_code") == code]

    tasks = []
    for target_id, items in data.get("tasks", {}).items():
        if target_id.startswith(code + "_"):
            for t in items:
                tasks.append((target_id, t))

    console.print()
    console.print(f"[bold cyan]Workspace:[/bold cyan] {code} - {show.get('name','')}")
    console.print(f"[dim]{show.get('root','')}[/dim]")

    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))
    table.add_column("Shots", style="cyan", no_wrap=True)
    table.add_column("Assets", style="magenta", no_wrap=True)
    table.add_column("Tasks", style="green")

    # Prepare rows (up to 3 entries each)
    shot_lines = [f"{s['id']} [{s['status']}]" for s in sorted(shots, key=lambda s: s["id"])[:3]]
    asset_lines = [f"{a['id']} [{a['type']}]" for a in sorted(assets, key=lambda a: a["id"])[:3]]
    task_lines = [f"{tid}:{t['name']} [{t['status']}]" for tid, t in tasks[:3]]

    def _lines(lines: list[str], more: int) -> str:
        extra = f"\n+{more} more" if more > 0 else ""
        return "\n".join(lines) + extra if lines else "—"

    table.add_row(
        _lines(shot_lines, max(0, len(shots) - len(shot_lines))),
        _lines(asset_lines, max(0, len(assets) - len(asset_lines))),
        _lines(task_lines, max(0, len(tasks) - len(task_lines))),
    )
    console.print(table)
    console.print()

# All available commands and their subcommands
COMMANDS = {
    "create": ["--interactive", "-c", "--show-code", "-n", "--name", "-t", "--template", "--git", "--git-lfs"],
    "open": ["krita", "blender", "photoshop", "aftereffects", "pureref", "--list", "-l", "--list-projects", "--project", "-p", "--choose", "-c", "--background", "-b"],
    "project": ["status", "commit", "list"],
    "doctor": [],
    "shows": ["create", "list", "use", "info", "delete"],
    "assets": ["add", "list", "info", "status", "delete"],
    "shots": ["add", "list", "info", "status", "delete"],
    "tasks": ["list", "add", "complete", "status", "delete"],
    "versions": ["list", "info", "latest", "delete"],
    "admin": ["config_show", "config_set", "doctor", "files", "add", "template", "create"],
    "workfiles": ["add", "list", "open"],
    "workspace": ["on", "off", "show"],
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
    "workfiles": "Create/open workfiles",
    "admin": "Configure settings and admin files",
    "workspace": "Show or toggle project summary",
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
    workspace_summary_enabled = False

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
            commands = _split_user_commands(raw_text, PASSTHROUGH_CMDS)
            if not commands:
                continue

            exit_session = False

            for text in commands:
                # Allow users to type full commands with the "pipely"/common typos prefix (e.g., "pipely tasks list")
                try:
                    parts = shlex.split(text)
                except ValueError:
                    parts = text.split()
                if parts and parts[0].lower() in PREFIX_ALIASES:
                    text = " ".join(parts[1:]).strip()

                    try:
                        parts = shlex.split(text)
                    except ValueError:
                        parts = text.split()

                if not text:
                    continue

                parts = _normalize_shorthand_command(parts)
                text = " ".join(parts)

                # Workspace summary toggles
                if text == "workspace" or text == "workspace show":
                    _workspace_summary()
                    continue
                if text == "workspace on":
                    workspace_summary_enabled = True
                    console.print("[green]Workspace summary enabled.[/green]")
                    _workspace_summary()
                    continue
                if text == "workspace off":
                    workspace_summary_enabled = False
                    console.print("[yellow]Workspace summary disabled.[/yellow]")
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
                if parts and parts[0] in PASSTHROUGH_CMDS:
                    from pipeline_tools.cli import app
                    args = parts

                    # Auto-add project to 'open' commands if a project is selected
                    if parts and parts[0] == "open" and current_project:
                        if "--project" not in parts and "-p" not in parts:
                            parts.extend(["--project", current_project])

                    try:
                        app(parts, standalone_mode=False)
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

                if workspace_summary_enabled:
                    _workspace_summary()

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

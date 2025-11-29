from __future__ import annotations

from typing import List

import typer
from rich.console import Console
from rich.columns import Columns
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from pipeline_tools import __version__
from pipeline_tools.core import observability
from pipeline_tools.tools.admin import main as admin_main
from pipeline_tools.tools.assets import main as assets_main
from pipeline_tools.tools.character_thumbnails import main as character_thumbnails_main
from pipeline_tools.tools.dcc_launcher.launcher import launch_dcc, get_dcc_executable, DCC_PATHS
from pipeline_tools.tools.project_creator import main as project_creator_main
from pipeline_tools.tools.shots import main as shots_main
from pipeline_tools.tools.shows import main as shows_main
from pipeline_tools.tools.tasks import main as tasks_main
from pipeline_tools.tools.versions import main as versions_main


app = typer.Typer(add_completion=False, help="Artist-friendly pipeline tools launcher.")

console = Console()

MENU_SECTIONS = [
    ("🚀 Getting Started", [
        ("create", "Create new project", "Set up folders and structure for animation/VFX"),
        ("doctor", "System check", "Verify your environment is configured correctly"),
        ("open", "Launch apps", "Open Krita, Blender, and other creative tools"),
    ]),
    ("📂 Project Management", [
        ("shows", "Shows", "Create and manage animation productions"),
        ("assets", "Assets", "Characters, props, and environments"),
        ("shots", "Shots", "Shot sequences and scene management"),
    ]),
    ("💼 Production", [
        ("tasks", "Tasks", "Track and assign work items"),
        ("versions", "Versions", "File version history and tracking"),
        ("admin", "Settings", "Configure pipeline preferences"),
    ]),
]

QUICK_START = [
    ("🎬 New Project", 'create --interactive', "Guided project setup"),
    ("🎨 Launch Krita", 'open krita', "Start painting/drawing"),
    ("🔧 System Check", 'doctor', "Verify installation"),
]


def _render_header() -> None:
    """Render GUI-style header."""
    console.print()
    title = Text()
    title.append("Pipeline Tools", style="bold cyan")
    title.append(f" v{__version__}", style="dim")

    subtitle = Text()
    subtitle.append("Artist-friendly animation & VFX pipeline", style="dim")

    panel = Panel(
        subtitle,
        title=title,
        border_style="cyan",
        padding=(0, 2),
    )
    console.print(panel)
    console.print()


def _render_quick_start() -> None:
    """Render quick start section."""
    console.print("[bold white]⚡ Quick Start[/bold white]")
    console.print()

    for label, cmd, description in QUICK_START:
        console.print(f"  {label}")
        console.print(f"    [cyan]$ pipeline-tools {cmd}[/cyan]  [dim]{description}[/dim]")
        console.print()

    console.print()


def _render_menu() -> None:
    """Render menu sections."""
    for section_name, commands in MENU_SECTIONS:
        console.print(f"[bold white]{section_name}[/bold white]")
        console.print()

        for cmd_name, label, description in commands:
            console.print(f"  [cyan]pipeline-tools {cmd_name}[/cyan]")
            console.print(f"    {label} — [dim]{description}[/dim]")
            console.print()

        console.print()


def _render_examples() -> None:
    """Render example usage section."""
    console.print("[bold white]📖 Examples[/bold white]")
    console.print()

    examples = [
        ("Create a new show", 'shows create -c PKU -n "My Show"'),
        ("Add a character", 'assets add -c PKU -t CH -n Hero'),
        ("Add a shot", 'shots add PKU_SH010 "Opening scene"'),
        ("Launch Krita", 'open krita'),
        ("Launch Blender in background", 'open blender -b'),
        ("List your tasks", 'tasks list'),
    ]

    for task, cmd in examples:
        console.print(f"  {task}")
        console.print(f"    [cyan]$ pipeline-tools {cmd}[/cyan]")
        console.print()

    console.print()


def _render_footer() -> None:
    """Render footer with help tip."""
    console.print("[dim]─[/dim]" * 60)
    console.print()
    console.print("[dim]Need more details? Add [cyan]--help[/cyan] to any command[/dim]")
    console.print()


def _echo_examples() -> None:
    _render_header()
    _render_quick_start()
    _render_menu()
    _render_examples()
    _render_footer()


def _echo_command_list() -> None:
    _render_header()
    _render_menu()


def _passthrough(ctx: typer.Context, runner, command_name: str) -> None:
    """Pass remaining args through to an existing argparse-based module with logging."""
    args = list(ctx.args)
    observability.log_event("command_start", command=command_name, cli_args=args)
    try:
        runner(args)
    except Exception as exc:  # pragma: no cover - thin glue layer
        observability.log_exception("command_error", exc, command=command_name)
        raise
    observability.log_event("command_complete", command=command_name, cli_args=args)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    examples: bool = typer.Option(False, "--examples", help="Show common commands and exit."),
    list_commands: bool = typer.Option(False, "--list", "--commands", help="List available commands."),
    version: bool = typer.Option(False, "--version", help="Show version and exit."),
    log_level: str = typer.Option("INFO", "--log-level", help="Log level (DEBUG, INFO, WARNING, ERROR)."),
    log_format: str = typer.Option(
        "console", "--log-format", help="Log format: console or json for structured logs."
    ),
    request_id: str = typer.Option(None, "--request-id", help="Override request ID for tracing/logs."),
    metrics_endpoint: str = typer.Option(
        None,
        "--metrics-endpoint",
        help="Optional StatsD endpoint (e.g. statsd://localhost:8125) for metrics.",
    ),
) -> None:
    if version:
        console.print(f"pipeline-tools {__version__}")
        raise typer.Exit()
    observability.init_observability(
        log_level=log_level,
        log_format=log_format,
        request_id=request_id,
        metrics_endpoint=metrics_endpoint,
        service="pipeline-tools",
    )
    observability.log_event("cli_entry", invoked_subcommand=ctx.invoked_subcommand)
    if examples:
        _echo_examples()
        raise typer.Exit()
    if list_commands:
        _echo_command_list()
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        # Launch interactive mode
        from pipeline_tools.interactive import run_interactive
        run_interactive()


@app.command()
def examples() -> None:
    """Show common commands and available modules."""
    _echo_examples()


@app.command()
def create(
    show_code: str = typer.Option(None, "-c", "--show-code", help="Show code, e.g. DMO."),
    name: str = typer.Option(None, "-n", "--name", help='Project name, e.g. "Demo Short 30s".'),
    template: str = typer.Option(None, "-t", "--template", help="Template key (see templates list)."),
    interactive: bool = typer.Option(False, "-i", "--interactive", help="Prompt for missing values."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without creating."),
    yes: bool = typer.Option(False, "-y", "--yes", help="Skip confirmation prompts."),
    git: bool = typer.Option(False, "-g", "--git", help="Initialize a git repository."),
    git_lfs: bool = typer.Option(False, "--git-lfs", help="Initialize Git LFS (implies --git)."),
    git_branch: str = typer.Option("main", "--git-branch", help="Initial git branch name."),
) -> None:
    """Create a project folder tree from a template."""
    argv: List[str] = []
    if show_code:
        argv.extend(["-c", show_code])
    if name:
        argv.extend(["-n", name])
    if template:
        argv.extend(["-t", template])
    if interactive:
        argv.append("--interactive")
    if dry_run:
        argv.append("--dry-run")
    if yes:
        argv.append("--yes")
    if git:
        argv.append("--git")
    if git_lfs:
        argv.append("--git-lfs")
    if git_branch != "main":
        argv.extend(["--git-branch", git_branch])
    project_creator_main.main(argv)


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def doctor(ctx: typer.Context) -> None:
    """Run environment checks."""
    observability.log_event("command_start", command="doctor", cli_args=list(ctx.args))
    admin_main.main(["doctor", *list(ctx.args)])
    observability.log_event("command_complete", command="doctor", cli_args=list(ctx.args))


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def admin(ctx: typer.Context) -> None:
    """Admin/config commands (config_show, config_set, doctor)."""
    _passthrough(ctx, admin_main.main, "admin")


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def shows(ctx: typer.Context) -> None:
    """Show-level commands (create/list/use/info/etc.)."""
    _passthrough(ctx, shows_main.main, "shows")


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def assets(ctx: typer.Context) -> None:
    """Asset-level commands (add/list/info/status/etc.)."""
    _passthrough(ctx, assets_main.main, "assets")


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def shots(ctx: typer.Context) -> None:
    """Shot-level commands (add/list/info/status/etc.)."""
    _passthrough(ctx, shots_main.main, "shots")


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def tasks(ctx: typer.Context) -> None:
    """Task commands for assets/shots."""
    _passthrough(ctx, tasks_main.main, "tasks")


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def versions(ctx: typer.Context) -> None:
    """Version tracking commands."""
    _passthrough(ctx, versions_main.main, "versions")


@app.command(
    "character-thumbnails",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def character_thumbnails(ctx: typer.Context) -> None:
    """Generate thumbnail sheets for characters."""
    _passthrough(ctx, character_thumbnails_main.main, "character-thumbnails")


@app.command()
def open(
    dcc_name: str = typer.Argument(..., help="DCC name (krita, blender, photoshop, etc.)"),
    background: bool = typer.Option(False, "-b", "--background", help="Launch in background"),
    list_dccs: bool = typer.Option(False, "-l", "--list", help="List supported DCCs"),
) -> None:
    """
    Open a DCC application.

    Examples:

        pipeline-tools open krita

        pipeline-tools open blender --background

        pipeline-tools open krita -b
    """
    from pathlib import Path

    if list_dccs:
        console.print()
        console.print("[bold cyan]📋 Supported DCCs[/bold cyan]")
        console.print()

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Status", style="cyan", width=3)
        table.add_column("DCC", style="bold", width=15)
        table.add_column("Path", style="dim")

        for dcc in sorted(DCC_PATHS.keys()):
            exe = get_dcc_executable(dcc)
            if exe:
                table.add_row("✓", dcc.capitalize(), f"[green]{exe}[/green]")
            else:
                table.add_row("✗", dcc.capitalize(), "[dim]Not installed[/dim]")

        console.print(table)
        console.print()
        return

    # Check if DCC exists
    executable = get_dcc_executable(dcc_name)
    if not executable:
        console.print()
        console.print(f"[red bold]❌ {dcc_name.capitalize()} not found[/red bold]")
        console.print()
        console.print("[yellow]Tip:[/yellow] Run [cyan]pipeline-tools open --list[/cyan] to see available DCCs")
        console.print()
        raise typer.Exit(1)

    # Launch
    try:
        console.print()
        console.print(f"[bold cyan]🚀 Launching {dcc_name.capitalize()}[/bold cyan]")

        # Show details in a nice table
        details = Table(show_header=False, box=None, padding=(0, 1), show_edge=False)
        details.add_column("Label", style="dim", width=12)
        details.add_column("Value", style="")

        details.add_row("Executable:", f"[dim]{executable}[/dim]")

        console.print(details)
        console.print()

        process = launch_dcc(
            dcc_name=dcc_name,
            file_path=None,
            project_root=None,
            background=background
        )

        if background:
            console.print(f"[green bold]✅ {dcc_name.capitalize()} launched[/green bold] [dim](PID: {process.pid})[/dim]")
        else:
            console.print(f"[green bold]✅ {dcc_name.capitalize()} is running[/green bold]")
            console.print("[dim]Waiting for application to close...[/dim]")
            process.wait()
            console.print(f"[yellow]👋 {dcc_name.capitalize()} closed[/yellow]")

        console.print()

    except FileNotFoundError as e:
        console.print()
        console.print(f"[red bold]❌ File not found[/red bold]")
        console.print(f"   [dim]{e}[/dim]")
        console.print()
        raise typer.Exit(1)
    except ValueError as e:
        console.print()
        console.print(f"[red bold]❌ Invalid file path[/red bold]")
        console.print(f"   [dim]{e}[/dim]")
        console.print()
        raise typer.Exit(1)
    except Exception as e:
        console.print()
        console.print(f"[red bold]❌ Error launching {dcc_name}[/red bold]")
        console.print(f"   [dim]{e}[/dim]")
        console.print()
        raise typer.Exit(1)


if __name__ == "__main__":
    app()


def run() -> None:
    """Console script entry point."""
    app()

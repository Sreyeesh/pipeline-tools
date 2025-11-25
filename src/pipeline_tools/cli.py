from __future__ import annotations

from typing import List

import typer
from rich.console import Console
from rich.table import Table

from pipeline_tools.core import observability
from pipeline_tools.tools.admin import main as admin_main
from pipeline_tools.tools.assets import main as assets_main
from pipeline_tools.tools.character_thumbnails import main as character_thumbnails_main
from pipeline_tools.tools.project_creator import main as project_creator_main
from pipeline_tools.tools.shots import main as shots_main
from pipeline_tools.tools.shows import main as shows_main
from pipeline_tools.tools.tasks import main as tasks_main
from pipeline_tools.tools.versions import main as versions_main


app = typer.Typer(add_completion=False, help="Artist-friendly pipeline tools launcher.")

console = Console()

COMMANDS = [
    ("create", "Create project folder trees from templates."),
    ("doctor", "Run environment checks."),
    ("admin", "Admin/config commands (config_show, config_set, doctor)."),
    ("shows", "Show-level commands (create/list/use/info/etc.)."),
    ("assets", "Asset-level commands (add/list/info/status/etc.)."),
    ("shots", "Shot-level commands (add/list/info/status/etc.)."),
    ("tasks", "Task commands for assets/shots."),
    ("versions", "Version tracking commands."),
    ("character-thumbnails", "Generate thumbnail sheets for characters."),
    ("examples", "Show common commands."),
]

EXAMPLE_COMMANDS = [
    'pipeline-tools create -c PKS -n "Poku Short 30s"',
    "pipeline-tools create --interactive",
    "pipeline-tools shows list",
    "pipeline-tools assets add -c PKS -t CH -n Poku",
    'pipeline-tools shots add PKS_SH010 "First pass layout"',
    "pipeline-tools doctor",
]


def _render_header() -> None:
    console.print("[bold cyan]Pipeline Tools[/bold cyan] [dim]· artist-friendly pipeline CLI[/dim]")
    console.print("Run a command below or add [bold]--help[/bold] to any command for details.\n")


def _render_examples() -> None:
    console.print("[bold]Common commands[/bold]")
    for example in EXAMPLE_COMMANDS:
        console.print(f"  [cyan]{example}[/cyan]")
    console.print()


def _render_command_table() -> None:
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Command", style="bold green")
    table.add_column("What it does")
    for name, help_text in COMMANDS:
        table.add_row(name, help_text)
    console.print(table)


def _echo_examples() -> None:
    _render_header()
    _render_examples()
    console.print("[bold]Commands[/bold]")
    _render_command_table()


def _echo_command_list() -> None:
    _render_command_table()


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
        _echo_examples()
        raise typer.Exit()


@app.command()
def examples() -> None:
    """Show common commands and available modules."""
    _echo_examples()


@app.command()
def create(
    show_code: str = typer.Option(None, "-c", "--show-code", help="Show code, e.g. PKS."),
    name: str = typer.Option(None, "-n", "--name", help='Project name, e.g. "Poku Short 30s".'),
    template: str = typer.Option(None, "-t", "--template", help="Template key (see templates list)."),
    interactive: bool = typer.Option(False, "-i", "--interactive", help="Prompt for missing values."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without creating."),
    yes: bool = typer.Option(False, "-y", "--yes", help="Skip confirmation prompts."),
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


if __name__ == "__main__":
    app()


def run() -> None:
    """Console script entry point."""
    app()

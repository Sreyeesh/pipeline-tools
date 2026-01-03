from __future__ import annotations

from pathlib import Path

import typer

from pipeline_tools import __version__
from pipeline_tools.os_utils import resolve_root, sanitize_folder_name

app = typer.Typer(add_completion=False, help="Pipely - create predictable project folders for artists.")

PROJECT_TEMPLATES: dict[str, list[str]] = {
    "animation": [
        "01_ADMIN",
        "02_PREPRO",
        "03_ASSETS",
        "04_SHOTS",
        "05_WORK",
        "06_DELIVERY",
        "z_TEMP",
    ],
    "game": [
        "01_DESIGN",
        "02_ART",
        "03_TECH",
        "04_AUDIO",
        "05_QA",
        "06_RELEASE",
        "z_TEMP",
    ],
    "art": [
        "01_REFERENCE",
        "02_WIP",
        "03_EXPORTS",
        "04_DELIVERY",
        "z_TEMP",
    ],
}


def _prompt_project_type(project_type: str | None) -> str:
    if project_type:
        candidate = project_type.strip().lower()
        if candidate in PROJECT_TEMPLATES:
            return candidate
        raise typer.BadParameter(f"Unsupported project type: {project_type}")
    choices = "/".join(PROJECT_TEMPLATES.keys())
    selected = typer.prompt(f"Project type? ({choices})", default="animation").strip().lower()
    while selected not in PROJECT_TEMPLATES:
        typer.echo(f"Please choose one of: {choices}")
        selected = typer.prompt(f"Project type? ({choices})").strip().lower()
    return selected


def _project_dir(root: Path, name: str) -> Path:
    slug = sanitize_folder_name(name, fallback="project")
    return root / slug


@app.command("init")
def cmd_init(
    name: str | None = typer.Option(None, "--name", "-n", help="Project name."),
    project_type: str | None = typer.Option(None, "--type", "-t", help="Project type (animation/game/art)."),
    root: Path | None = typer.Option(None, "--root", help="Base folder (defaults to current directory)."),
) -> None:
    """Create a clean folder structure for a new project."""
    project_name = name or typer.prompt("Project name")
    chosen_type = _prompt_project_type(project_type)
    base_root = resolve_root(root)
    project_dir = _project_dir(base_root, project_name)

    project_dir.mkdir(parents=True, exist_ok=True)
    for rel in PROJECT_TEMPLATES[chosen_type]:
        (project_dir / rel).mkdir(parents=True, exist_ok=True)

    typer.echo(f"→ Created {chosen_type} project at {project_dir}")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", help="Show version and exit."),
) -> None:
    if version:
        typer.echo(f"pipely {__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        typer.echo("Run `pipely init` to scaffold a project.")
        raise typer.Exit()


def run() -> None:
    app()

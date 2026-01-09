from __future__ import annotations

from pathlib import Path
import re

import typer

from pipeline_tools import __version__
from pipeline_tools.asset_cli import app as asset_app
from pipeline_tools.approval_cli import app as approval_app
from pipeline_tools.db_cli import app as db_app
from pipeline_tools.project_cli import app as project_app
from pipeline_tools.schedule_cli import app as schedule_app
from pipeline_tools.os_utils import resolve_root, sanitize_folder_name

app = typer.Typer(add_completion=False, help="Pipely - create predictable project folders for artists.")
app.add_typer(db_app, name="db")
app.add_typer(asset_app, name="asset")
app.add_typer(approval_app, name="approve")
app.add_typer(schedule_app, name="schedule")
app.add_typer(project_app, name="project")

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

TYPE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "animation": ("animation", "anim", "film", "short", "sequence", "shot", "vfx"),
    "game": ("game", "level", "prototype", "unity", "unreal", "rpg", "fps"),
    "art": ("art", "illustration", "painting", "concept", "portfolio", "design"),
}


def _infer_project_type(text: str) -> str | None:
    lowered = text.lower()
    scores: dict[str, int] = {key: 0 for key in PROJECT_TEMPLATES}
    for project_type, keywords in TYPE_KEYWORDS.items():
        for keyword in keywords:
            if re.search(rf"\b{re.escape(keyword)}\b", lowered):
                scores[project_type] += 1
    best_type = max(scores, key=scores.get)
    if scores[best_type] == 0:
        return None
    tied = [project_type for project_type, score in scores.items() if score == scores[best_type]]
    if len(tied) > 1:
        return None
    return best_type


def _infer_project_name(text: str) -> str | None:
    quoted = re.search(r'"([^"]+)"|\'([^\']+)\'', text)
    if quoted:
        name = quoted.group(1) or quoted.group(2)
    else:
        match = re.search(
            r"\b(?:called|named|titled|for|project)\s+([A-Za-z0-9][A-Za-z0-9 _.-]{1,60})",
            text,
            flags=re.IGNORECASE,
        )
        if not match:
            return None
        name = match.group(1)
    name = re.sub(r"^(called|named|titled)\s+", "", name.strip(), flags=re.IGNORECASE)
    name = re.split(r"[.,;:!?]", name)[0].strip()
    name = re.sub(r"\b(project|folder|folders|template)\b$", "", name, flags=re.IGNORECASE).strip()
    if not name:
        return None
    if name.lower() in PROJECT_TEMPLATES and len(name.split()) == 1:
        return None
    return name


def _apply_description(description: str, name: str | None, project_type: str | None) -> tuple[str | None, str | None]:
    inferred_name = _infer_project_name(description)
    inferred_type = _infer_project_type(description)
    if name is None:
        name = inferred_name
    if project_type is None:
        project_type = inferred_type
    return name, project_type


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
    describe: str | None = typer.Option(None, "--describe", "-d", help="Describe the project in plain language."),
    root: Path | None = typer.Option(None, "--root", help="Base folder (defaults to current directory)."),
) -> None:
    """Create a clean folder structure for a new project."""
    if describe:
        name, project_type = _apply_description(describe, name, project_type)

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

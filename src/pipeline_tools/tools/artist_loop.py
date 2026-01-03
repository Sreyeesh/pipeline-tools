from __future__ import annotations

import hashlib
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Sequence

import typer

from pipeline_tools.os_utils import resolve_root, sanitize_folder_name

app = typer.Typer(help="Artist loop workflow: Create → Work → Version → Deliver.")
DEFAULT_TASK_NAME = "main"


@dataclass
class TaskInfo:
    project: Path
    target: Path
    task: Path

    @property
    def display(self) -> str:
        rel = f"{self.project.name}/{self.target.name}/{self.task.name}"
        return rel


def _slugify(value: str, fallback: str = "project") -> str:
    return sanitize_folder_name(value, fallback=fallback)


def _ensure_root(root: Path | None) -> Path:
    base = resolve_root(root)
    base.mkdir(parents=True, exist_ok=True)
    return base


def _log_action(base_root: Path, message: str) -> None:
    log_path = base_root / "_pipely_log.txt"
    timestamp = datetime.utcnow().isoformat()
    _write_text(log_path, f"[{timestamp}] {message}\n", append=True)


# Python's Path.write_text lacks append flag pre-3.11. Provide helper.
def _write_text(path: Path, text: str, append: bool = False) -> None:
    mode = "a" if append else "w"
    with path.open(mode, encoding="utf-8") as handle:
        handle.write(text)


def _unique_file(base: Path) -> Path:
    candidate = base
    counter = 1
    while candidate.exists():
        stem = candidate.stem
        suffix = candidate.suffix
        candidate = candidate.with_name(f"{stem}_{counter:03d}{suffix}")
        counter += 1
    return candidate


def _discover_tasks(base_root: Path) -> list[TaskInfo]:
    tasks: list[TaskInfo] = []
    for project in base_root.iterdir():
        if not project.is_dir() or project.name.startswith("."):
            continue
        for target in project.iterdir():
            if not target.is_dir() or target.name.startswith("."):
                continue
            for task in target.iterdir():
                if not task.is_dir():
                    continue
                work = task / "work"
                versions = task / "versions"
                deliveries = task / "deliveries"
                if work.exists() and versions.exists() and deliveries.exists():
                    tasks.append(TaskInfo(project, target, task))
    return sorted(tasks, key=lambda t: t.display.lower())


def _prompt_choice(label: str, options: Sequence[str]) -> str:
    for idx, option in enumerate(options, start=1):
        typer.echo(f"  [{idx}] {option}")
    selection = typer.prompt(label)
    try:
        index = int(selection) - 1
        return options[index]
    except (ValueError, IndexError):
        raise typer.BadParameter("Invalid selection.")


def _resolve_task(base_root: Path, task_path: str | None) -> Path:
    if task_path:
        candidate = Path(task_path)
        if not candidate.is_absolute():
            candidate = base_root / candidate
        if not candidate.exists():
            raise typer.BadParameter(f"Task folder not found: {candidate}")
        return candidate
    tasks = _discover_tasks(base_root)
    if not tasks:
        raise typer.BadParameter("No tasks found. Run 'pipely loop create' first.")
    choice = _prompt_choice("Pick a task", [t.display for t in tasks])
    for info in tasks:
        if info.display == choice:
            return info.task
    raise typer.BadParameter("Task selection failed.")


def _ensure_task_structure(task_root: Path) -> None:
    for folder in ("work", "versions", "deliveries", "previews"):
        (task_root / folder).mkdir(parents=True, exist_ok=True)
    notes = task_root / "notes.md"
    if not notes.exists():
        notes.write_text("# Notes\n", encoding="utf-8")


def _version_files(versions_dir: Path) -> list[Path]:
    files = [
        p
        for p in versions_dir.glob("*")
        if p.is_file() and not p.name.startswith("notes_v")
    ]
    files.sort(key=lambda p: p.stat().st_mtime)
    return files


def _latest_version(versions_dir: Path) -> Path | None:
    files = _version_files(versions_dir)
    return files[-1] if files else None


def _next_version_path(task_root: Path, extension: str) -> tuple[Path, int]:
    versions_dir = task_root / "versions"
    base = f"{_slugify(task_root.parent.name, fallback='target')}_{_slugify(task_root.name, fallback=DEFAULT_TASK_NAME)}"
    max_index = 0
    for file in versions_dir.glob(f"{base}_v*"):
        match = re.match(rf"{re.escape(base)}_v(\d+)", file.stem)
        if match:
            max_index = max(max_index, int(match.group(1)))
    next_index = max_index + 1
    filename = f"{base}_v{next_index:03d}{extension}"
    return versions_dir / filename, next_index


def _copy_file(source: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    final_path = _unique_file(destination)
    shutil.copy2(source, final_path)
    return final_path


def _create_delivery_folder(task_root: Path) -> tuple[Path, int]:
    deliveries = task_root / "deliveries"
    deliveries.mkdir(parents=True, exist_ok=True)
    existing = sorted(p for p in deliveries.iterdir() if p.is_dir())
    next_index = len(existing) + 1
    folder = deliveries / f"delivery_{next_index:03d}"
    folder.mkdir(parents=True, exist_ok=False)
    return folder, next_index


def _checksum(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


@app.command("create")
def cmd_create(
    project: str = typer.Option(None, "--project", help="Project name/folder."),
    target: str = typer.Option(None, "--target", help="Asset or shot name."),
    task: str = typer.Option(None, "--task", help="Optional task folder name (defaults to 'main')."),
    root: Path | None = typer.Option(None, "--root", help="Project root (default: current directory)."),
) -> None:
    base_root = _ensure_root(root)
    project_name = project or typer.prompt("Project name")
    target_name = target or typer.prompt("Asset or Shot?")
    task_name = task or DEFAULT_TASK_NAME

    project_dir = base_root / _slugify(project_name, fallback="project")
    target_dir = project_dir / _slugify(target_name, fallback="target")
    task_dir = target_dir / _slugify(task_name, fallback="task")

    task_dir.mkdir(parents=True, exist_ok=True)
    _ensure_task_structure(task_dir)

    message = f"Create → {project_dir.relative_to(base_root)} / {target_dir.name} / {task_dir.name}"
    _log_action(base_root, message)
    typer.echo(f"→ Created workspace at {task_dir}")


@app.command("work")
def cmd_work(
    task_path: str = typer.Option(None, "--task", help="Path to task folder (project/target/task)."),
    root: Path | None = typer.Option(None, "--root", help="Project root (default: current directory)."),
) -> None:
    base_root = _ensure_root(root)
    task_root = _resolve_task(base_root, task_path)
    _ensure_task_structure(task_root)

    versions_dir = task_root / "versions"
    latest = _latest_version(versions_dir)
    work_dir = task_root / "work"
    work_dir.mkdir(parents=True, exist_ok=True)
    if latest:
        prompt = f"Copy latest version ({latest.name}) into work/current{latest.suffix}? [Y/n]"
        choice = typer.prompt(prompt, default="Y")
        if choice.lower() in {"y", "yes", ""}:
            dest = work_dir / f"current{latest.suffix}"
            final = _copy_file(latest, dest)
            typer.echo(f"→ Copied to {final}")
    else:
        typer.echo("No previous versions found—start creating your first save.")

    launch_file = work_dir / "launch.txt"
    if not launch_file.exists():
        launch_file.write_text("Edit this file with your preferred launch command.\n", encoding="utf-8")
    _log_action(base_root, f"Work → Ready at {task_root.relative_to(base_root)}")
    typer.echo("You're ready to create. Update work/launch.txt if you use a custom app command.")


@app.command("version")
def cmd_version(
    task_path: str = typer.Option(None, "--task", help="Path to task folder (project/target/task)."),
    description: str = typer.Option(None, "--description", "-d", help="Short note for this save."),
    source_file: Path | None = typer.Option(None, "--source", "-s", help="File to version (defaults to work/current.*)."),
    root: Path | None = typer.Option(None, "--root", help="Project root (default: current directory)."),
) -> None:
    base_root = _ensure_root(root)
    task_root = _resolve_task(base_root, task_path)
    _ensure_task_structure(task_root)
    work_dir = task_root / "work"

    source = source_file
    if source is None:
        candidates = list(work_dir.glob("current.*"))
        if candidates:
            source = candidates[0]
    if source is None:
        source_input = typer.prompt("File to version (path)")
        source = Path(source_input)
    if not source.exists():
        raise typer.BadParameter(f"Source file not found: {source}")

    note = description or typer.prompt("Describe this save")
    version_path, version_index = _next_version_path(task_root, source.suffix)
    saved = _copy_file(source, version_path)
    typer.echo(f"→ Saved {saved}")

    notes_path = task_root / "versions" / f"notes_v{version_index:03d}.txt"
    _write_text(notes_path, f"{note}\n")

    preview_dir = task_root / "previews"
    preview_dir.mkdir(parents=True, exist_ok=True)
    preview_file = preview_dir / f"{version_path.stem}.txt"
    if not preview_file.exists():
        preview_file.write_text("Add preview renders or thumbnails here.\n", encoding="utf-8")

    _log_action(base_root, f"Version → {version_path.relative_to(base_root)} ({note})")


@app.command("deliver")
def cmd_deliver(
    task_path: str = typer.Option(None, "--task", help="Path to task folder (project/target/task)."),
    target: str = typer.Option(None, "--target", help="Delivery target (dailies/client/archive)."),
    root: Path | None = typer.Option(None, "--root", help="Project root (default: current directory)."),
) -> None:
    base_root = _ensure_root(root)
    task_root = _resolve_task(base_root, task_path)
    versions_dir = task_root / "versions"
    files = _version_files(versions_dir)
    if not files:
        raise typer.BadParameter("No versions available. Run 'pipely loop version' first.")
    choice = _prompt_choice("Choose version", [f.name for f in files])
    selected = next(p for p in files if p.name == choice)

    delivery_target = target or typer.prompt("Delivery target (dailies/client/archive)", default="dailies")
    delivery_folder, index = _create_delivery_folder(task_root)
    delivered = _copy_file(selected, delivery_folder / selected.name)

    preview = task_root / "previews" / f"{selected.stem}.txt"
    if preview.exists():
        shutil.copy2(preview, delivery_folder / preview.name)

    manifest = delivery_folder / "README.txt"
    manifest.write_text(
        f"Delivery #{index:03d}\n"
        f"Version: {selected.name}\n"
        f"Target: {delivery_target}\n"
        f"Notes: Add reviewer comments here.\n",
        encoding="utf-8",
    )

    checksum_path = delivery_folder / "checksum.md5"
    checksum_path.write_text(f"{_checksum(delivered)}  {delivered.name}\n", encoding="utf-8")

    _log_action(base_root, f"Deliver → {selected.name} to {delivery_target}")
    typer.echo(f"→ Delivery ready at {delivery_folder}")


def run() -> None:
    app()

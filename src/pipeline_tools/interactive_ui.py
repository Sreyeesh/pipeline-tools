from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable, Callable

from rich.console import Console
from rich.table import Table

from pipeline_tools.core import db
from pipeline_tools.tools.workfiles.main import KIND_EXTENSIONS


def workspace_summary(console: Console, show_code: str | None = None, data: dict | None = None) -> None:
    """Print a compact workspace summary for the current show."""
    data = data or db.load_db()
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

    def _lines(lines: list[str], more: int) -> str:
        extra = f"\n+{more} more" if more > 0 else ""
        return "\n".join(lines) + extra if lines else "—"

    shot_lines = [f"{s['id']} [{s['status']}]" for s in sorted(shots, key=lambda s: s["id"])[:3]]
    asset_lines = [f"{a['id']} [{a['type']}]" for a in sorted(assets, key=lambda a: a["id"])[:3]]
    task_lines = [f"{tid}:{t['name']} [{t['status']}]" for tid, t in tasks[:3]]

    table.add_row(
        _lines(shot_lines, max(0, len(shots) - len(shot_lines))),
        _lines(asset_lines, max(0, len(assets) - len(asset_lines))),
        _lines(task_lines, max(0, len(tasks) - len(task_lines))),
    )
    console.print(table)
    console.print()


def project_structure(console: Console, project_path: Path | None, max_depth: int = 2, max_entries: int = 30) -> None:
    """Print a quick tree of the current project's folders/files (limited depth/entries)."""
    if not project_path:
        console.print("[yellow]No project selected. Type 'projects' to pick one.[/yellow]")
        return
    if not project_path.exists():
        console.print(f"[red]Project path not found:[/red] {project_path}")
        return

    console.print()
    console.print(f"[bold cyan]Project structure[/bold cyan] [dim]{project_path}[/dim]")

    def walk(path: Path, depth: int) -> None:
        if depth > max_depth:
            return
        try:
            entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            console.print("  " * depth + "[red]Permission denied[/red]")
            return

        if len(entries) > max_entries:
            shown = entries[:max_entries]
            extra = len(entries) - max_entries
        else:
            shown = entries
            extra = 0

        for entry in shown:
            prefix = "📁" if entry.is_dir() else "📄"
            console.print(f"{'  ' * depth}{prefix} {entry.name}")
            if entry.is_dir() and depth < max_depth:
                walk(entry, depth + 1)
        if extra > 0:
            console.print(f"{'  ' * (depth + 1)}… +{extra} more")

    walk(project_path, 0)
    console.print()


def render_quick_actions(console: Console, preferred_show: Callable[[str | None], str | None], show_code: str | None = None) -> None:
    example_show = (preferred_show(show_code) or "DMO").upper()
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Action", style="bold", width=18)
    table.add_column("Try typing", style="cyan")
    table.add_row("🎬 Open project", "open project 1 with blender")
    table.add_row("🧭 Switch show", f"switch to show {example_show}")
    table.add_row("🌳 Add asset", f"add environment asset called BG_Forest for show {example_show}")
    table.add_row("🎞 Add shot", f"add shot SH010 Opening scene for show {example_show}")
    table.add_row("📝 Assign task", "assign task animation for shot SH010 to Alice")
    table.add_row("🏗 Structure", "project structure")
    table.add_row("🗂 Workspace", "show workspace")
    table.add_row("🧾 Status", "what's the status")
    table.add_row("🕑 Recent", "show recent assets")
    console.print(table)
    console.print()


def render_core_loop(console: Console, preferred_show: Callable[[str | None], str | None], show_code: str | None = None) -> None:
    example_show = (preferred_show(show_code) or "DMO").upper()
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Step", style="bold cyan", width=8)
    table.add_column("Try typing", style="cyan")
    table.add_row("1) ▶️ Start", 'create a project named "Demo"')
    table.add_row("2) 🖌 Open", "open project 1 with blender (or krita/godot/unity)")
    table.add_row("3) ✅ Do", f"add shot SH010 for show {example_show} and assign to Alice")
    table.add_row("   🎞 Post", "workfiles export --file script.fountain")
    console.print("[bold]Core loop:[/bold] Start → Open → Do (add/assign/export)")
    console.print(table)
    console.print("[dim]Tip: stay in this prompt; just type phrases like the above.[/dim]")
    console.print()


def iter_workfiles_for_kind(base: Path, kind: str) -> list[Path]:
    """Return all workfiles for a given kind under 05_WORK, newest first."""
    ext = KIND_EXTENSIONS.get(kind.lower())
    if not ext:
        return []
    if not base.exists():
        return []
    files = [p for p in base.rglob(f"*.{ext}") if p.is_file()]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files


def format_mtime(path: Path) -> str:
    ts = path.stat().st_mtime
    return datetime.fromtimestamp(ts).strftime("%b %d %H:%M")


def render_workfile_table(console: Console, files: list[Path], show_root: Path) -> None:
    table = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 1))
    table.add_column("#", style="cyan", width=4)
    table.add_column("Target", style="magenta")
    table.add_column("File", style="white")
    table.add_column("Updated", style="dim")
    for idx, f in enumerate(files, 1):
        parts = f.relative_to(show_root).parts
        target = parts[2] if len(parts) >= 3 else "—"
        table.add_row(str(idx), target, f.name, format_mtime(f))
    console.print(table)


def render_target_table(console: Console, target_ids: Iterable[str]) -> None:
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("#", style="cyan", width=4)
    table.add_column("Target ID", style="magenta")
    for idx, tid in enumerate(target_ids, 1):
        table.add_row(str(idx), tid)
    console.print(table)


def artist_workfile_menu(
    console: Console,
    project_path: Path,
    dcc_name: str,
    show_code: str | None,
    data: dict | None = None,
) -> None:
    """
    Artist-friendly menu: pick/open existing workfile, or create + open a new one.
    """
    from pipeline_tools.cli import app

    show_root = project_path
    work_root = show_root / "05_WORK"
    files = iter_workfiles_for_kind(work_root, dcc_name)

    target_ids: list[str] = []
    if show_code:
        data = data or db.load_db()
        target_ids = sorted(
            [a["id"] for a in data.get("assets", {}).values() if a.get("show_code") == show_code]
            + [s["id"] for s in data.get("shots", {}).values() if s.get("show_code") == show_code]
        )

    console.print()
    console.print(f"[bold cyan]STEP 3: Pick Your File ({dcc_name.capitalize()})[/bold cyan]")
    if files:
        render_workfile_table(console, files[:12], show_root)
        if len(files) > 12:
            console.print(f"[dim]+{len(files) - 12} more…[/dim]")
    else:
        console.print("[yellow]No workfiles yet for this app.[/yellow]")

    console.print()
    console.print("[bold]Options:[/bold]")
    console.print("  • Type a [cyan]number[/cyan] to open that file")
    console.print("  • Type [green]n[/green] to create + open a new version")
    console.print("  • Type [blue]o[/blue] to open the app without a file")
    console.print("  • Press [dim]Enter[/dim] to go back")
    console.print()

    while True:
        choice = input("Select: ").strip().lower()
        if not choice:
            return
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(files):
                path = files[idx - 1]
                try:
                    app(["workfiles", "open", "--file", str(path), "--kind", dcc_name], standalone_mode=False)
                except SystemExit:
                    pass
                except Exception as exc:
                    console.print(f"[red]Error:[/red] {exc}")
                return
            console.print(f"[red]Invalid selection. Choose 1-{len(files)}[/red]")
            continue
        if choice == "o":
            try:
                app(["open", dcc_name, "--project", str(show_root)], standalone_mode=False)
            except SystemExit:
                pass
            except Exception as exc:
                console.print(f"[red]Error:[/red] {exc}")
            return
        if choice == "n":
            console.print()
            if target_ids:
                console.print("[bold magenta]Pick a target for the new file[/bold magenta]")
                render_target_table(console, target_ids[:20])
                if len(target_ids) > 20:
                    console.print(f"[dim]+{len(target_ids) - 20} more…[/dim]")
                target_sel = input("Target number (or id): ").strip()
                if not target_sel:
                    return
                if target_sel.isdigit():
                    t_idx = int(target_sel)
                    if 1 <= t_idx <= len(target_ids):
                        target_id = target_ids[t_idx - 1]
                    else:
                        console.print(f"[red]Invalid target. Choose 1-{len(target_ids)}[/red]")
                        continue
                else:
                    target_id = target_sel
            else:
                target_id = input("Target id (e.g., PKU_SH010): ").strip()
                if not target_id:
                    return

            try:
                app(["workfiles", "add", target_id, "--kind", dcc_name, "--open"], standalone_mode=False)
            except SystemExit:
                pass
            except Exception as exc:
                console.print(f"[red]Error:[/red] {exc}")
            return
        console.print("[yellow]Choose a file number, 'n' for new, 'o' to open the app, or Enter to go back.[/yellow]")

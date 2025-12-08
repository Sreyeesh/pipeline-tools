"""Interactive shell for Pipely with autocomplete."""


from __future__ import annotations

import re
import sys
import shlex
from pathlib import Path
from typing import List, Iterable
from datetime import datetime

from pipeline_tools import TASK_STATUS_VALUES
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.table import Table

from pipeline_tools.core import db
from pipeline_tools.tools.project_creator.templates import TEMPLATES
from pipeline_tools.tools.workfiles.main import KIND_EXTENSIONS

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
    # Keep natural phrases like "open project 1 with blender" together
    if re.match(
        r"^(open|select|choose|use)\s+project\s+\d+(?:\s+(?:with|using)\s+.+)?$",
        raw_text.strip(),
        flags=re.IGNORECASE,
    ):
        return [raw_text.strip()]
    # Keep simple list phrases together (list assets/shots/tasks ...)
    if ";" not in raw_text and "\n" not in raw_text and raw_text.strip().lower().startswith("list "):
        return [raw_text.strip()]

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
            # Allow natural phrases like "open project 1" to stay together
            is_open_project_phrase = current_main == "open" and tok == "project"
            # Keep "list assets/ shots/ tasks" together for natural phrasing
            is_list_phrase = current_main == "list"
            if current and tok in passthrough_cmds and not is_sub_of_current and not is_open_project_phrase and not is_list_phrase:
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


def _project_structure(project_path: Path | None, max_depth: int = 2, max_entries: int = 30) -> None:
    """
    Print a quick tree of the current project's folders/files (limited depth/entries).
    """
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


def _find_asset(query: str) -> tuple[str, dict] | None:
    """Find an asset by id or name (case-insensitive, partial ok)."""
    data = db.load_db()
    assets = list(data.get("assets", {}).values())
    if not assets:
        console.print("[yellow]No assets found in DB.[/yellow]")
        return None

    query_lower = query.lower()
    for a in assets:
        if a.get("id", "").lower() == query_lower:
            return a["id"], a
    for a in assets:
        if a.get("name", "").lower() == query_lower:
            return a["id"], a
    matches = [
        a for a in assets if query_lower in a.get("id", "").lower() or query_lower in a.get("name", "").lower()
    ]
    if len(matches) == 1:
        a = matches[0]
        return a["id"], a
    if len(matches) > 1:
        console.print(f"[yellow]Multiple assets match '{query}'. Showing first:[/yellow] {matches[0]['id']}")
        return matches[0]["id"], matches[0]

    console.print(f"[red]Asset matching '{query}' not found.[/red]")
    return None


def _ensure_task_for_asset(asset_id: str, task_name: str, status: str = "in_progress") -> None:
    """Add a task to an asset if missing; update status if present."""
    data = db.load_db()
    tasks = data.setdefault("tasks", {}).setdefault(asset_id, [])
    existing = None
    for t in tasks:
        if t.get("name") == task_name:
            existing = t
            break
    if existing:
        existing["status"] = status
        existing["updated_at"] = datetime.utcnow().isoformat()
        action = "Updated"
    else:
        tasks.append({"name": task_name, "status": status, "updated_at": datetime.utcnow().isoformat()})
        action = "Added"
    db.save_db(data)
    console.print(f"[green]{action} task[/green] '{task_name}' for {asset_id} → {status}")


def _derive_show_root_from_asset_path(asset_path: Path) -> Path | None:
    """Given an asset path, return the show root (parent of 03_ASSETS or 02_PREPRO)."""
    parts = asset_path.parts
    for idx, part in enumerate(parts):
        if part in {"03_ASSETS", "02_PREPRO"}:
            if idx == 0:
                continue
            return Path(*parts[:idx])
    return None


def _prompt_add_asset(default_show: str | None = None, default_name: str | None = None) -> None:
    """Lightweight wizard to add an asset when the user types 'add asset'."""
    from pipeline_tools.cli import app

    console.print()
    console.print("[bold cyan]Add a new asset[/bold cyan]")
    show_code = (default_show or input("Show code (e.g., DMO): ")).strip().upper()
    if not show_code:
        console.print("[yellow]Cancelled (no show code).[/yellow]")
        return
    name = (default_name or input("Asset name (e.g., Forest_BG): ")).strip()
    if not name:
        console.print("[yellow]Cancelled (no name).[/yellow]")
        return
    console.print("Type options: CH (character), ENV (environment), PR (prop), FX, DES, BLN, SND, RND, SC")
    asset_type = input("Type: ").strip().upper()
    if not asset_type:
        console.print("[yellow]Cancelled (no type).[/yellow]")
        return
    try:
        app(["assets", "add", "-c", show_code, "-t", asset_type, "-n", name], standalone_mode=False)
    except SystemExit:
        pass
    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")

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
    "info": "Show current project information",
    "status": "Quick git status for all projects",
    "commit": "Quick commit (prompts for project and message)",
    "help": "Show help menu",
    "exit": "Exit interactive mode",
    "quit": "Exit interactive mode",
}

ASSET_TYPE_ALIASES = {
    "ch": "CH",
    "char": "CH",
    "character": "CH",
    "characters": "CH",
    "env": "ENV",
    "environment": "ENV",
    "environments": "ENV",
    "bg": "ENV",
    "prop": "PR",
    "props": "PR",
    "pr": "PR",
    "fx": "FX",
    "effect": "FX",
    "effects": "FX",
}


def _render_quick_actions() -> None:
    """Small visual menu of common actions for artists."""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Action", style="bold", width=18)
    table.add_column("Try typing", style="cyan")
    table.add_row("🎬 Open project", "open project 1 with blender")
    table.add_row("🧭 Switch show", "switch to show PKU")
    table.add_row("🌳 Add asset", "add environment asset called BG_Forest for show PKU")
    table.add_row("🎞 Add shot", "add shot SH010 Opening scene for show PKU")
    table.add_row("🗂 Workspace", "show workspace")
    table.add_row("🧾 Status", "what's the status")
    table.add_row("🕑 Recent", "show recent assets")
    console.print(table)
    console.print()


def _interpret_natural_command(
    text: str,
    current_project: str | None = None,
    current_project_path: Path | None = None,
    current_show_code: str | None = None,
) -> tuple[list[str], str] | None:
    """
    Map simple natural-language phrases to real pipely commands so artists can type sentences.
    """
    cleaned = text.strip()

    # Create project (interactive)
    m = re.match(
        r"^(create|make|new)\s+(?:a\s+)?(?:new\s+)?project(?:\s+(?:called|named)\s+(?P<name>.+))?$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if m:
        name = (m.group("name") or "").strip()
        args = ["create", "--interactive"]
        if name:
            args.extend(["-n", name])
        return args, "Interpreting request as: pipely " + " ".join(args)

    # Create show (code + optional name)
    m = re.match(
        r"^(create|make|new)\s+(?:a\s+)?(?:new\s+)?show\s+(?P<code>[A-Za-z0-9_-]+)"
        r"(?:\s+(?:called|named)\s+(?P<name>.+))?$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if m:
        code = m.group("code")
        name = (m.group("name") or "").strip()
        args = ["shows", "create", "-c", code]
        if name:
            args.extend(["-n", name])
        return args, "Interpreting request as: pipely " + " ".join(args)

    # Open a DCC
    m = re.match(
        r"^(open|launch|start)\s+(?P<dcc>krita|blender|photoshop|aftereffects|pureref)"
        r"(?:\s+(?:for|in|on)\s+(?P<project>[\w\.-]+))?$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if m:
        dcc = m.group("dcc").lower()
        project = m.group("project") or current_project
        args = ["open", dcc]
        if project:
            args.extend(["--project", project])
        return args, "Interpreting request as: pipely " + " ".join(args)

    # Git status
    m = re.match(
        r"^(what'?s|show|check)?\s*(?:the\s+)?(?:git\s+)?status(?:\s+(?:for|of|on)\s+(?P<project>[\w\.-]+))?$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if m:
        project = m.group("project") or current_project
        args = ["project", "status"]
        if project:
            args.append(project)
        return args, "Interpreting request as: pipely " + " ".join(args)

    # Commit changes
    m = re.match(
        r"^commit(?:\s+my)?(?:\s+changes)?(?:\s+(?:for|in)\s+(?P<project>[\w\.-]+))?"
        r"(?:\s+with\s+(?:message|msg)\s+(?P<message>.+))?$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if m:
        project = m.group("project") or current_project
        message = (m.group("message") or "").strip()
        args = ["project", "commit"]
        if project:
            args.append(project)
        if message:
            args.extend(["-m", message])
        return args, "Interpreting request as: pipely " + " ".join(args)

    # List entities
    m = re.match(r"^list(?:\s+all)?\s+(?P<target>shows|assets|shots|projects)$", cleaned, flags=re.IGNORECASE)
    if m:
        target = m.group("target").lower()
        if target == "projects":
            return ["projects"], "Interpreting request as: pipely projects"
        return [target, "list"], "Interpreting request as: pipely " + target + " list"

    # Recent assets
    m = re.match(
        r"^(show|list|see|display|what(?:'s)?)\s+(?:the\s+)?(?:(?:recent|recently\s+added)\s+assets)(?:\s+(?P<num>\d+))?$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if m:
        num = m.group("num")
        args = ["assets", "recent"]
        if num:
            args.extend(["--limit", num])
        return args, "Interpreting request as: pipely " + " ".join(args)

    # List shows
    m = re.match(r"^(list|show|see)\s+shows$", cleaned, flags=re.IGNORECASE)
    if m:
        return ["shows", "list"], "Interpreting request as: pipely shows list"

    # List assets (optional type/show)
    m = re.match(
        r"^(list|show|see)\s+(?:(?P<type>characters?|assets?|props?|fx|environments?|env|bg)\s+)?assets(?:\s+for\s+show\s+(?P<show>[A-Za-z0-9_-]+))?$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if m:
        asset_type = m.group("type")
        show = m.group("show")
        args = ["assets", "list"]
        if show:
            args.extend(["-c", show])
        if asset_type:
            type_code = ASSET_TYPE_ALIASES.get(asset_type.lower())
            if type_code:
                args.extend(["-t", type_code])
        return args, "Interpreting request as: pipely " + " ".join(args)

    # Asset info
    m = re.match(r"^(show|see|get)\s+asset\s+(?P<asset>[A-Za-z0-9_-]+)$", cleaned, flags=re.IGNORECASE)
    if m:
        asset = m.group("asset")
        return ["assets", "info", asset], f"Interpreting request as: pipely assets info {asset}"

    # Add asset
    m = re.match(
        r"^(add|create|new)\s+(?P<type>characters?|ch|env|environment|environments|bg|props?|pr|fx|effects?)\s+asset\s+(?:called|named\s+)?(?P<name>[A-Za-z0-9._-]+)"
        r"(?:\s+(?:for|in)\s+show\s+(?P<show>[A-Za-z0-9_-]+))?$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if m:
        type_code = ASSET_TYPE_ALIASES.get(m.group("type").lower())
        if not type_code:
            type_code = "ENV"
        name = m.group("name")
        show = m.group("show")
        args = ["assets", "add", "-t", type_code, "-n", name]
        if show:
            args.extend(["-c", show])
        return args, "Interpreting request as: pipely " + " ".join(args)

    # Explicit environment asset phrasing
    m = re.match(
        r"^(add|create|new)\s+environment\s+asset\s+(?:called|named\s+)?(?P<name>[A-Za-z0-9._-]+)"
        r"(?:\s+(?:for|in)\s+show\s+(?P<show>[A-Za-z0-9_-]+))?$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if m:
        name = m.group("name")
        show = m.group("show")
        args = ["assets", "add", "-t", "ENV", "-n", name]
        if show:
            args.extend(["-c", show])
        return args, "Interpreting request as: pipely " + " ".join(args)

    # Generic add asset without explicit type defaults to ENV
    m = re.match(
        r"^(add|create|new)\s+asset\s+(?:called|named\s+)?(?P<name>[A-Za-z0-9._-]+)(?:\s+(?:for|in)\s+show\s+(?P<show>[A-Za-z0-9_-]+))?$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if m:
        name = m.group("name")
        show = m.group("show")
        args = ["assets", "add", "-t", "ENV", "-n", name]
        if show:
            args.extend(["-c", show])
        return args, "Interpreting request as: pipely " + " ".join(args)

    # List shots
    m = re.match(
        r"^(list|show|see)\s+shots(?:\s+for\s+show\s+(?P<show>[A-Za-z0-9_-]+))?$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if m:
        show = m.group("show")
        args = ["shots", "list"]
        if show:
            args.extend(["-c", show])
        return args, "Interpreting request as: pipely " + " ".join(args)

    # Add shot
    m = re.match(
        r"^(add|create|new)\s+shot\s+(?P<code>SH[A-Za-z0-9_-]+)\s+(?P<desc>.+?)(?:\s+(?:for|in)\s+show\s+(?P<show>[A-Za-z0-9_-]+))?$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if m:
        code = m.group("code")
        desc = m.group("desc").strip()
        show = m.group("show")
        tokens = ["shots", "add"]
        if show:
            tokens.extend(["-c", show])
        tokens.append(code)
        tokens.extend(desc.split())
        return tokens, "Interpreting request as: pipely " + " ".join(tokens)

    # List tasks for a target
    m = re.match(
        r"^(list|show|see)\s+tasks\s+(?:for|on)\s+(?P<target>[A-Za-z0-9_-]+)$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if m:
        target = m.group("target")
        return ["tasks", "list", target], f"Interpreting request as: pipely tasks list {target}"

    # Add task to a target
    m = re.match(
        r"^(add|create|new)\s+task\s+(?P<task>.+?)\s+(?:to|for|on)\s+(?P<target>[A-Za-z0-9_-]+)$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if m:
        task_name = m.group("task").strip()
        target = m.group("target")
        return ["tasks", "add", target, task_name], f"Interpreting request as: pipely tasks add {target} \"{task_name}\""

    # Update task status
    m = re.match(
        r"^(set|update|mark)\s+task\s+(?P<task>.+?)\s+(?:for|on)\s+(?P<target>[A-Za-z0-9_-]+)\s+(?:to\s+)?(?P<status>[A-Za-z_\\s]+)$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if m:
        task_name = m.group("task").strip()
        target = m.group("target")
        status = m.group("status").strip().lower().replace(" ", "_")
        if status not in TASK_STATUS_VALUES:
            console.print(f"[red]Unknown status '{status}'. Allowed: {', '.join(sorted(TASK_STATUS_VALUES))}[/red]")
            return None
        return ["tasks", "status", target, task_name, status], f"Interpreting request as: pipely tasks status {target} \"{task_name}\" {status}"

    # Delete task
    m = re.match(
        r"^(delete|remove)\s+task\s+(?P<task>.+?)\s+(?:for|from|on)\s+(?P<target>[A-Za-z0-9_-]+)$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if m:
        task_name = m.group("task").strip()
        target = m.group("target")
        return ["tasks", "delete", target, task_name], f"Interpreting request as: pipely tasks delete {target} \"{task_name}\""

    # Switch show
    m = re.match(
        r"^(switch|change|use)\s+(?:to\s+)?show\s+(?P<code>[A-Za-z0-9_-]+)$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if m:
        code = m.group("code")
        return ["shows", "use", "-c", code], "Interpreting request as: pipely shows use -c " + code

    # Show workspace/structure
    m = re.match(
        r"^(show|display|view|see|open)\s+(?:the\s+)?(?:(?:project\s+)?structure|workspace|files|folders)$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if m or cleaned.lower() in {"structure", "project structure", "workspace structure", "workspace"}:
        return ["structure"], "Interpreting request as: show project structure"

    return None


def _resolve_show_for_project_path(project_path: Path) -> tuple[str | None, dict | None]:
    """Find the DB show entry that matches a project path (by exact root or code in folder name)."""
    data = db.load_db()
    shows = data.get("shows", {}) or {}
    # Exact root match
    for code, show in shows.items():
        root = show.get("root")
        if root and Path(root).resolve() == project_path.resolve():
            return code, show
    # Fallback: try folder name second token as code
    parts = project_path.name.split("_")
    if len(parts) >= 2:
        code_candidate = parts[1]
        if code_candidate in shows:
            return code_candidate, shows[code_candidate]
    return None, None


def _iter_workfiles_for_kind(base: Path, kind: str) -> list[Path]:
    """Return all workfiles for a given kind under 05_WORK, newest first."""
    ext = KIND_EXTENSIONS.get(kind.lower())
    if not ext:
        return []
    if not base.exists():
        return []
    files = [p for p in base.rglob(f"*.{ext}") if p.is_file()]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files


def _format_mtime(path: Path) -> str:
    ts = path.stat().st_mtime
    return datetime.fromtimestamp(ts).strftime("%b %d %H:%M")


def _render_workfile_table(files: list[Path], show_root: Path) -> None:
    table = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 1))
    table.add_column("#", style="cyan", width=4)
    table.add_column("Target", style="magenta")
    table.add_column("File", style="white")
    table.add_column("Updated", style="dim")
    for idx, f in enumerate(files, 1):
        # target id is the parent folder name under workfiles (assets/shots/<id>/kind)
        parts = f.relative_to(show_root).parts
        target = parts[2] if len(parts) >= 3 else "—"
        table.add_row(str(idx), target, f.name, _format_mtime(f))
    console.print(table)


def _render_target_table(target_ids: Iterable[str]) -> None:
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("#", style="cyan", width=4)
    table.add_column("Target ID", style="magenta")
    for idx, tid in enumerate(target_ids, 1):
        table.add_row(str(idx), tid)
    console.print(table)


def _artist_workfile_menu(project_path: Path, dcc_name: str, show_code: str | None) -> None:
    """
    Artist-friendly menu: pick/open existing workfile, or create + open a new one.
    """
    from pipeline_tools.cli import app

    show_root = project_path
    work_root = show_root / "05_WORK"
    files = _iter_workfiles_for_kind(work_root, dcc_name)

    target_ids: list[str] = []
    if show_code:
        data = db.load_db()
        target_ids = sorted([
            a["id"] for a in data.get("assets", {}).values() if a.get("show_code") == show_code
        ] + [
            s["id"] for s in data.get("shots", {}).values() if s.get("show_code") == show_code
        ])

    console.print()
    console.print(f"[bold cyan]STEP 3: Pick Your File ({dcc_name.capitalize()})[/bold cyan]")
    if files:
        _render_workfile_table(files[:12], show_root)
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
            # Show targets if available
            console.print()
            if target_ids:
                console.print("[bold magenta]Pick a target for the new file[/bold magenta]")
                _render_target_table(target_ids[:20])
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
    console.print("│  [dim]Or just type: 'create a project named Demo'[/dim]        │")
    console.print("╰────────────────────────────────────────────────────────╯", style="cyan")
    console.print()
    _render_quick_actions()

    # Track available projects and DCCs for number selection
    available_projects = []
    available_dccs = []
    current_project = None
    current_project_path: Path | None = None
    current_show_entry: dict | None = None
    current_show_code: str | None = None
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

                # Asset add helper when no type/name provided
                m_add_asset = re.match(
                    r"^(help\\s+me\\s+)?add\\s+asset(?:\\s+(?:called|named)\\s+(?P<name>[A-Za-z0-9._-]+))?(?:\\s+(?:for|in)\\s+show\\s+(?P<show>[A-Za-z0-9_-]+))?$",
                    text,
                    flags=re.IGNORECASE,
                )
                if m_add_asset:
                    _prompt_add_asset(default_show=m_add_asset.group("show"), default_name=m_add_asset.group("name"))
                    continue

                # One-shot: "work on <asset> in <dcc> [task <name>]"
                m_work = re.match(
                    r"^(work on|start)\s+(?:asset\s+)?(?P<asset>[\w\.-]+)(?:\s+(?:in|with)\s+(?P<dcc>krita|blender|photoshop|aftereffects|pureref))?(?:\s+task\s+(?P<task>.+))?$",
                    text,
                    flags=re.IGNORECASE,
                )
                if m_work:
                    asset_query = m_work.group("asset")
                    dcc_name = (m_work.group("dcc") or "").lower()
                    task_name = m_work.group("task")
                    result = _find_asset(asset_query)
                    if not result:
                        continue
                    asset_id, asset_entry = result
                    show_code = asset_entry.get("show_code")
                    # Derive project path from asset path
                    asset_path = Path(asset_entry.get("path", ""))
                    show_root = _derive_show_root_from_asset_path(asset_path)
                    if not show_root or not show_root.exists():
                        console.print(f"[red]Could not locate project folder for asset {asset_id}[/red]")
                        continue

                    current_project = show_root.name
                    current_project_path = show_root
                    current_show_code = show_code

                    # Set default task name if not provided
                    task_label = task_name or (dcc_name.capitalize() + " work" if dcc_name else "Work")
                    _ensure_task_for_asset(asset_id, task_label, status="in_progress")

                    # Require a DCC to proceed to workfiles menu
                    if not dcc_name:
                        console.print("[yellow]Add a DCC: e.g., 'work on PKU_ENV_BG_Forest in krita'.[/yellow]")
                        continue

                    from pipeline_tools.tools.dcc_launcher.launcher import get_dcc_executable

                    if not get_dcc_executable(dcc_name):
                        console.print(f"[red]{dcc_name} not installed or not found.[/red]")
                        continue

                    console.print(f"[green]✓ Asset:[/green] {asset_id}  [dim]({show_root})[/dim]")
                    _artist_workfile_menu(current_project_path, dcc_name, current_show_code)
                    if workspace_summary_enabled:
                        _workspace_summary()
                    continue

                # Allow phrases like "open project 1" (optionally with a DCC) to act like selecting that project
                m_proj_select = re.match(
                    r"^(open|select|choose|use)\s+project\s+(?P<num>\d+)(?:\s+(?:with|using)\s+(?P<dcc>krita|blender|photoshop|aftereffects|pureref))?$",
                    text,
                    flags=re.IGNORECASE,
                )
                if m_proj_select and available_projects:
                    choice = int(m_proj_select.group("num"))
                    chosen_dcc = m_proj_select.group("dcc").lower() if m_proj_select.group("dcc") else None
                    create_option_num = len(available_projects) + 1

                    if choice == create_option_num:
                        console.print()
                        console.print("[bold cyan]🆕 Create New Project[/bold cyan]")
                        console.print()
                        from pipeline_tools.cli import app
                        try:
                            app(["create", "--interactive"], standalone_mode=False)
                        except SystemExit:
                            pass
                        except Exception as e:
                            console.print(f"[red]Error:[/red] {e}")
                        console.print()
                        console.print("[dim]Type 'projects' to see your new project[/dim]")
                        console.print()
                        continue

                    if 1 <= choice <= len(available_projects):
                        selected_project = available_projects[choice - 1]
                        current_project = selected_project.name
                        current_project_path = selected_project
                        current_show_code, current_show_entry = _resolve_show_for_project_path(selected_project)

                        console.print(f"[dim]Selecting project #{choice}: {current_project}[/dim]")
                        console.print(f"[green]✓ Project:[/green] [bold]{current_project}[/bold]")
                        if current_show_code:
                            console.print(f"[dim]Linked show:[/dim] {current_show_code}")
                            try:
                                from pipeline_tools.cli import app
                                app(["shows", "use", "-c", current_show_code], standalone_mode=False)
                            except Exception:
                                pass
                        console.print()

                        if chosen_dcc:
                            _artist_workfile_menu(current_project_path or Path.cwd(), chosen_dcc, current_show_code)
                            console.print()
                            console.print("[dim]Type 'projects' to work on another project[/dim]")
                            console.print()
                            show_dcc_menu = False
                            available_dccs = []
                            completer.update_context(dccs=[], show_dcc_menu=False)
                            if workspace_summary_enabled:
                                _workspace_summary()
                            continue

                        from pipeline_tools.tools.dcc_launcher.launcher import DCC_PATHS, get_dcc_executable
                        from rich.table import Table

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
                        completer.update_context(dccs=available_dccs, show_dcc_menu=True)

                        table = Table(show_header=False, box=None, padding=(0, 2))
                        table.add_column("Number", style="cyan bold", width=8)
                        table.add_column("Application", style="bold")

                        for idx, dcc in enumerate(installed_dccs, 1):
                            table.add_row(f"[cyan]{idx}[/cyan]", dcc.capitalize())

                        console.print("[bold cyan]STEP 2: Pick Your App[/bold cyan]")
                        console.print()
                        console.print(table)
                        console.print()
                        console.print("[dim]→ Type a number or press TAB to see all options[/dim]")
                        console.print()
                        continue
                    else:
                        console.print()
                        console.print(f"[red]❌ Invalid selection. Choose 1-{create_option_num}[/red]")
                        console.print()
                        continue

                # Friendly natural-language intents
                natural = _interpret_natural_command(text, current_project, current_project_path, current_show_code)
                if natural:
                    parts, note = natural
                    text = " ".join(parts)
                    console.print(f"[dim]{note}[/dim]")
                else:
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

                if text in {"structure", "project structure", "workspace structure", "show structure"}:
                    _project_structure(current_project_path)
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

                if text == "info":
                    # Show info about current project without opening app picker
                    if current_project and current_project_path:
                        console.print()
                        console.print(f"[bold cyan]Project Information[/bold cyan]")
                        console.print(f"[bold]Name:[/bold] {current_project}")
                        console.print(f"[bold]Path:[/bold] {current_project_path}")
                        if current_show_code:
                            console.print(f"[bold]Show:[/bold] {current_show_code}")

                        # Show git status if available
                        git_dir = current_project_path / '.git'
                        if git_dir.exists():
                            try:
                                import subprocess
                                result = subprocess.run(
                                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                                    cwd=current_project_path,
                                    capture_output=True,
                                    text=True,
                                    timeout=1
                                )
                                if result.returncode == 0:
                                    branch_name = result.stdout.strip()
                                    console.print(f"[bold]Branch:[/bold] {branch_name}")

                                # Show git status summary
                                result = subprocess.run(
                                    ["git", "status", "--short"],
                                    cwd=current_project_path,
                                    capture_output=True,
                                    text=True,
                                    timeout=2
                                )
                                if result.returncode == 0 and result.stdout.strip():
                                    console.print(f"[bold]Status:[/bold] [yellow]{len(result.stdout.strip().splitlines())} changed file(s)[/yellow]")
                                elif result.returncode == 0:
                                    console.print(f"[bold]Status:[/bold] [green]Clean working tree[/green]")
                            except Exception:
                                pass

                        console.print()
                    else:
                        console.print()
                        console.print("[yellow]No project selected. Type 'projects' to pick one.[/yellow]")
                        console.print()
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

                            console.print()
                            _artist_workfile_menu(current_project_path or Path.cwd(), dcc_name, current_show_code)
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
                            current_project_path = selected_project
                            current_show_code, current_show_entry = _resolve_show_for_project_path(selected_project)

                            console.print()
                            console.print(f"[green]✓ Project:[/green] [bold]{current_project}[/bold]")
                            if current_show_code:
                                console.print(f"[dim]Linked show:[/dim] {current_show_code}")
                                try:
                                    from pipeline_tools.cli import app
                                    app(["shows", "use", "-c", current_show_code], standalone_mode=False)
                                except Exception:
                                    pass
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
                    _render_quick_actions()

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

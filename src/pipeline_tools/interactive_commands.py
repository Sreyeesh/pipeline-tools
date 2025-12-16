from __future__ import annotations

import re
import shlex
from pathlib import Path
from typing import Iterable

from rich.console import Console

from pipeline_tools import TASK_STATUS_VALUES
from pipeline_tools.core import db
from pipeline_tools.tools.project_creator.templates import TEMPLATES


COMMANDS = {
    "create": ["--interactive", "-c", "--show-code", "-n", "--name", "-t", "--template", "--git", "--git-lfs"],
    "open": [
        "krita",
        "blender",
        "photoshop",
        "aftereffects",
        "pureref",
        "--list",
        "-l",
        "--list-projects",
        "--project",
        "-p",
        "--choose",
        "-c",
        "--background",
        "-b",
    ],
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


def split_user_commands(raw_text: str, passthrough_cmds: set[str], commands_map: dict[str, list[str]]) -> list[str]:
    """
    Split pasted input into individual commands including natural-language helpers.
    """
    cleaned = raw_text.strip()
    if not cleaned:
        return []

    if re.match(
        r"^(open|select|choose|use)\s+project\s+\d+(?:\s+(?:with|using)\s+.+)?$",
        cleaned,
        flags=re.IGNORECASE,
    ):
        return [cleaned]

    if re.match(
        r"^(create|make|new)\s+(?:a\s+)?(?:new\s+)?project\b.*$",
        cleaned,
        flags=re.IGNORECASE,
    ):
        return [cleaned]

    if ";" not in raw_text and "\n" not in raw_text and cleaned.lower().startswith("list "):
        return [cleaned]

    normalized = raw_text.replace(";", "\n")

    subcommand_tokens: set[str] = set()
    for subs in commands_map.values():
        subcommand_tokens.update(subs)
    top_level_tokens = [cmd for cmd in passthrough_cmds if cmd not in subcommand_tokens]

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
            is_sub_of_current = current_main in commands_map and tok in commands_map[current_main]
            is_open_project_phrase = current_main == "open" and tok == "project"
            is_list_phrase = current_main == "list"
            if (
                current
                and tok in passthrough_cmds
                and not is_sub_of_current
                and not is_open_project_phrase
                and not is_list_phrase
            ):
                commands.append(" ".join(current))
                current = [tok]
            else:
                current.append(tok)
        if current:
            commands.append(" ".join(current))
    return commands


def normalize_shorthand_command(parts: list[str]) -> list[str]:
    """
    Allow artist-friendly shorthand commands (shows create DMO "Demo" animation_short).
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


def preferred_show_code(explicit: str | None = None) -> str | None:
    """Pick a reasonable show code for examples: explicit -> current -> first show."""
    if explicit:
        return explicit
    try:
        data = db.load_db()
        if data.get("current_show"):
            return data.get("current_show")
        shows = data.get("shows") or {}
        if shows:
            return sorted(shows.keys())[0]
    except Exception:
        pass
    return None


def infer_show_code_token(target: str, fallback: str | None = None) -> str | None:
    """Guess show code from a project folder/name like AN_DMO_DemoShort."""
    token = target.strip()
    if not token:
        return fallback
    parts = token.split("_")
    if len(parts) >= 2:
        candidate = parts[1].upper()
        if 2 <= len(candidate) <= 8:
            return candidate
    alnum = re.sub(r"[^A-Za-z0-9]", "", token).upper()
    if 2 <= len(alnum) <= 8:
        return alnum
    return fallback


def interpret_natural_command(
    text: str,
    console: Console,
    current_project: str | None = None,
    current_project_path: Path | None = None,
    current_show_code: str | None = None,
) -> tuple[list[str], str] | None:
    """
    Map simple natural-language phrases to real pipely commands so artists can type sentences.
    """
    cleaned = text.strip()

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

    m = re.match(
        r"^(delete|remove)\s+(?P<target>[A-Za-z0-9._-]+)$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if m:
        target = m.group("target")
        show_code = None
        parts = target.split("_")
        if len(parts) >= 2 and len(parts[1]) <= 6:
            show_code = parts[1]
        elif len(target) <= 6:
            show_code = target
        elif current_show_code:
            show_code = current_show_code
        if not show_code:
            console.print("[yellow]Unable to infer show code to delete.[/yellow]")
            return None
        args = ["shows", "delete", "-c", show_code, "--delete-folders"]
        return args, "Interpreting request as: pipely " + " ".join(args)

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

    m = re.match(r"^list(?:\s+all)?\s+(?P<target>shows|assets|shots|projects)$", cleaned, flags=re.IGNORECASE)
    if m:
        target = m.group("target").lower()
        if target == "projects":
            return ["projects"], "Interpreting request as: pipely projects"
        return [target, "list"], "Interpreting request as: pipely " + target + " list"

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

    m = re.match(r"^(list|show|see)\s+shows$", cleaned, flags=re.IGNORECASE)
    if m:
        return ["shows", "list"], "Interpreting request as: pipely shows list"

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

    m = re.match(r"^(show|see|get)\s+asset\s+(?P<asset>[A-Za-z0-9_-]+)$", cleaned, flags=re.IGNORECASE)
    if m:
        asset = m.group("asset")
        return ["assets", "info", asset], f"Interpreting request as: pipely assets info {asset}"

    m = re.match(
        r"^(add|create|new)\s+(?P<type>characters?|ch|env|environment|environments|bg|props?|pr|fx|effects?)\s+asset\s+(?:(?:called|named)\s+)?(?P<name>[A-Za-z0-9._-]+)"
        r"(?:\s+(?:for|in)\s+show\s+(?P<show>[A-Za-z0-9_-]+))?$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if m:
        type_code = ASSET_TYPE_ALIASES.get(m.group("type").lower()) or "ENV"
        name = m.group("name")
        show = m.group("show")
        args = ["assets", "add", "-t", type_code, "-n", name]
        if show:
            args.extend(["-c", show])
        return args, "Interpreting request as: pipely " + " ".join(args)

    m = re.match(
        r"^(add|create|new)\s+environment\s+asset\s+(?:(?:called|named)\s+)?(?P<name>[A-Za-z0-9._-]+)"
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

    m = re.match(
        r"^(add|create|new)\s+asset\s+(?:(?:called|named)\s+)?(?P<name>[A-Za-z0-9._-]+)(?:\s+(?:for|in)\s+show\s+(?P<show>[A-Za-z0-9_-]+))?$",
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

    m = re.match(
        r"^(list|show|see)\s+tasks\s+(?:for|on)\s+(?P<target>[A-Za-z0-9_-]+)$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if m:
        target = m.group("target")
        return ["tasks", "list", target], f"Interpreting request as: pipely tasks list {target}"

    m = re.match(
        r"^(add|create|new)\s+task\s+(?P<task>.+?)\s+(?:to|for|on)\s+(?P<target>[A-Za-z0-9_-]+)$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if m:
        task_name = m.group("task").strip()
        target = m.group("target")
        return ["tasks", "add", target, task_name], f"Interpreting request as: pipely tasks add {target} \"{task_name}\""

    m = re.match(
        r"^(set|update|mark)\s+task\s+(?P<task>.+?)\s+(?:for|on)\s+(?P<target>[A-Za-z0-9_-]+)\s+(?:to\s+)?(?P<status>[A-Za-z_\s]+)$",
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

    m = re.match(
        r"^(delete|remove)\s+task\s+(?P<task>.+?)\s+(?:for|from|on)\s+(?P<target>[A-Za-z0-9_-]+)$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if m:
        task_name = m.group("task").strip()
        target = m.group("target")
        return ["tasks", "delete", target, task_name], f"Interpreting request as: pipely tasks delete {target} \"{task_name}\""

    m = re.match(
        r"^(switch|change|use)\s+(?:to\s+)?show\s+(?P<code>[A-Za-z0-9_-]+)$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if m:
        code = m.group("code")
        return ["shows", "use", "-c", code], "Interpreting request as: pipely shows use -c " + code

    m = re.match(
        r"^(show|display|view|see|open)\s+(?:the\s+)?(?:(?:project\s+)?structure|workspace|files|folders)$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if m or cleaned.lower() in {"structure", "project structure", "workspace structure", "workspace"}:
        return ["structure"], "Interpreting request as: show project structure"

    return None

import argparse
import sys
import shutil
from pathlib import Path
from typing import Optional

from pipeline_tools.core import db
from pipeline_tools.core.cli import FriendlyArgumentParser
from pipeline_tools.core.fs_utils import create_folders
from pipeline_tools.core.paths import make_show_root
from pipeline_tools.tools.project_creator.templates import TEMPLATES
from datetime import datetime, timezone


def _get_show_or_exit(show_code: str, data: dict) -> dict:
    show = data["shows"].get(show_code)
    if not show:
        print(f"Show '{show_code}' not found. Create it first with show_create.")
        sys.exit(1)
    return show


def _resolve_show_code(args_show: Optional[str], data: dict) -> str:
    if args_show:
        return args_show
    current = data.get("current_show")
    if not current:
        print("No show specified and no current show is set. Use show_use or pass --show-code.")
        sys.exit(1)
    return current


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = FriendlyArgumentParser(
        description="Show-level commands: create, list, use, info."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    c_create = sub.add_parser("create", help="Create a show folder and register it.")
    c_create.add_argument("-c", "--show-code", required=True, help="Show code, e.g. DMO")
    c_create.add_argument("-n", "--name", required=True, help='Show name, e.g. "Demo Short 30s"')
    c_create.add_argument(
        "-t",
        "--template",
        default="animation_short",
        help=(
            "Folder template key to use. Available: "
            f"{', '.join(sorted(TEMPLATES.keys()))} (default: animation_short)"
        ),
    )

    c_list = sub.add_parser("list", help="List shows in the DB.")
    c_list.add_argument("-v", "--verbose", action="store_true", help="Include template info.")

    c_use = sub.add_parser("use", help="Set the current show.")
    c_use.add_argument("-c", "--show-code", required=True, help="Show code to set as current.")

    c_info = sub.add_parser("info", help="Show details for one show.")
    c_info.add_argument("-c", "--show-code", help="Show code (defaults to current).")

    c_delete = sub.add_parser("delete", help="Delete a show record (DB only).")
    c_delete.add_argument("-c", "--show-code", required=True, help="Show code to delete.")
    c_delete.add_argument(
        "--force", action="store_true", help="Skip warning about existing folders (keeps folders)."
    )
    c_delete.add_argument(
        "--delete-folders", action="store_true", help="Also delete the show folder from disk."
    )

    c_rename = sub.add_parser("rename", help="Rename a show code in the DB.")
    c_rename.add_argument("old_code", help="Existing show code.")
    c_rename.add_argument("new_code", help="New show code.")
    c_rename.add_argument(
        "--name",
        help="Optional new show name (defaults to existing).",
    )

    c_root = sub.add_parser("root", help="Print root path for a show.")
    c_root.add_argument("-c", "--show-code", help="Show code (defaults to current).")

    c_templates = sub.add_parser("templates", help="List available templates.")

    c_summary = sub.add_parser("summary", help="Summary for one show.")
    c_summary.add_argument("-c", "--show-code", help="Show code (defaults to current).")

    return parser.parse_args(argv)


def cmd_create(args: argparse.Namespace) -> None:
    template_key = args.template
    if template_key not in TEMPLATES:
        print(f"Unknown template '{template_key}'. Available: {', '.join(sorted(TEMPLATES.keys()))}")
        sys.exit(1)

    data = db.load_db()

    show_code = args.show_code
    if show_code in data["shows"]:
        print(f"Show '{show_code}' already exists in the DB.")
        sys.exit(1)

    show_root: Path = make_show_root(show_code, args.name, template_key=template_key)
    if show_root.exists():
        print(
            f"Show folder already exists: {show_root}\n"
            "Cowardly refusing to overwrite. Choose a different show code/name or remove the existing folder."
        )
        sys.exit(1)

    print(f"Creating show at: {show_root}")
    create_folders(show_root, TEMPLATES[template_key])

    now = datetime.now(timezone.utc).isoformat()
    data["shows"][show_code] = {
        "code": show_code,
        "name": args.name,
        "template": template_key,
        "root": str(show_root),
        "created_at": now,
        "updated_at": now,
    }
    data["current_show"] = show_code
    db.save_db(data)
    print(f"Registered show '{show_code}' and set as current.")


def cmd_list(args: argparse.Namespace) -> None:
    data = db.load_db()
    shows = data.get("shows", {})
    if not shows:
        print("No shows found.")
        return
    for code in sorted(shows.keys()):
        show = shows[code]
        line = f"{code} | {show['name']} | {show['root']}"
        if args.verbose:
            line += f" | template={show.get('template')}"
        if data.get("current_show") == code:
            line += "  (current)"
        print(line)


def cmd_use(args: argparse.Namespace) -> None:
    data = db.load_db()
    _get_show_or_exit(args.show_code, data)
    data["current_show"] = args.show_code
    db.save_db(data)
    print(f"Current show set to {args.show_code}.")


def cmd_info(args: argparse.Namespace) -> None:
    data = db.load_db()
    show_code = _resolve_show_code(args.show_code, data)
    show = _get_show_or_exit(show_code, data)
    assets = data.get("assets", {})
    assets_for_show = [a for a in assets.values() if a.get("show_code") == show_code]
    status_counts: dict[str, int] = {}
    for asset in assets_for_show:
        status = asset.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1

    print(f"Show: {show['code']} | {show['name']}")
    print(f"Root: {show['root']}")
    print(f"Template: {show.get('template')}")
    print(f"Assets: {len(assets_for_show)}")
    if status_counts:
        parts = [f"{k}:{v}" for k, v in sorted(status_counts.items())]
        print("Asset statuses: " + ", ".join(parts))
    else:
        print("Asset statuses: none")


def cmd_delete(args: argparse.Namespace) -> None:
    data = db.load_db()
    show = data["shows"].get(args.show_code)
    if not show:
        print(f"Show '{args.show_code}' not found.")
        sys.exit(1)

    root = Path(show["root"])
    if root.exists():
        if args.delete_folders:
            try:
                shutil.rmtree(root)
                print(f"Deleted show folder: {root}")
            except Exception as exc:
                print(f"Failed to delete show folder '{root}': {exc}")
                sys.exit(1)
        elif not args.force:
            print(
                f"Show folder exists at {root}. Delete it, use --delete-folders to remove it automatically, or pass --force to keep folders and only remove the DB record."
            )
            sys.exit(1)

    # Drop assets/shots tied to the show
    assets = {
        k: v for k, v in data.get("assets", {}).items() if v.get("show_code") != args.show_code
    }
    shots = {
        k: v for k, v in data.get("shots", {}).items() if v.get("show_code") != args.show_code
    }
    data["assets"] = assets
    data["shots"] = shots
    data["tasks"] = {k: v for k, v in data.get("tasks", {}).items() if not k.startswith(args.show_code + "_")}
    data["versions"] = {
        k: v for k, v in data.get("versions", {}).items() if v.get("show_code") != args.show_code
    }
    data["notes"] = [n for n in data.get("notes", []) if n.get("show_code") != args.show_code]

    del data["shows"][args.show_code]
    if data.get("current_show") == args.show_code:
        data["current_show"] = None
    db.save_db(data)
    print(f"Deleted show '{args.show_code}' from DB.")


def cmd_rename(args: argparse.Namespace) -> None:
    data = db.load_db()
    show = data["shows"].get(args.old_code)
    if not show:
        print(f"Show '{args.old_code}' not found.")
        sys.exit(1)
    if args.new_code in data["shows"]:
        print(f"Show '{args.new_code}' already exists.")
        sys.exit(1)

    now = datetime.now(timezone.utc).isoformat()
    new_show = dict(show)
    new_show["code"] = args.new_code
    if args.name:
        new_show["name"] = args.name
    new_show["updated_at"] = now

    data["shows"][args.new_code] = new_show
    del data["shows"][args.old_code]

    # Update assets/shots/tasks/versions to reference new code (paths unchanged)
    id_map: dict[str, str] = {}

    new_assets = {}
    for asset_id, asset in data.get("assets", {}).items():
        if asset.get("show_code") == args.old_code:
            updated = dict(asset)
            updated["show_code"] = args.new_code
            clean_name = "".join(updated["name"].split())
            new_id = f"{args.new_code}_{updated['type']}_{clean_name}"
            id_map[asset_id] = new_id
            updated["id"] = new_id
            new_assets[new_id] = updated
        else:
            new_assets[asset_id] = asset
    data["assets"] = new_assets

    new_shots = {}
    for shot_id, shot in data.get("shots", {}).items():
        if shot.get("show_code") == args.old_code:
            updated = dict(shot)
            updated["show_code"] = args.new_code
            base_code = shot.get("code") or shot_id.split("_")[-1]
            new_id = f"{args.new_code}_{base_code}"
            id_map[shot_id] = new_id
            updated["id"] = new_id
            new_shots[new_id] = updated
        else:
            new_shots[shot_id] = shot
    data["shots"] = new_shots

    # Tasks keyed by target_id
    new_tasks = {}
    for target_id, tasks in data.get("tasks", {}).items():
        new_id = id_map.get(target_id, target_id.replace(args.old_code + "_", args.new_code + "_"))
        new_tasks[new_id] = tasks
    data["tasks"] = new_tasks

    new_versions = {}
    for ver_id, ver in data.get("versions", {}).items():
        updated = dict(ver)
        if ver.get("show_code") == args.old_code:
            updated["show_code"] = args.new_code
        new_id = ver_id.replace(args.old_code + "_", args.new_code + "_")
        new_versions[new_id] = updated
    data["versions"] = new_versions

    if data.get("current_show") == args.old_code:
        data["current_show"] = args.new_code

    db.save_db(data)
    print(f"Renamed show '{args.old_code}' to '{args.new_code}' in DB (paths unchanged).")


def cmd_root(args: argparse.Namespace) -> None:
    data = db.load_db()
    show_code = _resolve_show_code(args.show_code, data)
    show = _get_show_or_exit(show_code, data)
    print(show["root"])


def cmd_templates() -> None:
    for key in sorted(TEMPLATES.keys()):
        print(f"{key}")


def cmd_summary(args: argparse.Namespace) -> None:
    data = db.load_db()
    show_code = _resolve_show_code(args.show_code, data)
    _get_show_or_exit(show_code, data)

    assets = [
        a
        for a in data.get("assets", {}).values()
        if a.get("show_code") == show_code
    ]
    shots = [
        s
        for s in data.get("shots", {}).values()
        if s.get("show_code") == show_code
    ]

    asset_status_counts: dict[str, int] = {}
    for a in assets:
        st = a.get("status", "unknown")
        asset_status_counts[st] = asset_status_counts.get(st, 0) + 1

    shot_status_counts: dict[str, int] = {}
    for s in shots:
        st = s.get("status", "unknown")
        shot_status_counts[st] = shot_status_counts.get(st, 0) + 1

    print(f"Show: {show_code}")
    print(f"Assets: {len(assets)} ({', '.join(f'{k}:{v}' for k,v in sorted(asset_status_counts.items())) or 'none'})")
    print(f"Shots: {len(shots)} ({', '.join(f'{k}:{v}' for k,v in sorted(shot_status_counts.items())) or 'none'})")


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.command == "create":
        cmd_create(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "use":
        cmd_use(args)
    elif args.command == "info":
        cmd_info(args)
    elif args.command == "delete":
        cmd_delete(args)
    elif args.command == "rename":
        cmd_rename(args)
    elif args.command == "root":
        cmd_root(args)
    elif args.command == "templates":
        cmd_templates()
    elif args.command == "summary":
        cmd_summary(args)
    else:
        print("Unknown command")
        sys.exit(1)


if __name__ == "__main__":
    main()

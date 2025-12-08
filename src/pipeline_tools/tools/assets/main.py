import argparse
import sys
from pathlib import Path
from typing import Optional

from datetime import datetime

from pipeline_tools import DB_STATUS_VALUES
from pipeline_tools.core import db
from pipeline_tools.core.cli import FriendlyArgumentParser
from pipeline_tools.core.fs_utils import create_folders
from pipeline_tools.core.paths import make_show_root
from rich.console import Console
from rich.table import Table

ASSET_TYPE_DIRS = {
    "CH": "characters",
    "ENV": "environments",
    "PR": "props",
    "SC": "script",  # Pre-production: screenplays/scripts
    "FX": "fx",  # Effects and animation helpers
    "DES": "designs",  # Design sheets
    "BLN": "blender",  # Blender project files
    "SND": "sound",  # Sound/audio assets
    "RND": "renders",  # Render outputs
}
DEFAULT_STATUS = "design"
console = Console()


def _resolve_show_code(args_show: Optional[str], data: dict) -> str:
    if args_show:
        return args_show
    current = data.get("current_show")
    if not current:
        print("No show specified and no current show is set. Use show_use or pass --show-code.")
        sys.exit(1)
    return current


def _get_show_or_exit(show_code: str, data: dict) -> dict:
    show = data["shows"].get(show_code)
    if not show:
        print(f"Show '{show_code}' not found. Create it first with show_create.")
        sys.exit(1)
    return show


def _asset_id(show_code: str, asset_type: str, name: str) -> str:
    clean_name = "".join(name.split())
    return f"{show_code.upper()}_{asset_type.upper()}_{clean_name}"


def _asset_path(show_root: Path, asset_type: str, name: str) -> Path:
    clean_name = "".join(name.split())
    type_dir = ASSET_TYPE_DIRS[asset_type.upper()]
    # Scripts go in pre-production folder, other assets in 03_ASSETS
    if asset_type.upper() == "SC":
        return show_root / "02_PREPRO" / type_dir / clean_name
    return show_root / "03_ASSETS" / type_dir / clean_name


def _ensure_status(status: str) -> None:
    if status not in DB_STATUS_VALUES:
        print(f"Invalid status '{status}'. Allowed: {', '.join(sorted(DB_STATUS_VALUES))}")
        sys.exit(1)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = FriendlyArgumentParser(description="Asset-level commands: add, list, info, status, find, tags.")
    sub = parser.add_subparsers(dest="command", required=True)

    c_add = sub.add_parser("add", help="Create an asset and its folder.")
    c_add.add_argument("--show-code", "-c", help="Show code (defaults to current).")
    c_add.add_argument("--type", "-t", required=True, choices=sorted(ASSET_TYPE_DIRS.keys()), help="Asset type: CH/ENV/PR.")
    c_add.add_argument("--name", "-n", required=True, help="Asset name, e.g. Hero.")

    c_list = sub.add_parser("list", help="List assets for a show.")
    c_list.add_argument("--show-code", "-c", help="Show code (defaults to current).")
    c_list.add_argument("--type", "-t", choices=sorted(ASSET_TYPE_DIRS.keys()), help="Filter by type.")
    c_list.add_argument("--status", choices=sorted(DB_STATUS_VALUES), help="Filter by status.")

    c_info = sub.add_parser("info", help="Show details for one asset.")
    c_info.add_argument("asset_id", help="Asset ID, e.g. DMO_CH_Hero")

    c_status = sub.add_parser("status", help="Update asset status.")
    c_status.add_argument("asset_id", help="Asset ID, e.g. DMO_CH_Hero")
    c_status.add_argument("status", choices=sorted(DB_STATUS_VALUES), help="New status.")

    c_delete = sub.add_parser("delete", help="Delete an asset from DB (keeps folders).")
    c_delete.add_argument("asset_id", help="Asset ID to delete.")

    c_rename = sub.add_parser("rename", help="Rename an asset in DB (folders unchanged).")
    c_rename.add_argument("asset_id", help="Existing asset ID.")
    c_rename.add_argument("new_name", help="New human-readable name.")

    c_tag = sub.add_parser("tag", help="Add a tag to an asset.")
    c_tag.add_argument("asset_id", help="Asset ID.")
    c_tag.add_argument("tag", help="Tag to add.")

    c_untag = sub.add_parser("untag", help="Remove a tag from an asset.")
    c_untag.add_argument("asset_id", help="Asset ID.")
    c_untag.add_argument("tag", help="Tag to remove.")

    c_find = sub.add_parser("find", help="Find assets by partial name or tag.")
    c_find.add_argument("--show-code", "-c", help="Show code (defaults to current).")
    c_find.add_argument("--name", help="Partial name/ID match.")
    c_find.add_argument("--tag", help="Filter by tag.")

    c_recent = sub.add_parser("recent", help="List recently updated assets.")
    c_recent.add_argument("--limit", type=int, default=5, help="Number to show (default 5).")

    return parser.parse_args(argv)


def cmd_add(args: argparse.Namespace) -> None:
    data = db.load_db()
    show_code = _resolve_show_code(args.show_code, data)
    show = _get_show_or_exit(show_code, data)

    asset_type = args.type.upper()
    asset_id = _asset_id(show_code, asset_type, args.name)
    if asset_id in data["assets"]:
        print(f"Asset '{asset_id}' already exists.")
        sys.exit(1)

    show_root = Path(show["root"])
    asset_path = _asset_path(show_root, asset_type, args.name)

    rels = [
        asset_path.relative_to(show_root),
        asset_path.relative_to(show_root) / "workfiles",
        asset_path.relative_to(show_root) / "renders",
    ]
    create_folders(show_root, [str(r) for r in rels])

    now = datetime.utcnow().isoformat()
    data["assets"][asset_id] = {
        "id": asset_id,
        "show_code": show_code,
        "type": asset_type,
        "name": args.name,
        "status": DEFAULT_STATUS,
        "path": str(asset_path),
        "tags": [],
        "created_at": now,
        "updated_at": now,
    }
    db.save_db(data)
    print(f"Created asset {asset_id}")
    print(f"Path: {asset_path}")


def cmd_list(args: argparse.Namespace) -> None:
    data = db.load_db()
    show_code = _resolve_show_code(args.show_code, data)
    _get_show_or_exit(show_code, data)
    assets = [
        a
        for a in data.get("assets", {}).values()
        if a.get("show_code") == show_code
    ]

    if args.type:
        assets = [a for a in assets if a.get("type") == args.type]
    if args.status:
        assets = [a for a in assets if a.get("status") == args.status]

    if not assets:
        print("No assets found.")
        return

    table = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 1))
    table.add_column("ID", style="bold", overflow="fold")
    table.add_column("Type", style="magenta", width=4)
    table.add_column("Status", style="green")
    table.add_column("Name", style="white")
    table.add_column("Path", style="dim", overflow="fold")

    for asset in sorted(assets, key=lambda a: a["id"]):
        table.add_row(
            asset["id"],
            asset["type"],
            asset["status"],
            asset["name"],
            asset["path"],
        )

    console.print(table)


def cmd_info(args: argparse.Namespace) -> None:
    data = db.load_db()
    asset = data.get("assets", {}).get(args.asset_id)
    if not asset:
        print(f"Asset '{args.asset_id}' not found.")
        sys.exit(1)
    print(f"Asset: {asset['id']}")
    print(f"Show: {asset['show_code']}")
    print(f"Type: {asset['type']}")
    print(f"Name: {asset['name']}")
    print(f"Status: {asset['status']}")
    print(f"Path: {asset['path']}")
    if asset.get("tags"):
        print(f"Tags: {', '.join(sorted(asset['tags']))}")
    if asset.get("updated_at"):
        print(f"Updated: {asset['updated_at']}")


def cmd_status(args: argparse.Namespace) -> None:
    data = db.load_db()
    asset = data.get("assets", {}).get(args.asset_id)
    if not asset:
        print(f"Asset '{args.asset_id}' not found.")
        sys.exit(1)
    _ensure_status(args.status)
    asset["status"] = args.status
    asset["updated_at"] = datetime.utcnow().isoformat()
    db.save_db(data)
    print(f"Updated {args.asset_id} to status '{args.status}'.")


def cmd_delete(args: argparse.Namespace) -> None:
    data = db.load_db()
    asset = data.get("assets", {}).get(args.asset_id)
    if not asset:
        print(f"Asset '{args.asset_id}' not found.")
        sys.exit(1)
    del data["assets"][args.asset_id]
    # Drop tasks/versions for this asset
    data["tasks"] = {k: v for k, v in data.get("tasks", {}).items() if k != args.asset_id}
    data["versions"] = {
        k: v for k, v in data.get("versions", {}).items() if v.get("target_id") != args.asset_id
    }
    data["notes"] = [n for n in data.get("notes", []) if n.get("target_id") != args.asset_id]
    db.save_db(data)
    print(f"Deleted asset '{args.asset_id}' from DB (folders untouched).")


def cmd_rename(args: argparse.Namespace) -> None:
    data = db.load_db()
    asset = data.get("assets", {}).get(args.asset_id)
    if not asset:
        print(f"Asset '{args.asset_id}' not found.")
        sys.exit(1)
    asset["name"] = args.new_name
    asset["updated_at"] = datetime.utcnow().isoformat()
    db.save_db(data)
    print(f"Renamed asset '{args.asset_id}' to '{args.new_name}' (folders unchanged).")


def cmd_tag(args: argparse.Namespace) -> None:
    data = db.load_db()
    asset = data.get("assets", {}).get(args.asset_id)
    if not asset:
        print(f"Asset '{args.asset_id}' not found.")
        sys.exit(1)
    tags = set(asset.get("tags", []))
    tags.add(args.tag)
    asset["tags"] = sorted(tags)
    asset["updated_at"] = datetime.utcnow().isoformat()
    db.save_db(data)
    print(f"Tagged {args.asset_id} with '{args.tag}'.")


def cmd_untag(args: argparse.Namespace) -> None:
    data = db.load_db()
    asset = data.get("assets", {}).get(args.asset_id)
    if not asset:
        print(f"Asset '{args.asset_id}' not found.")
        sys.exit(1)
    tags = set(asset.get("tags", []))
    if args.tag in tags:
        tags.remove(args.tag)
    asset["tags"] = sorted(tags)
    asset["updated_at"] = datetime.utcnow().isoformat()
    db.save_db(data)
    print(f"Removed tag '{args.tag}' from {args.asset_id}.")


def cmd_find(args: argparse.Namespace) -> None:
    data = db.load_db()
    show_code = _resolve_show_code(args.show_code, data)
    assets = [
        a
        for a in data.get("assets", {}).values()
        if a.get("show_code") == show_code
    ]
    if args.name:
        q = args.name.lower()
        assets = [a for a in assets if q in a["name"].lower() or q in a["id"].lower()]
    if args.tag:
        assets = [a for a in assets if args.tag in a.get("tags", [])]
    if not assets:
        print("No assets found.")
        return
    for a in sorted(assets, key=lambda a: a.get("updated_at", ""))[::-1]:
        tag_str = f" tags={','.join(a.get('tags', []))}" if a.get("tags") else ""
        print(f"{a['id']} | {a['type']} | {a['status']} | {a['name']} | {a['path']}{tag_str}")


def cmd_recent(args: argparse.Namespace) -> None:
    data = db.load_db()
    assets = list(data.get("assets", {}).values())
    assets.sort(key=lambda a: a.get("updated_at", ""), reverse=True)
    if not assets:
        print("No assets found.")
        return
    for asset in assets[: args.limit]:
        print(f"{asset['id']} | {asset.get('updated_at','')} | {asset['status']} | {asset['name']}")


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.command == "add":
        cmd_add(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "info":
        cmd_info(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "delete":
        cmd_delete(args)
    elif args.command == "rename":
        cmd_rename(args)
    elif args.command == "tag":
        cmd_tag(args)
    elif args.command == "untag":
        cmd_untag(args)
    elif args.command == "find":
        cmd_find(args)
    elif args.command == "recent":
        cmd_recent(args)
    else:
        print("Unknown command")
        sys.exit(1)


if __name__ == "__main__":
    main()

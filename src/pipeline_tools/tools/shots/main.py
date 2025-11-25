import argparse
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

from pipeline_tools import SHOT_STATUS_VALUES
from pipeline_tools.core import db
from pipeline_tools.core.cli import FriendlyArgumentParser
from pipeline_tools.core.paths import make_show_root
from pipeline_tools.core.fs_utils import create_folders

DEFAULT_SHOT_STATUS = "not_started"


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


def _shot_id(show_code: str, code: str) -> str:
    base = code.upper()
    return f"{show_code}_{base}"


def _shot_path(show_root: Path, code: str) -> Path:
    return show_root / "04_SHOTS" / code.upper()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = FriendlyArgumentParser(description="Shot commands: add, list, info, status, delete, generate.")
    sub = parser.add_subparsers(dest="command", required=True)

    c_add = sub.add_parser("add", help="Add a shot.")
    c_add.add_argument("--show-code", "-c", help="Show code (defaults to current).")
    c_add.add_argument("code", help="Shot code, e.g. SH020.")
    c_add.add_argument("description", help="Shot description.")

    c_list = sub.add_parser("list", help="List shots for a show.")
    c_list.add_argument("--show-code", "-c", help="Show code (defaults to current).")
    c_list.add_argument("--status", choices=sorted(SHOT_STATUS_VALUES), help="Filter by status.")

    c_info = sub.add_parser("info", help="Shot details.")
    c_info.add_argument("shot_id", help="Shot ID, e.g. DMO_SH020")

    c_status = sub.add_parser("status", help="Update shot status.")
    c_status.add_argument("shot_id", help="Shot ID.")
    c_status.add_argument("status", choices=sorted(SHOT_STATUS_VALUES), help="New status.")

    c_delete = sub.add_parser("delete", help="Delete a shot from DB.")
    c_delete.add_argument("shot_id", help="Shot ID.")

    c_gen = sub.add_parser("generate_range", help="Create a range of shots.")
    c_gen.add_argument("--show-code", "-c", help="Show code (defaults to current).")
    c_gen.add_argument("start", type=int, help="Start number (e.g. 10 for SH010).")
    c_gen.add_argument("end", type=int, help="End number inclusive.")
    c_gen.add_argument(
        "--step", type=int, default=10, help="Step between shot numbers (default 10)."
    )

    return parser.parse_args(argv)


def cmd_add(args: argparse.Namespace) -> None:
    data = db.load_db()
    show_code = _resolve_show_code(args.show_code, data)
    show = _get_show_or_exit(show_code, data)
    shot_id = _shot_id(show_code, args.code)
    if shot_id in data.get("shots", {}):
        print(f"Shot '{shot_id}' already exists.")
        sys.exit(1)

    show_root = Path(show["root"])
    shot_path = _shot_path(show_root, args.code)
    rels = [
        shot_path.relative_to(show_root),
        shot_path.relative_to(show_root) / "workfiles",
        shot_path.relative_to(show_root) / "renders",
    ]
    create_folders(show_root, [str(r) for r in rels])
    now = datetime.utcnow().isoformat()
    data["shots"][shot_id] = {
        "id": shot_id,
        "code": args.code.upper(),
        "show_code": show_code,
        "description": args.description,
        "status": DEFAULT_SHOT_STATUS,
        "path": str(shot_path),
        "created_at": now,
        "updated_at": now,
    }
    db.save_db(data)
    print(f"Created shot {shot_id}")


def cmd_list(args: argparse.Namespace) -> None:
    data = db.load_db()
    show_code = _resolve_show_code(args.show_code, data)
    _get_show_or_exit(show_code, data)
    shots = [
        s for s in data.get("shots", {}).values() if s.get("show_code") == show_code
    ]
    if args.status:
        shots = [s for s in shots if s.get("status") == args.status]
    if not shots:
        print("No shots found.")
        return
    for shot in sorted(shots, key=lambda s: s["id"]):
        print(f"{shot['id']} | {shot['status']} | {shot['description']} | {shot['path']}")


def cmd_info(args: argparse.Namespace) -> None:
    data = db.load_db()
    shot = data.get("shots", {}).get(args.shot_id)
    if not shot:
        print(f"Shot '{args.shot_id}' not found.")
        sys.exit(1)
    print(f"Shot: {shot['id']}")
    print(f"Show: {shot['show_code']}")
    print(f"Status: {shot['status']}")
    print(f"Description: {shot['description']}")
    print(f"Path: {shot['path']}")


def cmd_status(args: argparse.Namespace) -> None:
    data = db.load_db()
    shot = data.get("shots", {}).get(args.shot_id)
    if not shot:
        print(f"Shot '{args.shot_id}' not found.")
        sys.exit(1)
    shot["status"] = args.status
    shot["updated_at"] = datetime.utcnow().isoformat()
    db.save_db(data)
    print(f"Updated {args.shot_id} to status '{args.status}'.")


def cmd_delete(args: argparse.Namespace) -> None:
    data = db.load_db()
    if args.shot_id not in data.get("shots", {}):
        print(f"Shot '{args.shot_id}' not found.")
        sys.exit(1)
    del data["shots"][args.shot_id]
    data["tasks"] = {k: v for k, v in data.get("tasks", {}).items() if k != args.shot_id}
    data["versions"] = {
        k: v for k, v in data.get("versions", {}).items() if v.get("target_id") != args.shot_id
    }
    data["notes"] = [n for n in data.get("notes", []) if n.get("target_id") != args.shot_id]
    db.save_db(data)
    print(f"Deleted shot '{args.shot_id}' from DB (folders untouched).")


def cmd_generate_range(args: argparse.Namespace) -> None:
    data = db.load_db()
    show_code = _resolve_show_code(args.show_code, data)
    show = _get_show_or_exit(show_code, data)
    show_root = Path(show["root"])
    created = []
    for num in range(args.start, args.end + 1, args.step):
        code = f"SH{num:03d}"
        shot_id = _shot_id(show_code, code)
        if shot_id in data.get("shots", {}):
            continue
        shot_path = _shot_path(show_root, code)
        rels = [
            shot_path.relative_to(show_root),
            shot_path.relative_to(show_root) / "workfiles",
            shot_path.relative_to(show_root) / "renders",
        ]
        create_folders(show_root, [str(r) for r in rels])
        now = datetime.utcnow().isoformat()
        data.setdefault("shots", {})[shot_id] = {
            "id": shot_id,
            "code": code,
            "show_code": show_code,
            "description": f"{code} auto-generated",
            "status": DEFAULT_SHOT_STATUS,
            "path": str(shot_path),
            "created_at": now,
            "updated_at": now,
        }
        created.append(shot_id)
    db.save_db(data)
    print(f"Created {len(created)} shots.")


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
    elif args.command == "generate_range":
        cmd_generate_range(args)
    else:
        print("Unknown command")
        sys.exit(1)


if __name__ == "__main__":
    main()

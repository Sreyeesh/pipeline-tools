import argparse
import sys
from datetime import datetime

from pipeline_tools.core import db
from pipeline_tools.core.cli import FriendlyArgumentParser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = FriendlyArgumentParser(description="Version commands.")
    sub = parser.add_subparsers(dest="command", required=True)

    c_new = sub.add_parser("new", help="Create a new version.")
    c_new.add_argument("target_id", help="Asset or shot ID.")
    c_new.add_argument("kind", help="Kind, e.g. design/model/rig/anim/comp.")

    c_list = sub.add_parser("list", help="List versions for a target.")
    c_list.add_argument("--asset", help="Asset ID.")
    c_list.add_argument("--shot", help="Shot ID.")

    c_latest = sub.add_parser("latest", help="Show latest version for a target/kind.")
    c_latest.add_argument("--asset", help="Asset ID.")
    c_latest.add_argument("--shot", help="Shot ID.")
    c_latest.add_argument("--kind", help="Filter by kind.")

    c_tag = sub.add_parser("tag", help="Tag a version.")
    c_tag.add_argument("version_id", help="Version ID.")
    c_tag.add_argument("tag", help="Tag to add.")

    c_delete = sub.add_parser("delete", help="Delete a version by ID.")
    c_delete.add_argument("version_id", help="Version ID to delete.")

    return parser.parse_args(argv)


def _resolve_target(asset: str | None, shot: str | None) -> str:
    if asset and shot:
        print("Pass only one of --asset or --shot.")
        sys.exit(1)
    if asset:
        return asset
    if shot:
        return shot
    print("Specify --asset or --shot.")
    sys.exit(1)


def _ensure_target(target_id: str, data: dict) -> dict:
    target = data.get("assets", {}).get(target_id) or data.get("shots", {}).get(target_id)
    if not target:
        print(f"Target '{target_id}' not found.")
        sys.exit(1)
    return target


def _next_version_id(data: dict, target_id: str, kind: str) -> str:
    existing = [
        v for v in data.get("versions", {}).values() if v.get("target_id") == target_id and v.get("kind") == kind
    ]
    if not existing:
        num = 1
    else:
        nums = []
        for v in existing:
            ver_str = v.get("version_id", "").split("_")[-1].lstrip("v")
            try:
                nums.append(int(ver_str))
            except ValueError:
                continue
        num = max(nums) + 1 if nums else 1
    return f"{target_id}_{kind}_v{num:03d}"


def cmd_new(args: argparse.Namespace) -> None:
    data = db.load_db()
    target = _ensure_target(args.target_id, data)
    version_id = _next_version_id(data, args.target_id, args.kind)
    now = datetime.utcnow().isoformat()
    data.setdefault("versions", {})[version_id] = {
        "version_id": version_id,
        "target_id": args.target_id,
        "kind": args.kind,
        "show_code": target.get("show_code"),
        "tags": [],
        "created_at": now,
        "updated_at": now,
    }
    db.save_db(data)
    print(f"Created version {version_id}")


def _list_for_target(target_id: str, data: dict, kind: str | None = None) -> list[dict]:
    versions = [
        v for v in data.get("versions", {}).values() if v.get("target_id") == target_id
    ]
    if kind:
        versions = [v for v in versions if v.get("kind") == kind]
    return sorted(versions, key=lambda v: v.get("version_id", ""))


def cmd_list(args: argparse.Namespace) -> None:
    data = db.load_db()
    target_id = _resolve_target(args.asset, args.shot)
    _ensure_target(target_id, data)
    versions = _list_for_target(target_id, data)
    if not versions:
        print("No versions found.")
        return
    for v in versions:
        tag_str = f" tags={','.join(v.get('tags', []))}" if v.get("tags") else ""
        print(f"{v['version_id']} | {v['kind']} | {v.get('created_at','')}{tag_str}")


def cmd_latest(args: argparse.Namespace) -> None:
    data = db.load_db()
    target_id = _resolve_target(args.asset, args.shot)
    _ensure_target(target_id, data)
    versions = _list_for_target(target_id, data, args.kind)
    if not versions:
        print("No versions found.")
        sys.exit(1)
    print(versions[-1]["version_id"])


def cmd_tag(args: argparse.Namespace) -> None:
    data = db.load_db()
    ver = data.get("versions", {}).get(args.version_id)
    if not ver:
        print(f"Version '{args.version_id}' not found.")
        sys.exit(1)
    tags = set(ver.get("tags", []))
    tags.add(args.tag)
    ver["tags"] = sorted(tags)
    ver["updated_at"] = datetime.utcnow().isoformat()
    db.save_db(data)
    print(f"Tagged {args.version_id} with '{args.tag}'.")


def cmd_delete(args: argparse.Namespace) -> None:
    data = db.load_db()
    if args.version_id not in data.get("versions", {}):
        print(f"Version '{args.version_id}' not found.")
        sys.exit(1)
    del data["versions"][args.version_id]
    db.save_db(data)
    print(f"Deleted version '{args.version_id}'.")


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.command == "new":
        cmd_new(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "latest":
        cmd_latest(args)
    elif args.command == "tag":
        cmd_tag(args)
    elif args.command == "delete":
        cmd_delete(args)
    else:
        print("Unknown command")
        sys.exit(1)


if __name__ == "__main__":
    main()

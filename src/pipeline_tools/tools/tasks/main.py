import argparse
import sys
from datetime import datetime

from pipeline_tools import TASK_STATUS_VALUES
from pipeline_tools.core import db
from pipeline_tools.core.cli import FriendlyArgumentParser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = FriendlyArgumentParser(description="Task commands for assets/shots.")
    sub = parser.add_subparsers(dest="command", required=True)

    c_add = sub.add_parser("add", help="Add a task to a target.")
    c_add.add_argument("target_id", help="Asset or shot ID.")
    c_add.add_argument("task_name", help="Task name, e.g. Model.")

    c_list = sub.add_parser("list", help="List tasks for a target.")
    c_list.add_argument("target_id", help="Asset or shot ID.")

    c_status = sub.add_parser("status", help="Update task status.")
    c_status.add_argument("target_id", help="Asset or shot ID.")
    c_status.add_argument("task_name", help="Task name.")
    c_status.add_argument("status", choices=sorted(TASK_STATUS_VALUES), help="Task status.")

    c_delete = sub.add_parser("delete", help="Delete a task from a target.")
    c_delete.add_argument("target_id", help="Asset or shot ID.")
    c_delete.add_argument("task_name", help="Task name.")

    return parser.parse_args(argv)


def _ensure_target_exists(target_id: str, data: dict) -> None:
    if target_id not in data.get("assets", {}) and target_id not in data.get("shots", {}):
        print(f"Target '{target_id}' not found in assets or shots.")
        sys.exit(1)


def cmd_add(args: argparse.Namespace) -> None:
    data = db.load_db()
    _ensure_target_exists(args.target_id, data)
    tasks = data.setdefault("tasks", {}).setdefault(args.target_id, [])
    if any(t["name"] == args.task_name for t in tasks):
        print(f"Task '{args.task_name}' already exists for {args.target_id}.")
        sys.exit(1)
    tasks.append(
        {"name": args.task_name, "status": "not_started", "updated_at": datetime.utcnow().isoformat()}
    )
    db.save_db(data)
    print(f"Added task '{args.task_name}' to {args.target_id}.")


def cmd_list(args: argparse.Namespace) -> None:
    data = db.load_db()
    _ensure_target_exists(args.target_id, data)
    tasks = data.get("tasks", {}).get(args.target_id, [])
    if not tasks:
        print("No tasks found.")
        return
    for t in tasks:
        print(f"{t['name']} | {t['status']} | {t.get('updated_at','')}")


def cmd_status(args: argparse.Namespace) -> None:
    data = db.load_db()
    _ensure_target_exists(args.target_id, data)
    tasks = data.get("tasks", {}).get(args.target_id, [])
    for t in tasks:
        if t["name"] == args.task_name:
            t["status"] = args.status
            t["updated_at"] = datetime.utcnow().isoformat()
            db.save_db(data)
            print(f"Updated {args.target_id}:{args.task_name} to {args.status}.")
            return
    print(f"Task '{args.task_name}' not found for {args.target_id}.")
    sys.exit(1)


def cmd_delete(args: argparse.Namespace) -> None:
    data = db.load_db()
    _ensure_target_exists(args.target_id, data)
    tasks = data.get("tasks", {}).get(args.target_id, [])
    new_tasks = [t for t in tasks if t["name"] != args.task_name]
    if len(new_tasks) == len(tasks):
        print(f"Task '{args.task_name}' not found for {args.target_id}.")
        sys.exit(1)
    if new_tasks:
        data["tasks"][args.target_id] = new_tasks
    else:
        data["tasks"].pop(args.target_id, None)
    db.save_db(data)
    print(f"Deleted task '{args.task_name}' from {args.target_id}.")


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.command == "add":
        cmd_add(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "delete":
        cmd_delete(args)
    else:
        print("Unknown command")
        sys.exit(1)


if __name__ == "__main__":
    main()

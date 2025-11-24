import argparse
import os
import sys
from pathlib import Path

from pipeline_tools.core import db
from pipeline_tools.core.cli import FriendlyArgumentParser
from pipeline_tools.core.paths import CREATIVE_ROOT, get_creative_root
from pipeline_tools.tools.project_creator.templates import TEMPLATES


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = FriendlyArgumentParser(description="Admin commands: config_show, config_set, doctor.")
    sub = parser.add_subparsers(dest="command", required=True)

    c_show = sub.add_parser("config_show", help="Show current config.")
    c_set = sub.add_parser("config_set", help="Set a config key/value in DB.")
    c_set.add_argument("key", help="Key to set (e.g. creative_root, db_path).")
    c_set.add_argument("value", help="Value to set.")

    sub.add_parser("doctor", help="Run a basic health check.")

    return parser.parse_args(argv)


def cmd_config_show() -> None:
    data = db.load_db()
    cfg = data.get("config", {})
    print(f"DB path: {db.get_db_path()}")
    print(f"Creative root (resolved): {get_creative_root()}")
    print(f"Creative root (default/fallback): {CREATIVE_ROOT}")
    for k, v in cfg.items():
        print(f"{k}: {v}")


def cmd_config_set(args: argparse.Namespace) -> None:
    data = db.load_db()
    data.setdefault("config", {})[args.key] = args.value
    db.save_db(data)
    print(f"Set config {args.key}={args.value}")


def cmd_doctor() -> None:
    ok = True
    db_path = db.get_db_path()
    db_dir = db_path.parent
    resolved_root = get_creative_root()
    try:
        data = db.load_db()
        db.save_db(data)
    except Exception as exc:  # pragma: no cover
        print(f"DB check failed: {exc}")
        ok = False
    if not CREATIVE_ROOT.exists():
        print(f"Creative root missing: {CREATIVE_ROOT}")
        ok = False
    if not db_dir.exists():
        print(f"DB parent folder missing and will be created: {db_dir}")
    elif not os.access(db_dir, os.W_OK):
        print(f"DB parent folder not writable: {db_dir}")
        ok = False
    if db_path.exists():
        print(f"DB OK at {db_path}")
    else:
        print(f"DB will be created at {db_path}")
    if resolved_root.exists():
        writable = os.access(resolved_root, os.W_OK)
        print(f"Creative root: {resolved_root} (writeable={bool(writable)})")
        if not writable:
            ok = False
    else:
        print(f"Creative root missing: {resolved_root}")
        ok = False
    print(f"PIPELINE_TOOLS_DB: {os.environ.get('PIPELINE_TOOLS_DB', '(default)')}")
    print(f"PIPELINE_TOOLS_ROOT: {os.environ.get('PIPELINE_TOOLS_ROOT', '(default)')}")
    print("Templates:", ", ".join(sorted(TEMPLATES.keys())))
    if ok:
        print("Doctor: OK")
    else:
        sys.exit(1)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.command == "config_show":
        cmd_config_show()
    elif args.command == "config_set":
        cmd_config_set(args)
    elif args.command == "doctor":
        cmd_doctor()
    else:
        print("Unknown command")
        sys.exit(1)


if __name__ == "__main__":
    main()

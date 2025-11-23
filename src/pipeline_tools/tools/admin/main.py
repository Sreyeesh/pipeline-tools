import argparse
import sys
from pathlib import Path

from pipeline_tools.core import db
from pipeline_tools.core.paths import CREATIVE_ROOT
from pipeline_tools.tools.project_creator.templates import TEMPLATES


class FriendlyArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(2, f"Error: {message}\nUse -h/--help for details.\n")


def parse_args() -> argparse.Namespace:
    parser = FriendlyArgumentParser(description="Admin commands: config_show, config_set, doctor.")
    sub = parser.add_subparsers(dest="command", required=True)

    c_show = sub.add_parser("config_show", help="Show current config.")
    c_set = sub.add_parser("config_set", help="Set a config key/value in DB.")
    c_set.add_argument("key", help="Key to set (e.g. creative_root, db_path).")
    c_set.add_argument("value", help="Value to set.")

    sub.add_parser("doctor", help="Run a basic health check.")

    return parser.parse_args()


def cmd_config_show() -> None:
    data = db.load_db()
    cfg = data.get("config", {})
    print(f"DB path: {db.get_db_path()}")
    print(f"Creative root (code): {CREATIVE_ROOT}")
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
    try:
        data = db.load_db()
        db.save_db(data)
    except Exception as exc:  # pragma: no cover
        print(f"DB check failed: {exc}")
        ok = False
    if not CREATIVE_ROOT.exists():
        print(f"Creative root missing: {CREATIVE_ROOT}")
        ok = False
    if db_path.exists():
        print(f"DB OK at {db_path}")
    else:
        print(f"DB will be created at {db_path}")
    print("Templates:", ", ".join(sorted(TEMPLATES.keys())))
    if ok:
        print("Doctor: OK")
    else:
        sys.exit(1)


def main() -> None:
    args = parse_args()
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

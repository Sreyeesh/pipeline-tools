import argparse
import json
import os
import sys
import time

from pipeline_tools.core import db, observability
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

    c_doc = sub.add_parser("doctor", help="Run a basic health check.")
    c_doc.add_argument("--json", action="store_true", help="Emit JSON output for automation.")

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


def _doctor_report() -> dict:
    report: dict[str, object] = {
        "status": "ok",
        "request_id": observability.get_request_id(),
        "checks": {},
        "env": {
            "PIPELINE_TOOLS_DB": os.environ.get("PIPELINE_TOOLS_DB"),
            "PIPELINE_TOOLS_ROOT": os.environ.get("PIPELINE_TOOLS_ROOT"),
            "PIPELINE_TOOLS_METRICS": os.environ.get("PIPELINE_TOOLS_METRICS"),
        },
        "templates": sorted(TEMPLATES.keys()),
    }
    ok = True

    db_path = db.get_db_path()
    db_dir = db_path.parent
    db_info = {
        "path": str(db_path),
        "parent": str(db_dir),
        "exists": db_path.exists(),
        "parent_exists": db_dir.exists(),
        "writable": os.access(db_dir, os.W_OK) if db_dir.exists() else None,
    }
    try:
        data = db.load_db()
        db.save_db(data)
        db_info["healthy"] = True
    except Exception as exc:  # pragma: no cover
        db_info["healthy"] = False
        db_info["error"] = str(exc)
        ok = False
    report["checks"]["db"] = db_info

    resolved_root = get_creative_root()
    root_info = {
        "resolved": str(resolved_root),
        "default": str(CREATIVE_ROOT),
        "exists": resolved_root.exists(),
        "writable": os.access(resolved_root, os.W_OK) if resolved_root.exists() else None,
    }
    if not resolved_root.exists() or not root_info["writable"]:
        ok = False
    report["checks"]["creative_root"] = root_info

    if not db_dir.exists():
        ok = False

    report["status"] = "ok" if ok else "error"
    return report


def _print_human_doctor(report: dict) -> None:
    db_info = report["checks"]["db"]
    root_info = report["checks"]["creative_root"]
    print(f"DB path: {db_info['path']}")
    if db_info["exists"]:
        print("DB exists and was readable/writable.")
    else:
        print("DB will be created on next run.")
    if not db_info.get("healthy", False):
        print(f"DB check failed: {db_info.get('error', 'unknown error')}")
    print(f"DB parent: {db_info['parent']} (exists={db_info['parent_exists']}, writable={db_info['writable']})")

    print(f"Creative root (resolved): {root_info['resolved']} (exists={root_info['exists']}, writable={root_info['writable']})")
    print(f"Creative root (default/fallback): {root_info['default']}")

    env = report["env"]
    print(f"PIPELINE_TOOLS_DB: {env.get('PIPELINE_TOOLS_DB') or '(default)'}")
    print(f"PIPELINE_TOOLS_ROOT: {env.get('PIPELINE_TOOLS_ROOT') or '(default)'}")
    print(f"PIPELINE_TOOLS_METRICS: {env.get('PIPELINE_TOOLS_METRICS') or '(disabled)'}")
    print("Templates:", ", ".join(report["templates"]))
    print(f"Doctor: {report['status'].upper()}")


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.command == "config_show":
        cmd_config_show()
    elif args.command == "config_set":
        cmd_config_set(args)
    elif args.command == "doctor":
        start = time.time()
        report = _doctor_report()
        duration_ms = (time.time() - start) * 1000
        observability.increment("doctor.run")
        observability.record_timing("doctor.duration_ms", duration_ms)
        observability.log_event(
            "doctor_run",
            status=report["status"],
            db_path=report["checks"]["db"]["path"],  # type: ignore[index]
            creative_root=report["checks"]["creative_root"]["resolved"],  # type: ignore[index]
            duration_ms=int(duration_ms),
        )
        if getattr(args, "json", False):
            print(json.dumps(report, indent=2))
        else:
            _print_human_doctor(report)
        if report["status"] != "ok":
            sys.exit(1)
    else:
        print("Unknown command")
        sys.exit(1)


if __name__ == "__main__":
    main()

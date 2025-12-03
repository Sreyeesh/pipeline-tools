import argparse
import json
import os
import sys
import time
import shutil
import subprocess
from pathlib import Path

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

    c_files = sub.add_parser("files", help="List or open admin files (01_ADMIN) for a show.")
    c_files.add_argument("-c", "--show-code", help="Show code (defaults to current show).")
    c_files.add_argument("filename", nargs="?", help="File name in 01_ADMIN to open.")
    c_files.add_argument("--open", action="store_true", help="Open the file instead of just listing.")

    c_add = sub.add_parser("add", help="Copy a file into 01_ADMIN for the current show.")
    c_add.add_argument("source", help="Source file to copy.")
    c_add.add_argument("--name", help="Optional destination name (default: keep source name).")
    c_add.add_argument("-c", "--show-code", help="Show code (defaults to current show).")

    c_template = sub.add_parser("template", help="Copy a bundled template into 01_ADMIN.")
    c_template.add_argument(
        "--template",
        "-t",
        default="animation_bible",
        choices=["animation_bible"],
        help="Template key to copy (default: animation_bible).",
    )
    c_template.add_argument(
        "--name",
        help="Destination name (default: <SHOWCODE>_animation_bible.md for animation_bible).",
    )
    c_template.add_argument("-c", "--show-code", help="Show code (defaults to current show).")

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


def _open_file(path: Path) -> None:
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)
    try:
        if sys.platform.startswith("darwin"):
            subprocess.run(["open", str(path)], check=True)
        elif os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
        else:
            subprocess.run(["xdg-open", str(path)], check=True)
    except Exception as exc:  # pragma: no cover
        print(f"Failed to open file: {exc}")
        sys.exit(1)


def _load_show(show_code: str | None) -> dict:
    data = db.load_db()
    code = show_code or data.get("current_show")
    if not code:
        print("No show specified and no current show is set. Use --show-code or set a current show.")
        sys.exit(1)
    show = data.get("shows", {}).get(code)
    if not show:
        print(f"Show '{code}' not found in DB.")
        sys.exit(1)
    return show


def cmd_files(args: argparse.Namespace) -> None:
    show = _load_show(args.show_code)

    admin_dir = Path(show["root"]) / "01_ADMIN"
    if not admin_dir.exists():
        print(f"Admin folder not found: {admin_dir}")
        sys.exit(1)

    files = sorted([p for p in admin_dir.iterdir() if p.is_file()])
    if not args.filename:
        if not files:
            print("No files found in 01_ADMIN.")
            return
        for f in files:
            size_kb = f.stat().st_size / 1024
            print(f"{f.name} ({size_kb:.1f} KB)")
        return

    target = admin_dir / args.filename
    if not args.open:
        if target.exists():
            print(target)
        else:
            print(f"File not found: {target}")
            sys.exit(1)
    else:
        _open_file(target)


def cmd_add(args: argparse.Namespace) -> None:
    show = _load_show(args.show_code)
    admin_dir = Path(show["root"]) / "01_ADMIN"
    admin_dir.mkdir(parents=True, exist_ok=True)

    source = Path(args.source)
    if not source.exists():
        print(f"Source file not found: {source}")
        sys.exit(1)

    dest_name = args.name or source.name
    dest = admin_dir / dest_name
    shutil.copy2(source, dest)
    print(f"Copied to: {dest}")


def _template_source_path(template_key: str) -> Path:
    if template_key == "animation_bible":
        base = Path(__file__).resolve().parent.parent / "project_creator" / "reference" / "animation_short" / "01_ADMIN"
        return base / "animation_bible_template.md"
    raise ValueError(f"Unknown template '{template_key}'")


def cmd_template(args: argparse.Namespace) -> None:
    show = _load_show(args.show_code)
    admin_dir = Path(show["root"]) / "01_ADMIN"
    admin_dir.mkdir(parents=True, exist_ok=True)

    src = _template_source_path(args.template)
    if not src.exists():
        print(f"Template file missing: {src}")
        sys.exit(1)

    dest_name = args.name or f"{show['code']}_animation_bible.md" if args.template == "animation_bible" else src.name
    dest = admin_dir / dest_name
    shutil.copy2(src, dest)
    print(f"Copied template to: {dest}")


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
    elif args.command == "files":
        cmd_files(args)
    elif args.command == "add":
        cmd_add(args)
    elif args.command == "template":
        cmd_template(args)
    else:
        print("Unknown command")
        sys.exit(1)


if __name__ == "__main__":
    main()

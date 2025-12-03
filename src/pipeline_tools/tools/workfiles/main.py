import argparse
import os
import sys
from pathlib import Path
from typing import Iterable

from pipeline_tools.core import db
from pipeline_tools.core.cli import FriendlyArgumentParser
from pipeline_tools.tools.dcc_launcher import launcher as dcc_launcher


KIND_EXTENSIONS = {
    "krita": "kra",
    "blender": "blend",
    "pureref": "pur",
    "photoshop": "psd",
    "aftereffects": "aep",
    "image": "png",
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = FriendlyArgumentParser(description="Manage workfiles for assets and shots.")
    sub = parser.add_subparsers(dest="command", required=True)

    c_add = sub.add_parser("add", help="Create a new workfile for an asset or shot.")
    c_add.add_argument("target_id", help="Asset or shot id (e.g., PKU_CH_Poku_Main or PKU_SH010).")
    c_add.add_argument("--kind", "-k", required=True, help="DCC/work type (krita, blender, pureref, etc.).")
    c_add.add_argument("--name", help="Optional custom base name (default: <target_id>_<kind>).")
    c_add.add_argument("--ext", help="Override file extension (default from kind).")
    c_add.add_argument("--show-code", "-c", help="Show code (defaults to derived prefix or current show).")
    c_add.add_argument("--open", action="store_true", help="Open the created file in the matching DCC.")

    c_list = sub.add_parser("list", help="List workfiles for a target or show.")
    c_list.add_argument("--target-id", help="Asset or shot id to filter.")
    c_list.add_argument("--show-code", "-c", help="Show code (defaults to current show).")

    c_open = sub.add_parser("open", help="Open an existing workfile.")
    c_open.add_argument("--target-id", help="Asset or shot id (use latest file).")
    c_open.add_argument("--kind", "-k", help="Kind to filter (krita, blender, etc.).")
    c_open.add_argument("--file", "-f", help="Explicit file path to open.")
    c_open.add_argument("--show-code", "-c", help="Show code (defaults to derived prefix or current show).")

    return parser.parse_args(argv)


def _load_db_show(show_code: str | None) -> dict:
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


def _infer_show_code(target_id: str) -> str | None:
    parts = target_id.split("_", 1)
    return parts[0] if parts else None


def _bucket(target_id: str) -> str:
    if "_SH" in target_id:
        return "shots"
    return "assets"


def _work_root(show_root: Path) -> Path:
    root = show_root / "05_WORK"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _target_dir(show_root: Path, target_id: str, kind: str | None = None) -> Path:
    base = _work_root(show_root) / _bucket(target_id) / target_id
    if kind:
        base = base / kind
    base.mkdir(parents=True, exist_ok=True)
    return base


def _next_version_path(base_dir: Path, base_name: str, ext: str) -> Path:
    existing = list(base_dir.glob(f"{base_name}_w*.{ext}"))
    max_ver = 0
    for path in existing:
        stem = path.stem
        if "_w" in stem:
            try:
                ver = int(stem.split("_w")[-1])
                max_ver = max(max_ver, ver)
            except ValueError:
                continue
    return base_dir / f"{base_name}_w{max_ver + 1:03d}.{ext}"


def _create_placeholder(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(b"")  # simple placeholder


def _open_workfile(path: Path, kind: str | None = None) -> None:
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)
    dcc_kind = (kind or "").lower()
    try:
        if dcc_kind in dcc_launcher.DCC_PATHS:
            dcc_launcher.launch_dcc(dcc_kind, file_path=str(path), project_root=str(path.parent))
        else:
            from pipeline_tools.tools.admin.main import _open_file  # reuse helper
            _open_file(path)
    except Exception as exc:  # pragma: no cover
        print(f"Failed to open workfile: {exc}")
        sys.exit(1)


def cmd_add(args: argparse.Namespace) -> None:
    show_code = args.show_code or _infer_show_code(args.target_id)
    show = _load_db_show(show_code)
    show_root = Path(show["root"])

    kind = args.kind.lower()
    ext = (args.ext or KIND_EXTENSIONS.get(kind) or "work").lstrip(".")
    base_name = args.name or f"{args.target_id}_{kind}"

    target_dir = _target_dir(show_root, args.target_id, kind)
    path = _next_version_path(target_dir, base_name, ext)
    _create_placeholder(path)
    print(f"Created workfile: {path}")

    if args.open:
        _open_workfile(path, kind)


def _iter_workfiles(base: Path) -> Iterable[Path]:
    if not base.exists():
        return []
    return sorted([p for p in base.rglob("*") if p.is_file()])


def _version_number(path: Path) -> int:
    stem = path.stem
    if "_w" in stem:
        try:
            return int(stem.split("_w")[-1])
        except ValueError:
            return 0
    return 0


def cmd_list(args: argparse.Namespace) -> None:
    show_code = args.show_code
    target_id = args.target_id

    if target_id:
        show_code = show_code or _infer_show_code(target_id)

    show = _load_db_show(show_code)
    show_root = Path(show["root"])

    if target_id:
        base = _target_dir(show_root, target_id)
        files = _iter_workfiles(base)
        if not files:
            print("No workfiles found.")
            return
        for f in files:
            print(f.relative_to(show_root))
    else:
        base = _work_root(show_root)
        files = _iter_workfiles(base)
        if not files:
            print("No workfiles found.")
            return
        for f in files:
            print(f.relative_to(show_root))


def cmd_open(args: argparse.Namespace) -> None:
    if not args.file and not args.target_id:
        print("Provide --file or --target-id to open.")
        sys.exit(1)

    if args.file:
        path = Path(args.file)
        kind = args.kind
        if not kind and path.suffix:
            ext = path.suffix.lstrip(".")
            kind = next((k for k, v in KIND_EXTENSIONS.items() if v == ext), None)
        _open_workfile(path, kind)
        return

    target_id = args.target_id
    show_code = args.show_code or _infer_show_code(target_id)
    show = _load_db_show(show_code)
    show_root = Path(show["root"])
    kind = args.kind.lower() if args.kind else None

    base = _target_dir(show_root, target_id, kind)
    candidates = list(_iter_workfiles(base))
    if not candidates:
        print(f"No workfiles found for {target_id}.")
        sys.exit(1)

    candidates.sort(key=lambda p: (_version_number(p), p.stat().st_mtime), reverse=True)
    path = candidates[0]
    _open_workfile(path, kind)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.command == "add":
        cmd_add(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "open":
        cmd_open(args)
    else:
        print("Unknown command")
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

import argparse
import os
import sys
import subprocess
import shutil
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
    "fountain": "fountain",
    "markdown": "md",
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

    c_export = sub.add_parser("export", help="Export a workfile (currently Fountain -> PDF).")
    c_export.add_argument("--file", "-f", required=True, help="Path to the source workfile (Fountain).")
    c_export.add_argument("--out", "-o", help="Destination PDF path (default: alongside source).")

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


def _work_root(show_root: Path, create: bool = True) -> Path:
    root = show_root / "05_WORK"
    if create:
        root.mkdir(parents=True, exist_ok=True)
    return root


def _target_dir(show_root: Path, target_id: str, kind: str | None = None, create: bool = True) -> Path:
    base = _work_root(show_root, create=create) / _bucket(target_id) / target_id
    if kind:
        base = base / kind
    if create:
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
    if path.suffix == ".blend":
        _create_blender_file(path)
        return
    if path.suffix == ".kra":
        _create_krita_file(path)
        return
    if not path.exists():
        path.write_bytes(b"")  # simple placeholder


def _create_krita_file(path: Path) -> None:
    """Create a valid Krita file manually (it's a ZIP archive with specific structure)."""
    import zipfile
    import base64

    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Create a minimal valid .kra file (which is a ZIP archive)
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_STORED) as kra:
            # Create mimetype (must be first and uncompressed)
            kra.writestr('mimetype', 'application/x-kra', compress_type=zipfile.ZIP_STORED)

            # Create minimal maindoc.xml
            maindoc = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE DOC PUBLIC '-//KDE//DTD krita 2.0//EN' 'http://www.calligra.org/DTD/krita-2.0.dtd'>
<DOC xmlns="http://www.calligra.org/DTD/krita" syntaxVersion="2" editor="Krita" kritaVersion="5.0">
 <IMAGE name="Untitled" mime="application/x-kra" width="1920" height="1080" colorspace-name="RGBA" profile="sRGB-elle-V2-srgbtrc.icc" description="" x-res="300" y-res="300">
  <layers>
   <layer name="Background" opacity="255" visible="1" locked="0" uuid="{00000000-0000-0000-0000-000000000001}" nodetype="paintlayer" colorlabel="0" collapsed="0" filename="layer1" colorspace="RGBA" channelflags="" channellockflags=""/>
  </layers>
 </IMAGE>
</DOC>
'''
            kra.writestr('maindoc.xml', maindoc)

            # Create minimal documentinfo.xml
            docinfo = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE document-info PUBLIC '-//KDE//DTD document-info 1.1//EN' 'http://www.calligra.org/DTD/document-info-1.1.dtd'>
<document-info xmlns="http://www.calligra.org/DTD/document-info">
 <about>
  <title>Untitled</title>
 </about>
</document-info>
'''
            kra.writestr('documentinfo.xml', docinfo)

            # Create minimal preview.png (1x1 transparent PNG)
            tiny_png = base64.b64decode(
                'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
            )
            kra.writestr('preview.png', tiny_png)

            # Create proper layer data in Untitled/layers/
            # 1920x1080 RGBA = 1920 * 1080 * 4 = 8,294,400 bytes of transparent pixels
            layer_data = b'\x00' * (1920 * 1080 * 4)
            kra.writestr('Untitled/layers/layer1', layer_data)

            # Create a minimal sRGB ICC profile
            # This is a simplified sRGB v2 profile
            srgb_profile = base64.b64decode(
                'AAACLEFEQkUCEAAAbW50clJHQiBYWVogB9YAAQABAAAAAAABAABhY3NwAAAAAAAAAAAAAAAAAAAA'
                'AAAAAAAAAAAAAQAA9tYAAQAAAADTLQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
                'AAAAAAAAAAAAAAAAAAAALY3BydAAAAQAAAAA0ZGVzYwAAAWAAAAAAdGV4dAAAAABDb3B5cmlnaH'
                'Qgc1JHQiBJRUM2MTk2Ni0yLjEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
                'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
            )
            kra.writestr('Untitled/layers/layer1.icc', srgb_profile)

    except Exception as exc:
        print(f"[warning] Could not create Krita file at {path.name}: {exc}")


def _create_blender_file(path: Path) -> None:
    """Create a valid Blender file using Blender in background if available."""
    exe = dcc_launcher.get_dcc_executable("blender")
    if not exe:
        # Fallback: avoid writing an invalid .blend; leave absent
        print(f"[warning] Blender not found; skipping creation of {path.name}. Open Blender and save to this path.")
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    # Convert path to string and escape backslashes for Python expression
    path_str = str(path).replace("\\", "\\\\")
    parent_str = str(path.parent).replace("\\", "\\\\")

    cmd = [
        exe,
        "--background",
        "--factory-startup",
        "--python-expr",
        (
            "import bpy, os; "
            f"os.makedirs(r'{parent_str}', exist_ok=True); "
            "bpy.ops.wm.read_factory_settings(use_empty=True); "
            f"bpy.ops.wm.save_as_mainfile(filepath=r'{path_str}')"
        ),
    ]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:  # pragma: no cover
        print(f"[warning] Could not create Blender file at {path.name}")
        print(f"[warning] Blender error: {exc.stderr if exc.stderr else exc}")
    except Exception as exc:  # pragma: no cover
        print(f"[warning] Could not create Blender file at {path}: {exc}")


def _open_workfile(path: Path, kind: str | None = None) -> None:
    dcc_kind = (kind or "").lower()
    if not path.exists() and dcc_kind == "blender":
        # Try to create a valid .blend on the fly
        _create_blender_file(path)
    if not path.exists() and dcc_kind == "krita":
        # Try to create a valid .kra on the fly
        _create_krita_file(path)
    if not path.exists():
        if dcc_kind == "blender":
            # Fallback: open Blender with target file path set for auto-save
            project_root = None
            try:
                project_root = path.parents[4]
            except IndexError:
                project_root = path.parent
            try:
                dcc_launcher.launch_dcc("blender", project_root=str(project_root), target_file_path=str(path))
                print(f"[info] Opening Blender with target file: {path.name}")
                print(f"[info] Press Ctrl+S in Blender to save to this file.")
                return
            except Exception:
                pass
        if dcc_kind == "krita":
            # Fallback: open Krita with target file path set for auto-save
            project_root = None
            try:
                project_root = path.parents[4]
            except IndexError:
                project_root = path.parent
            try:
                dcc_launcher.launch_dcc("krita", project_root=str(project_root), target_file_path=str(path))
                print(f"[info] Opening Krita with target file: {path.name}")
                print(f"[info] Press Ctrl+S in Krita to save to this file.")
                return
            except Exception:
                pass
        print(f"File not found: {path}")
        sys.exit(1)
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


def _export_fountain(src: Path, dst: Path) -> None:
    if not src.exists():
        print(f"File not found: {src}")
        sys.exit(1)
    dst.parent.mkdir(parents=True, exist_ok=True)

    # Prefer afterwriting (Node), fallback to screenplain if installed
    afterwriting = shutil.which("afterwriting")
    screenplain = shutil.which("screenplain")

    if afterwriting:
        cmd = [afterwriting, "convert", "--source", str(src), "--pdf", str(dst)]
        try:
            subprocess.run(cmd, check=True)
            print(f"Exported PDF: {dst}")
            return
        except subprocess.CalledProcessError as exc:
            print(f"Export failed with command: {' '.join(cmd)}")
            print(exc)
            sys.exit(exc.returncode or 1)

    if screenplain:
        try:
            import reportlab  # type: ignore # noqa: F401
        except ImportError:
            print("screenplain is installed but missing dependency 'reportlab'. Install it with: pip install reportlab")
            sys.exit(1)
        # screenplain writes to stdout; pipe to the target PDF and force format
        cmd = [screenplain, "--format", "pdf", str(src)]
        try:
            with dst.open("wb") as fh:
                subprocess.run(cmd, check=True, stdout=fh)
            print(f"Exported PDF: {dst}")
            return
        except subprocess.CalledProcessError as exc:
            print(f"Export failed with command: {' '.join(cmd)}")
            print(exc)
            sys.exit(exc.returncode or 1)

    print("No exporter found. Install 'afterwriting' (npm) or 'screenplain' (pip).")
    sys.exit(1)


def cmd_export(args: argparse.Namespace) -> None:
    src = Path(args.file)
    if not args.out:
        dst = src.with_suffix(".pdf")
    else:
        dst = Path(args.out)
        if dst.is_dir():
            dst = dst / (src.stem + ".pdf")
    _export_fountain(src, dst)


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
        base = _target_dir(show_root, target_id, create=False)
        if not base.exists():
            print("No workfiles found.")
            return
        files = _iter_workfiles(base)
        if not files:
            print("No workfiles found.")
            return
        for f in files:
            print(f.relative_to(show_root))
    else:
        base = _work_root(show_root, create=False)
        if not base.exists():
            print("No workfiles found.")
            return
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

    base = _target_dir(show_root, target_id, kind, create=False)
    if not base.exists():
        print(f"No workfiles found for {target_id}.")
        sys.exit(1)

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
    elif args.command == "export":
        cmd_export(args)
    else:
        print("Unknown command")
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

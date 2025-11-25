import argparse
import sys
from pathlib import Path

from pipeline_tools.core.cli import FriendlyArgumentParser
from pipeline_tools.core.paths import make_show_root
from pipeline_tools.core.fs_utils import create_folders
from .templates import TEMPLATES


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = FriendlyArgumentParser(
        description=(
            "Create project folder structures from templates.\n"
            "Example: -c DMO -n \"Demo Short 30s\" -t animation_short"
        )
    )
    parser.add_argument(
        "--template",
        "-t",
        default="animation_short",
        help=(
            "Folder template key to use. Available: "
            f"{', '.join(sorted(TEMPLATES.keys()))} (default: animation_short)"
        ),
    )
    parser.add_argument(
        "--show-code",
        "-c",
        required=False,
        help="Short show code (e.g. DMO). Used in the root folder name.",
    )
    parser.add_argument(
        "--name",
        "-n",
        required=False,
        help='Project title (e.g. "Demo Short 30s"). Used in the root folder name.',
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Prompt for missing values, preview the folder tree, and confirm before creating.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the target path and folders without creating anything.",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompts (useful for non-interactive runs).",
    )
    return parser.parse_args(argv)


def _prompt(prompt_text: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        resp = input(f"{prompt_text}{suffix}: ").strip()
        if not resp and default is not None:
            resp = default
        if resp:
            return resp
        print("Please enter a value.")


def _pick_template(current: str | None = None) -> str:
    default = current or "animation_short"
    available = sorted(TEMPLATES.keys())
    print("Available templates:")
    for key in available:
        print(f"- {key}")
    while True:
        choice = _prompt("Template key", default)
        if choice in TEMPLATES:
            return choice
        print(f"Unknown template '{choice}'. Choose one from: {', '.join(available)}")


def _preview_tree(show_root: Path, rel_paths: list[str], limit: int = 30) -> None:
    print(f"\nTarget path: {show_root}")
    print("Folders to create:")
    for rel in rel_paths[:limit]:
        print(f"- {show_root / rel}")
    if len(rel_paths) > limit:
        remaining = len(rel_paths) - limit
        print(f"... and {remaining} more")
    print()


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    template_key = args.template or "animation_short"
    show_code = args.show_code
    project_name = args.name

    if args.interactive:
        show_code = show_code or _prompt("Show code (e.g. DMO)")
        project_name = project_name or _prompt('Project name (e.g. "Demo Short 30s")')
        template_key = _pick_template(template_key)
    else:
        if not show_code or not project_name:
            print("Error: --show-code and --name are required (or use --interactive).")
            sys.exit(2)

    if template_key not in TEMPLATES:
        available = ", ".join(sorted(TEMPLATES.keys()))
        print(f"Unknown template '{template_key}'. Available templates: {available}")
        sys.exit(1)

    rel_paths = TEMPLATES[template_key]

    show_root: Path = make_show_root(show_code, project_name, template_key=template_key)

    if show_root.exists():
        print(
            f"Project folder already exists: {show_root}\n"
            "Cowardly refusing to overwrite. Choose a different show code/name or "
            "remove the existing folder."
        )
        sys.exit(1)

    if args.dry_run:
        _preview_tree(show_root, rel_paths)
        print("Dry run complete; nothing was created.")
        return

    if args.interactive and not args.yes:
        _preview_tree(show_root, rel_paths)
        proceed = input("Create these folders? [y/N]: ").strip().lower()
        if proceed not in {"y", "yes"}:
            print("Aborted.")
            return

    print(f"Creating project at: {show_root}")
    create_folders(show_root, rel_paths)
    print("Done.")


if __name__ == "__main__":
    main()

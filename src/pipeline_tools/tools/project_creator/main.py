import argparse
import sys
from pathlib import Path

from pipeline_tools.core.paths import make_show_root
from pipeline_tools.core.fs_utils import create_folders
from .templates import TEMPLATES


class FriendlyArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        """Print cleaner errors that point users to help."""
        self.print_usage(sys.stderr)
        self.exit(2, f"Error: {message}\nUse -h/--help for details.\n")


def parse_args() -> argparse.Namespace:
    parser = FriendlyArgumentParser(
        description=(
            "Create project folder structures from templates.\n"
            "Example: -c PKS -n \"Poku Short 30s\" -t animation_short"
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
        required=True,
        help="Short show code (e.g. PKS). Used in the root folder name.",
    )
    parser.add_argument(
        "--name",
        "-n",
        required=True,
        help='Project title (e.g. "Poku Short 30s"). Used in the root folder name.',
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    template_key = args.template
    show_code = args.show_code
    project_name = args.name

    if template_key not in TEMPLATES:
        available = ", ".join(sorted(TEMPLATES.keys()))
        print(f"Unknown template '{template_key}'. Available templates: {available}")
        sys.exit(1)

    rel_paths = TEMPLATES[template_key]

    show_root: Path = make_show_root(show_code, project_name)

    if show_root.exists():
        print(
            f"Project folder already exists: {show_root}\n"
            "Cowardly refusing to overwrite. Choose a different show code/name or "
            "remove the existing folder."
        )
        sys.exit(1)

    print(f"Creating project at: {show_root}")
    create_folders(show_root, rel_paths)
    print("Done.")


if __name__ == "__main__":
    main()

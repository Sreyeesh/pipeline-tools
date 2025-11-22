import argparse
from pathlib import Path

from pipeline_tools.core.paths import make_show_root
from pipeline_tools.core.fs_utils import create_folders
from .templates import TEMPLATES


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create project folder structures from templates."
    )
    parser.add_argument(
        "--template",
        "-t",
        choices=TEMPLATES.keys(),
        default="animation_short",
        help="Template to use (default: animation_short)",
    )
    parser.add_argument(
        "--show-code",
        "-c",
        required=True,
        help="Show code, e.g. PKS",
    )
    parser.add_argument(
        "--name",
        "-n",
        required=True,
        help='Project name, e.g. "Poku Short 30s"',
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    template_key = args.template
    show_code = args.show_code
    project_name = args.name

    rel_paths = TEMPLATES[template_key]

    show_root: Path = make_show_root(show_code, project_name)

    print(f"Creating project at: {show_root}")
    create_folders(show_root, rel_paths)
    print("Done.")


if __name__ == "__main__":
    main()

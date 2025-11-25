import argparse
import sys
from pathlib import Path

from pipeline_tools.core import paths
from pipeline_tools.core.cli import FriendlyArgumentParser
from pipeline_tools.core.fs_utils import create_folders

LOCATIONS = {
    "assets": Path("03_ASSETS/characters"),
    "prepro": Path("02_PREPRO/designs/characters"),
}
DEFAULT_LOCATION = "assets"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = FriendlyArgumentParser(
        description=(
            "Create a character thumbnails folder inside a project.\n"
            "Example: -c DMO -n \"Demo Short 30s\" --character courierA"
        )
    )
    parser.add_argument(
        "--show-code",
        "-c",
        required=True,
        help="Short show code (e.g. DMO). Used in the root folder name.",
    )
    parser.add_argument(
        "--name",
        "-n",
        required=True,
        help='Project title (e.g. "Demo Short 30s"). Used in the root folder name.',
    )
    parser.add_argument(
        "--character",
        required=True,
        help="Character identifier (e.g. courierA). Used for the folder name.",
    )
    parser.add_argument(
        "--location",
        "-l",
        choices=sorted(LOCATIONS.keys()),
        default=DEFAULT_LOCATION,
        help=(
            "Where to place the thumbnails folder: assets or prepro "
            f"(default: {DEFAULT_LOCATION})."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    show_root: Path = paths.make_show_root(args.show_code, args.name)
    rel_base = LOCATIONS[args.location]
    rel_path = rel_base / args.character / "thumbnails"

    target = show_root / rel_path

    print(f"Creating character thumbnails folder at: {target}")
    create_folders(show_root, [str(rel_path)])
    print("Done.")


if __name__ == "__main__":
    main()

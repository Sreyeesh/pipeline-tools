"""
Primary entrypoint for artist-friendly commands.

Shortcuts into existing tool modules with a single command.
"""
from __future__ import annotations

import argparse
import sys
from textwrap import dedent

from pipeline_tools.tools.admin import main as admin_main
from pipeline_tools.tools.project_creator import main as project_creator_main


class FriendlyArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(2, f"Error: {message}\nUse -h/--help for details.\n")


EXAMPLES = dedent(
    """
    Common commands:
      pipeline-tools create -c PKS -n "Poku Short 30s"
      pipeline-tools create --interactive
      pipeline-tools create -c PKS -n "Poku Short 30s" -t animation_short --dry-run
      pipeline-tools doctor
      pipeline-tools doctor && pipeline-tools create --interactive
    """
).strip()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = FriendlyArgumentParser(description="Pipeline tools launcher.")
    parser.add_argument(
        "--examples",
        action="store_true",
        help="Print common commands and exit.",
    )

    sub = parser.add_subparsers(dest="command", required=False)

    create = sub.add_parser("create", help="Create a project folder tree (wrapper over project_creator).")
    create.add_argument("-c", "--show-code", help="Show code, e.g. PKS.")
    create.add_argument("-n", "--name", help='Project name, e.g. "Poku Short 30s".')
    create.add_argument("-t", "--template", help="Template key (see templates list).")
    create.add_argument("-i", "--interactive", action="store_true", help="Prompt for missing values.")
    create.add_argument("--dry-run", action="store_true", help="Preview without creating.")
    create.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompts.")

    sub.add_parser("doctor", help="Run environment checks.")
    sub.add_parser("examples", help="Show common commands.")

    return parser.parse_args(argv)


def run_examples() -> None:
    print(EXAMPLES)


def run_create(args: argparse.Namespace) -> None:
    argv: list[str] = []
    if args.show_code:
        argv.extend(["-c", args.show_code])
    if args.name:
        argv.extend(["-n", args.name])
    if args.template:
        argv.extend(["-t", args.template])
    if args.interactive:
        argv.append("--interactive")
    if args.dry_run:
        argv.append("--dry-run")
    if args.yes:
        argv.append("--yes")
    project_creator_main.main(argv)


def run_doctor() -> None:
    admin_main.main(["admin", "doctor"])


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    if args.examples or args.command == "examples":
        run_examples()
        return
    if args.command == "create":
        run_create(args)
        return
    if args.command == "doctor":
        run_doctor()
        return

    # No subcommand defaults to examples to keep things friendly.
    run_examples()


if __name__ == "__main__":
    main()

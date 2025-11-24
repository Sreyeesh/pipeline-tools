from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Callable, Mapping, Sequence


class FriendlyArgumentParser(argparse.ArgumentParser):
    """ArgumentParser that prints concise, user-friendly errors."""

    def error(self, message: str) -> None:  # pragma: no cover - thin wrapper
        self.print_usage(sys.stderr)
        self.exit(2, f"Error: {message}\nUse -h/--help for details.\n")


Runner = Callable[[Sequence[str] | None], None]


@dataclass(frozen=True)
class CommandSpec:
    """Lightweight description of a CLI command and how to run it."""

    name: str
    help: str
    runner: Runner


CommandMap = Mapping[str, CommandSpec]

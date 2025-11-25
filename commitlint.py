#!/usr/bin/env python3
"""
Simple conventional commit checker for git hooks and CI.

Usage:
  # Check commits in a range (CI)
  python commitlint.py range <base> <head>

  # Commit-msg hook
  python commitlint.py hook .git/COMMIT_EDITMSG
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from typing import Iterable, Tuple


CONVENTIONAL_RE = re.compile(
    r"^(build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test)(\([^)]+\))?: .+"
)
ALLOWED_PREFIXES = ("Merge ",)


def is_conventional(message: str) -> bool:
    message = message.strip()
    if not message:
        return False
    if message.startswith(ALLOWED_PREFIXES):
        return True
    return bool(CONVENTIONAL_RE.match(message))


def _run_git(args):
    return subprocess.check_output(["git", *args], text=True).strip()


def commits_in_range(base: str, head: str) -> Iterable[Tuple[str, str]]:
    fmt = "%H:::%s"
    log_range = f"{base}..{head}"
    output = _run_git(["log", "--format=" + fmt, log_range])
    for line in output.splitlines():
        sha, _, subject = line.partition(":::")
        yield sha, subject


def check_commits(base: str, head: str) -> int:
    failures = []
    for sha, subject in commits_in_range(base, head):
        if not is_conventional(subject):
            failures.append((sha, subject))
    if failures:
        print("Conventional commit check failed for the following commits:")
        for sha, subject in failures:
            print(f"- {sha[:7]}: {subject}")
        print("\nExpected format: type(scope?): short description")
        print("Allowed types: build, chore, ci, docs, feat, fix, perf, refactor, revert, style, test")
        return 1
    return 0


def check_hook_file(path: str) -> int:
    with open(path, "r", encoding="utf-8") as fh:
        subject = fh.readline().strip()
    if is_conventional(subject):
        return 0
    print("Conventional commit check failed for commit message:")
    print(subject)
    print("\nExpected format: type(scope?): short description")
    print("Allowed types: build, chore, ci, docs, feat, fix, perf, refactor, revert, style, test")
    return 1


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Conventional commit checker.")
    sub = parser.add_subparsers(dest="mode", required=True)

    hook = sub.add_parser("hook", help="Check a commit-msg hook file")
    hook.add_argument("path", help="Path to commit message file")

    rng = sub.add_parser("range", help="Check commits in a git range")
    rng.add_argument("base", help="Base commit (exclusive)")
    rng.add_argument("head", help="Head commit (inclusive)")

    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    if args.mode == "hook":
        return check_hook_file(args.path)
    if args.mode == "range":
        return check_commits(args.base, args.head)
    print("Unknown mode")
    return 1


if __name__ == "__main__":
    sys.exit(main())

"""Project status and git workflow commands."""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Optional

from pipeline_tools.core.cli import FriendlyArgumentParser
from pipeline_tools.core.paths import get_creative_root
from pipeline_tools.core import db


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = FriendlyArgumentParser(
        description="Check project status and manage git workflow."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # Status command
    c_status = sub.add_parser("status", help="Show project git status")
    c_status.add_argument(
        "project",
        nargs="?",
        help="Project folder name (e.g., AN_PKU_POKU). If not provided, shows all projects.",
    )

    # Commit command
    c_commit = sub.add_parser("commit", help="Commit changes in a project")
    c_commit.add_argument("project", help="Project folder name (e.g., AN_PKU_POKU)")
    c_commit.add_argument("-m", "--message", help="Commit message")
    c_commit.add_argument(
        "--push", action="store_true", help="Push to remote after committing"
    )

    # List command
    c_list = sub.add_parser("list", help="List all projects with their status")

    return parser.parse_args(argv)


def get_project_path(project_name: str) -> Optional[Path]:
    """Get the full path to a project."""
    creative_root = get_creative_root()
    project_path = creative_root / project_name

    if not project_path.exists():
        print(f"Error: Project '{project_name}' not found at {project_path}")
        return None

    # Check if it's a git repository
    git_dir = project_path / ".git"
    if not git_dir.exists():
        print(f"Error: Project '{project_name}' is not a git repository")
        return None

    return project_path


def cmd_status(args: argparse.Namespace) -> None:
    """Show git status for a project."""
    if args.project:
        # Show status for specific project
        project_path = get_project_path(args.project)
        if not project_path:
            sys.exit(1)

        print(f"\n📁 Project: [bold]{args.project}[/bold]")
        print(f"📍 Path: {project_path}\n")

        # Get detailed status information
        # Get current branch
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=project_path,
            capture_output=True,
            text=True,
        )
        current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"

        # Get status info
        status_result = subprocess.run(
            ["git", "status", "--porcelain", "--branch"],
            cwd=project_path,
            capture_output=True,
            text=True,
        )

        if status_result.returncode != 0:
            print(f"❌ Failed to get git status")
            sys.exit(1)

        lines = status_result.stdout.strip().split('\n')
        branch_line = lines[0] if lines else ""
        file_changes = [l for l in lines[1:] if l.strip()]

        # Parse branch tracking info
        ahead = 0
        behind = 0
        remote_branch = None
        if branch_line.startswith('##'):
            # Example: ## main...origin/main [ahead 1]
            parts = branch_line[3:].strip()
            if '...' in parts:
                local_remote = parts.split('[')[0].strip()
                if '...' in local_remote:
                    _, remote_branch = local_remote.split('...')

                # Check for ahead/behind
                if '[ahead' in parts:
                    ahead_match = parts.split('[ahead')[1].split(']')[0].strip()
                    try:
                        ahead = int(ahead_match.replace(',', '').strip())
                    except ValueError:
                        pass
                if 'behind' in parts:
                    behind_match = parts.split('behind')[1].split(']')[0].strip()
                    try:
                        behind = int(behind_match.replace(',', '').strip())
                    except ValueError:
                        pass

        # Display status summary
        print("╭─────────────────────────────────────────╮")
        print(f"│ 🌿 Branch: {current_branch:<26} │")

        if remote_branch:
            print(f"│ 🔗 Remote: {remote_branch:<26} │")
        else:
            print(f"│ 🔗 Remote: [dim]No remote tracking[/dim]{'':>9} │")

        if ahead > 0 and behind > 0:
            print(f"│ 📊 Status: ↑{ahead} ahead, ↓{behind} behind{'':>10} │")
        elif ahead > 0:
            print(f"│ 📊 Status: ↑ {ahead} commit(s) to push{'':>8} │")
        elif behind > 0:
            print(f"│ 📊 Status: ↓ {behind} commit(s) to pull{'':>7} │")
        else:
            print(f"│ 📊 Status: ✅ Up to date{'':>17} │")

        print(f"│ 📝 Changes: {len(file_changes)} file(s){'':>17} │")
        print("╰─────────────────────────────────────────╯")
        print()

        if file_changes:
            print("Modified files:")
            for change in file_changes[:10]:  # Show max 10 files
                status_code = change[:2]
                filename = change[3:].strip()

                # Parse status codes
                if status_code.strip() == 'M':
                    icon = "📝"
                    status_text = "Modified"
                elif status_code.strip() == 'A':
                    icon = "➕"
                    status_text = "Added"
                elif status_code.strip() == 'D':
                    icon = "➖"
                    status_text = "Deleted"
                elif status_code.strip() == 'R':
                    icon = "🔄"
                    status_text = "Renamed"
                elif status_code.strip() == '??':
                    icon = "❓"
                    status_text = "Untracked"
                else:
                    icon = "•"
                    status_text = "Changed"

                print(f"  {icon} {filename} [{status_text}]")

            if len(file_changes) > 10:
                print(f"  ... and {len(file_changes) - 10} more files")
            print()
            print("💡 Tip: Run 'commit' to save your changes")
        else:
            print("✅ Working tree clean - no changes to commit")
            if ahead > 0:
                print(f"💡 Tip: Run 'git push' to sync {ahead} commit(s) to remote")

        print()
    else:
        # Show status for all projects
        creative_root = get_creative_root()
        projects = [
            p for p in creative_root.iterdir()
            if p.is_dir() and not p.name.startswith('.') and (p / '.git').exists()
        ]

        if not projects:
            print("\n❌ No git projects found.")
            print(f"📍 Looking in: {creative_root}")
            print("\n💡 Tip: Create a new project with the 'create' command")
            return

        print(f"\n📂 Git Projects Overview\n")

        for idx, project in enumerate(sorted(projects), 1):
            # Get short status
            result = subprocess.run(
                ["git", "status", "--porcelain", "--branch"],
                cwd=project,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                branch_line = lines[0] if lines else ""
                file_changes = [l for l in lines[1:] if l.strip()]

                # Parse branch info
                current_branch = "unknown"
                ahead = 0
                remote_branch = None

                if branch_line.startswith('##'):
                    parts = branch_line[3:].strip()
                    # Get branch name
                    if '...' in parts:
                        current_branch = parts.split('...')[0].strip()
                        remote_info = parts.split('...')[1].split('[')[0].strip()
                        remote_branch = remote_info if remote_info else None

                        # Check for ahead
                        if '[ahead' in parts:
                            ahead_match = parts.split('[ahead')[1].split(']')[0].strip()
                            try:
                                ahead = int(ahead_match.replace(',', '').strip())
                            except ValueError:
                                pass
                    else:
                        # No remote tracking
                        current_branch = parts.split('[')[0].strip()

                # Determine overall status
                has_changes = len(file_changes) > 0
                needs_push = ahead > 0

                if has_changes:
                    status_icon = "📝"
                    status_text = "Changes pending"
                elif needs_push:
                    status_icon = "⬆️"
                    status_text = "Ready to push"
                else:
                    status_icon = "✅"
                    status_text = "Clean & synced"

                # Display project status
                print(f"{idx}. {status_icon} {project.name}")
                print(f"   🌿 {current_branch}", end="")

                if remote_branch:
                    print(f" → {remote_branch}", end="")

                if ahead > 0:
                    print(f" [↑{ahead}]", end="")

                print()  # New line

                if has_changes:
                    print(f"   📝 {len(file_changes)} file(s) changed")
                elif needs_push:
                    print(f"   ⬆️  {ahead} commit(s) to push")
                else:
                    print(f"   ✅ Up to date")

                print()
            else:
                print(f"{idx}. ❓ {project.name}")
                print(f"   ⚠️  Git status unavailable")
                print()

        print("💡 Tip: Type 'status <number>' to see detailed status for a project")


def cmd_commit(args: argparse.Namespace) -> None:
    """Commit changes in a project."""
    project_path = get_project_path(args.project)
    if not project_path:
        sys.exit(1)

    print(f"\n📁 Project: {args.project}")
    print(f"📍 Path: {project_path}\n")

    # Show current status
    print("Current status:")
    subprocess.run(["git", "status", "--short"], cwd=project_path)
    print()

    # Get commit message
    message = args.message
    if not message:
        print("Enter commit message (Ctrl+C to cancel):")
        try:
            message = input("> ").strip()
        except KeyboardInterrupt:
            print("\n\nAborted.")
            sys.exit(0)

    if not message:
        print("Error: Commit message cannot be empty")
        sys.exit(1)

    # Stage all changes
    print("Staging changes...")
    result = subprocess.run(
        ["git", "add", "."],
        cwd=project_path,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"❌ Failed to stage changes: {result.stderr}")
        sys.exit(1)

    # Create commit
    print(f"Creating commit: '{message}'")
    result = subprocess.run(
        ["git", "commit", "-m", message],
        cwd=project_path,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        if "nothing to commit" in result.stdout:
            print("✅ Nothing to commit, working tree clean")
        else:
            print(f"❌ Failed to commit: {result.stderr}")
            sys.exit(1)
    else:
        print(f"✅ Committed successfully")
        print(result.stdout)

    # Push if requested
    if args.push:
        print("\nPushing to remote...")
        result = subprocess.run(
            ["git", "push"],
            cwd=project_path,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"❌ Failed to push: {result.stderr}")
            sys.exit(1)
        else:
            print("✅ Pushed successfully")

    print()


def cmd_list(args: argparse.Namespace) -> None:
    """List all projects with their status."""
    creative_root = get_creative_root()
    all_projects = [
        p for p in creative_root.iterdir()
        if p.is_dir() and not p.name.startswith('.')
    ]

    if not all_projects:
        print("No projects found.")
        return

    print(f"\n📂 Projects in {creative_root}\n")

    for project in sorted(all_projects):
        git_dir = project / '.git'
        if git_dir.exists():
            # Get git status
            result = subprocess.run(
                ["git", "status", "--short", "--branch"],
                cwd=project,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                branch_line = lines[0] if lines else ""
                changes = len([l for l in lines[1:] if l.strip()])

                status_icon = "✅" if changes == 0 else "📝"
                print(f"{status_icon} {project.name} (git)")
                print(f"   {branch_line}")
                if changes > 0:
                    print(f"   {changes} file(s) changed")
            else:
                print(f"❓ {project.name} (git - status unavailable)")
        else:
            print(f"📁 {project.name} (no git)")

        print()


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    if args.command == "status":
        cmd_status(args)
    elif args.command == "commit":
        cmd_commit(args)
    elif args.command == "list":
        cmd_list(args)
    else:
        print("Unknown command")
        sys.exit(1)


if __name__ == "__main__":
    main()

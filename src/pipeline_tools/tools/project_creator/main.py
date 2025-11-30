import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from pipeline_tools.core.cli import FriendlyArgumentParser
from pipeline_tools.core.paths import make_show_root
from pipeline_tools.core.fs_utils import create_folders
from pipeline_tools.core.git_utils import setup_git_repo, GitError, check_git_available, check_git_lfs_available
from pipeline_tools.core.db import get_conn
from .templates import TEMPLATES
from .gitignore_templates import GITIGNORE_TEMPLATES
from .gitattributes_templates import GITATTRIBUTES_TEMPLATES
from .starter_files import create_animation_starter_files


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
    parser.add_argument(
        "--git",
        "-g",
        action="store_true",
        help="Initialize a git repository in the project.",
    )
    parser.add_argument(
        "--git-lfs",
        action="store_true",
        help="Initialize Git LFS for large file support (implies --git).",
    )
    parser.add_argument(
        "--git-branch",
        default="main",
        help="Initial git branch name (default: main).",
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


def _write_gitignore(project_path: Path, template_key: str) -> None:
    """Write .gitignore file for the project."""
    gitignore_content = GITIGNORE_TEMPLATES.get(template_key, GITIGNORE_TEMPLATES["animation_short"])
    gitignore_path = project_path / ".gitignore"
    gitignore_path.write_text(gitignore_content)


def _write_gitattributes(project_path: Path, template_key: str) -> None:
    """Write .gitattributes file for the project."""
    gitattributes_content = GITATTRIBUTES_TEMPLATES.get(template_key, GITATTRIBUTES_TEMPLATES["animation_short"])
    gitattributes_path = project_path / ".gitattributes"
    gitattributes_path.write_text(gitattributes_content)


def _register_project_in_db(show_code: str, project_name: str, template_key: str, show_root: Path) -> None:
    """Register the project in the database."""
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()

    # Check if project already exists
    existing = cur.execute("SELECT code FROM shows WHERE code=?", (show_code,)).fetchone()
    if existing:
        print(f"Project '{show_code}' already registered in database, updating...")
        cur.execute(
            "UPDATE shows SET name=?, template=?, root=?, updated_at=? WHERE code=?",
            (project_name, template_key, str(show_root), now, show_code)
        )
    else:
        print(f"Registering project '{show_code}' in database...")
        cur.execute(
            "INSERT INTO shows(code, name, template, root, created_at, updated_at) VALUES(?,?,?,?,?,?)",
            (show_code, project_name, template_key, str(show_root), now, now)
        )

    conn.commit()
    conn.close()


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    template_key = args.template or "animation_short"
    show_code = args.show_code
    project_name = args.name
    use_git = args.git or args.git_lfs
    use_lfs = args.git_lfs
    git_branch = args.git_branch

    # Check Git availability if requested
    if use_git and not check_git_available():
        print("Error: Git is not installed or not available in PATH.")
        print("Please install Git to use --git or --git-lfs options.")
        sys.exit(1)

    if use_lfs and not check_git_lfs_available():
        print("Error: Git LFS is not installed or not available in PATH.")
        print("Please install Git LFS to use --git-lfs option.")
        print("Visit: https://git-lfs.github.com/")
        sys.exit(1)

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
        if use_git:
            print(f"Git repository: Yes (branch: {git_branch})")
            if use_lfs:
                print("Git LFS: Yes")
        print("Dry run complete; nothing was created.")
        return

    if args.interactive and not args.yes:
        _preview_tree(show_root, rel_paths)
        if use_git:
            print(f"Git repository: Yes (branch: {git_branch})")
            if use_lfs:
                print("Git LFS: Yes")
        proceed = input("Create these folders? [y/N]: ").strip().lower()
        if proceed not in {"y", "yes"}:
            print("Aborted.")
            return

    print(f"Creating project at: {show_root}")
    create_folders(show_root, rel_paths)

    # Register project in database
    _register_project_in_db(show_code, project_name, template_key, show_root)

    # Create starter files for animation projects
    if template_key in ['animation_short', 'animation_series']:
        print("Creating starter files (PureRef, Krita)...")
        created_files = create_animation_starter_files(
            show_root,
            show_code,
            project_name,
            template_key
        )

        # Report created files
        if created_files['pureref']:
            print(f"  Created {len(created_files['pureref'])} PureRef file(s)")
        if created_files['krita']:
            print(f"  Created {len(created_files['krita'])} Krita file(s)")
        if created_files['blender']:
            print(f"  Created {len(created_files['blender'])} Blender file(s)")

    # Write .gitignore if using git
    if use_git:
        print("Creating .gitignore...")
        _write_gitignore(show_root, template_key)

        # Write .gitattributes if using LFS
        if use_lfs:
            print("Creating .gitattributes for LFS...")
            _write_gitattributes(show_root, template_key)

        # Initialize git repository
        try:
            print(f"Initializing Git repository (branch: {git_branch})...")
            setup_git_repo(
                show_root,
                use_lfs=use_lfs,
                initial_branch=git_branch,
                create_commit=True,
                commit_message=f"Initial commit: {project_name} ({show_code})",
            )
            print("Git repository initialized successfully.")
            if use_lfs:
                print("Git LFS configured and ready.")
        except GitError as e:
            print(f"Warning: Git initialization failed: {e}")
            print("Project created but without Git repository.")

    print("Done.")


if __name__ == "__main__":
    main()

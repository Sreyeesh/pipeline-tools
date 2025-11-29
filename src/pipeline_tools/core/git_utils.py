"""Git repository utilities for project initialization."""

import subprocess
from pathlib import Path
from typing import Optional


class GitError(Exception):
    """Raised when a git operation fails."""
    pass


def check_git_available() -> bool:
    """Check if git is installed and available."""
    try:
        subprocess.run(
            ["git", "--version"],
            capture_output=True,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_git_lfs_available() -> bool:
    """Check if git-lfs is installed and available."""
    try:
        subprocess.run(
            ["git-lfs", "--version"],
            capture_output=True,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def init_git_repo(
    project_path: Path,
    initial_branch: str = "main",
) -> None:
    """
    Initialize a git repository at the given path.

    Args:
        project_path: Path to the project directory
        initial_branch: Name of the initial branch (default: main)

    Raises:
        GitError: If git initialization fails
    """
    if not check_git_available():
        raise GitError("Git is not installed or not available in PATH")

    try:
        # Initialize git repo
        subprocess.run(
            ["git", "init", "-b", initial_branch],
            cwd=project_path,
            capture_output=True,
            check=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise GitError(f"Failed to initialize git repository: {e.stderr}")


def init_git_lfs(project_path: Path) -> None:
    """
    Initialize Git LFS in the repository.

    Args:
        project_path: Path to the project directory

    Raises:
        GitError: If git-lfs initialization fails
    """
    if not check_git_lfs_available():
        raise GitError("Git LFS is not installed or not available in PATH")

    try:
        # Install git-lfs hooks
        subprocess.run(
            ["git", "lfs", "install"],
            cwd=project_path,
            capture_output=True,
            check=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise GitError(f"Failed to initialize Git LFS: {e.stderr}")


def create_initial_commit(
    project_path: Path,
    message: str = "Initial commit: project structure",
) -> None:
    """
    Create an initial commit with all files.

    Args:
        project_path: Path to the project directory
        message: Commit message

    Raises:
        GitError: If commit creation fails
    """
    try:
        # Stage all files
        subprocess.run(
            ["git", "add", "."],
            cwd=project_path,
            capture_output=True,
            check=True,
            text=True,
        )

        # Create commit
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=project_path,
            capture_output=True,
            check=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise GitError(f"Failed to create initial commit: {e.stderr}")


def setup_git_repo(
    project_path: Path,
    use_lfs: bool = False,
    initial_branch: str = "main",
    create_commit: bool = True,
    commit_message: Optional[str] = None,
) -> None:
    """
    Set up a complete git repository with optional LFS support.

    Args:
        project_path: Path to the project directory
        use_lfs: Whether to initialize Git LFS
        initial_branch: Name of the initial branch (default: main)
        create_commit: Whether to create an initial commit
        commit_message: Custom commit message (optional)

    Raises:
        GitError: If any git operation fails
    """
    # Initialize git repository
    init_git_repo(project_path, initial_branch)

    # Initialize Git LFS if requested
    if use_lfs:
        init_git_lfs(project_path)

    # Create initial commit if requested
    if create_commit:
        msg = commit_message or "Initial commit: project structure"
        create_initial_commit(project_path, msg)

"""List non-primary Git branches in a directory tree."""

import os
import subprocess
import sys
from pathlib import Path
from shutil import which

from fortext import Fg, style


def p(*values: object) -> None:
    """Print to stdout."""
    print(*values)  # noqa: T201


def get_git_path(git_executable: str) -> Path:
    """Check if the configured git executable exists and is runnable."""
    which_git = which(git_executable)

    if not which_git:
        p(f'Error: `{git_executable}` is not installed or not found in PATH.')
        sys.exit(1)
    try:
        subprocess.run(  # noqa: S603
            [git_executable, '--version'],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return Path(which_git).resolve()
    except (subprocess.CalledProcessError, FileNotFoundError):
        p(f'Error: `{git_executable}` is not a valid Git executable.')
        sys.exit(1)


def get_git_repos(root: Path, *, skip_hidden_dirs: bool) -> list[Path]:
    """Recursively find all directories under root that contain a `.git` folder."""
    git_repos: list[Path] = []
    for dirpath, dirnames, _ in os.walk(root):
        if skip_hidden_dirs:
            dirnames[:] = [d for d in dirnames if not d.startswith('.') or d == '.git']
        if '.git' in dirnames:
            git_repos.append(Path(dirpath))
            dirnames.clear()
    return git_repos


def get_repo_branches(repo_path: Path, git_path: Path) -> list[str]:
    """Get the list of branches in a Git repository."""
    try:
        result = subprocess.run(  # noqa: S603
            [git_path.as_posix(), '-C', str(repo_path), 'branch', '--format=%(refname:short)'],
            check=True,
            capture_output=True,
            text=True,
        )
        return [line.strip() for line in result.stdout.strip().splitlines()]
    except subprocess.CalledProcessError:
        return []


def get_repo_name(repo_path: Path, git_path: Path) -> str | None:
    """Try to extract a friendly name for a Git repository based on its remote origin URL."""
    try:
        result = subprocess.run(  # noqa: S603
            [git_path.as_posix(), '-C', str(repo_path), 'remote', 'get-url', 'origin'],
            check=True,
            capture_output=True,
            text=True,
        )
        url = result.stdout.strip()
        url.removesuffix('.git')
        if '://' in url:
            path = url.split('://')[1].split('/', 1)[1]
        elif '@' in url:
            path = url.split('@', 1)[1].split(':', 1)[1]
        else:
            return repo_path.name
    except subprocess.CalledProcessError:
        return repo_path.name
    else:
        return path


def find_repos_with_branches(root: Path, git_path: Path, *, skip_hidden_dirs: bool) -> None:
    """Find all Git repositories under root and print their non-primary branches."""
    home = Path.home().resolve()
    repo_paths = {p.resolve() for p in get_git_repos(root, skip_hidden_dirs=skip_hidden_dirs)}

    for repo_path in sorted(repo_paths):
        all_branches = get_repo_branches(repo_path, git_path)
        primary_branch = get_primary_branch(repo_path, git_path)
        branches = [b for b in all_branches if b != primary_branch]
        if branches:
            try:
                display_path = f'~/{repo_path.relative_to(home)}'
            except ValueError:
                display_path = str(repo_path)
            p(style(f'=== {display_path} ===', Fg.BRIGHT_CYAN))
            for branch in branches:
                p(style(f'* {branch}', Fg.YELLOW))
            p()


def get_primary_branch(repo_path: Path, git_path: Path) -> str | None:
    """Get the name of the primary branch in a Git repository."""

    def _run_git(args: list[str]) -> str | None:
        try:
            result = subprocess.run(  # noqa: S603
                [git_path.as_posix(), '-C', str(repo_path), *args],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,  # suppress fatal messages
                text=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    # 1: origin/HEAD
    ref = _run_git(['symbolic-ref', 'refs/remotes/origin/HEAD'])
    if ref:
        return ref.removeprefix('refs/remotes/origin/')

    # 2️: remote show origin
    output = _run_git(['remote', 'show', 'origin'])
    if output:
        for line in output.splitlines():
            if 'HEAD branch:' in line:
                return line.split(':', 1)[1].strip()

    # 3️: main/master
    for branch in ('main', 'master'):
        if _run_git(['show-ref', '--verify', f'refs/heads/{branch}']):
            return branch

    return None

"""List non-primary Git branches in a directory tree."""

import argparse
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
    """Get the list of non-main/non-master branches in a Git repository."""
    try:
        result = subprocess.run(  # noqa: S603
            [git_path.as_posix(), '-C', str(repo_path), 'branch', '--format=%(refname:short)'],
            check=True,
            capture_output=True,
            text=True,
        )
        branches = [line.strip() for line in result.stdout.strip().splitlines()]
        return [b for b in branches if b not in {'main', 'master'}]
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
    """Find all Git repositories under root and print their non-main/master branches."""
    home = Path.home().resolve()
    repo_paths = {p.resolve() for p in get_git_repos(root, skip_hidden_dirs=skip_hidden_dirs)}

    for repo_path in sorted(repo_paths):
        branches = get_repo_branches(repo_path, git_path)
        if branches:
            try:
                display_path = f'~/{repo_path.relative_to(home)}'
            except ValueError:
                display_path = str(repo_path)
            p(style(f'=== {display_path} ===', Fg.BRIGHT_CYAN))
            for branch in branches:
                p(style(f'* {branch}', Fg.YELLOW))
            p()


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='List non-main/non-master Git branches in a directory tree.'
    )
    parser.add_argument('path', type=Path, help='Root directory to scan for Git repositories.')
    parser.add_argument(
        '--include-hidden',
        action='store_true',
        help='Include hidden directories (default: hidden dirs are skipped).',
    )
    parser.add_argument(
        '--git-path',
        type=str,
        default='git',
        help='Path to the `git` executable (default: use first found in PATH).',
    )
    return parser.parse_args()


def main() -> None:
    """Program entry point."""
    args = parse_args()
    git_executable = args.git_path

    git_path = get_git_path(git_executable)

    root = args.path.expanduser().resolve()
    if not root.exists() or not root.is_dir():
        p(f'Invalid path: {root}')
        sys.exit(1)

    skip_hidden_dirs = not args.include_hidden
    find_repos_with_branches(root, git_path, skip_hidden_dirs=skip_hidden_dirs)


if __name__ == '__main__':
    main()

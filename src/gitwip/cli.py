"""Command line interface functionality."""

import argparse
import sys
from importlib.metadata import version
from pathlib import Path

from gitwip.main import find_repos_with_branches, get_git_path, p


class VersionAction(argparse.Action):
    """Print the installed package version when requested."""

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        _namespace: argparse.Namespace,
        _values: object,
        _option_string: str | None = None,
    ) -> None:
        """Exit after printing the version."""
        sys.stdout.write(f'{parser.prog} {version("gitwip")}\n')
        parser.exit()


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='List non-primary Git branches and stashes in a directory tree.'
    )
    parser.add_argument(
        '--version', action=VersionAction, nargs=0, help='Show the version and exit.'
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


def cli() -> None:
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
    cli()

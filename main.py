import os
import subprocess
import sys
import argparse
from pathlib import Path
from typing import Optional

ANSI_HEADER = "\033[1;36m"  # bright cyan
ANSI_BRANCH = "\033[0;33m"  # yellow
ANSI_RESET = "\033[0m"


def get_git_repos(root: Path, skip_hidden_dirs: bool) -> list[Path]:
    git_repos: list[Path] = []
    for dirpath, dirnames, _ in os.walk(root):
        if skip_hidden_dirs:
            dirnames[:] = [d for d in dirnames if not d.startswith(".") or d == ".git"]
        if ".git" in dirnames:
            git_repos.append(Path(dirpath))
            dirnames.clear()
    return git_repos


def get_repo_branches(repo_path: Path) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "branch", "--format=%(refname:short)"],
            check=True,
            capture_output=True,
            text=True,
        )
        branches = [line.strip() for line in result.stdout.strip().splitlines()]
        return [b for b in branches if b not in {"main", "master"}]
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: `git` is not installed or not found in PATH.")
        sys.exit(1)


def get_repo_name(repo_path: Path) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "remote", "get-url", "origin"],
            check=True,
            capture_output=True,
            text=True,
        )
        url = result.stdout.strip()
        if url.endswith(".git"):
            url = url[:-4]
        if "://" in url:
            path = url.split("://")[1].split("/", 1)[1]
        elif "@" in url:
            path = url.split("@", 1)[1].split(":", 1)[1]
        else:
            return repo_path.name
        return path
    except subprocess.CalledProcessError:
        return repo_path.name


def find_repos_with_branches(root: Path, skip_hidden_dirs: bool) -> None:
    home = Path.home().resolve()
    repo_paths = {p.resolve() for p in get_git_repos(root, skip_hidden_dirs)}

    for repo_path in sorted(repo_paths):
        branches = get_repo_branches(repo_path)
        if branches:
            try:
                display_path = f"~/{repo_path.relative_to(home)}"
            except ValueError:
                display_path = str(repo_path)
            print(f"{ANSI_HEADER}=== {display_path} ==={ANSI_RESET}")
            for branch in branches:
                print(f"{ANSI_BRANCH}* {branch}{ANSI_RESET}")
            print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="List non-main/non-master Git branches in a directory tree."
    )
    parser.add_argument(
        "path", type=Path, help="Root directory to scan for Git repositories."
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden directories (default: hidden dirs are skipped).",
    )

    args = parser.parse_args()
    root = args.path.expanduser().resolve()

    if not root.exists() or not root.is_dir():
        print(f"Invalid path: {root}")
        sys.exit(1)

    skip_hidden_dirs = not args.include_hidden
    find_repos_with_branches(root, skip_hidden_dirs)


if __name__ == "__main__":
    main()

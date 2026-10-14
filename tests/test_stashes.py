"""Integration tests for listing Git stashes."""

import subprocess
from pathlib import Path

import pytest

from gitwip.main import find_repos_with_branches


def git(repo: Path, *args: str) -> None:
    """Run Git in a test repository."""
    subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True)


def test_stash_without_non_primary_branches(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A repository with only a primary branch still appears when it has a stash."""
    repo = tmp_path / 'example'
    repo.mkdir()
    git(repo, 'init', '-b', 'main')
    git(repo, 'config', 'user.name', 'Test User')
    git(repo, 'config', 'user.email', 'test@example.com')
    (repo / 'file.txt').write_text('initial')
    git(repo, 'add', 'file.txt')
    git(repo, 'commit', '-m', 'initial')
    (repo / 'file.txt').write_text('changed')
    git(repo, 'stash', 'push', '-m', 'unfinished work')

    find_repos_with_branches(tmp_path, Path('git'), skip_hidden_dirs=True)

    output = capsys.readouterr().out
    assert '=== ' in output
    assert 'stash@{0}: On main: unfinished work' in output
    assert '* main' not in output

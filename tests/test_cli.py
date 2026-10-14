"""Tests for the command-line interface."""

import sys
from importlib.metadata import version

import pytest

from gitwip.cli import cli


def test_version_exits_without_path(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The version flag works without the required repository path."""
    monkeypatch.setattr(sys, 'argv', ['gitwip', '--version'])

    with pytest.raises(SystemExit) as exc_info:
        cli()

    assert exc_info.value.code == 0
    assert capsys.readouterr().out == f'gitwip {version("gitwip")}\n'

import sys

import pytest

from giv.main import main


def test_version_flag(capsys):
    # Ensure --version prints the version and exits with code 0
    ret = main(["--version"])
    assert ret == 0
    captured = capsys.readouterr()
    # Output should be a semantic version string
    out = captured.out.strip()
    assert out != ""
    assert "." in out


def test_help_flag(capsys):
    # Ensure --help prints usage and exits with code 0
    ret = main(["--help"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "usage" in captured.out.lower()


def test_message_dry_run(capsys):
    # Without git, diff will be empty; ensure prompt prints at least header
    # Global args must come before subcommand
    ret = main(["--dry-run", "message"])
    assert ret == 0
    captured = capsys.readouterr()
    output = captured.out.strip()
    # The prompt should contain the header text '# Commit Message Request' from template
    assert "Commit Message Request" in output
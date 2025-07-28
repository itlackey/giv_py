from giv import __version__


def test_version_string():
    # Should match the package version declared in pyproject.toml
    assert isinstance(__version__, str)
    parts = __version__.split(".")
    assert len(parts) >= 3
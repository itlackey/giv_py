from giv.config import ConfigManager


def test_config_set_get_list_unset(working_directory):
    """Test basic configuration operations with isolated directory."""
    cfg_path = working_directory / "config"
    mgr = ConfigManager(config_path=cfg_path)
    # Initially empty
    assert mgr.list() == {}
    assert mgr.get("foo") is None
    # Set a value
    mgr.set("foo", "bar")
    assert mgr.get("foo") == "bar"
    assert mgr.list() == {"foo": "bar"}
    # Update value
    mgr.set("foo", "baz")
    assert mgr.get("foo") == "baz"
    # Add another key
    mgr.set("alpha", "beta")
    result = mgr.list()
    assert result["foo"] == "baz"
    assert result["alpha"] == "beta"
    # Unset key
    mgr.unset("foo")
    assert mgr.get("foo") is None
    assert "foo" not in mgr.list()
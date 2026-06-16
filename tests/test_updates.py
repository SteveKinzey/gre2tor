from gre2tor.updates import _is_newer, check_for_updates


def test_is_newer_compares_release_tags():
    assert _is_newer("v0.1.1", "0.1.0") is True
    assert _is_newer("v1.0.0", "0.9.9") is True
    assert _is_newer("v0.1.0", "0.1.0") is False
    assert _is_newer("v0.0.9", "0.1.0") is False


def test_update_check_can_be_disabled(monkeypatch):
    monkeypatch.setenv("GRE2TOR_DISABLE_UPDATE_CHECK", "1")
    info = check_for_updates(force=True)
    assert info["checked"] is False
    assert info["update_available"] is False
    assert info["current_version"]

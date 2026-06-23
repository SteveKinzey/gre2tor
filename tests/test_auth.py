import re

from gre2tor import create_app


def _app(tmp_path, **overrides):
    config = {
        "DATABASE_PATH": tmp_path / "auth.sqlite3",
        "INSTANCE_PATH": tmp_path / "instance",
        "SECRET_KEY": "test-secret",
        "AUTH_ALLOW_DEV_MAGIC_LINK": True,
        "AUTH_ALLOWED_EMAILS": "",
    }
    config.update(overrides)
    app = create_app(config)
    app.config.update(TESTING=True)
    return app


def _extract_dev_magic_link(html: str) -> str:
    match = re.search(r'href="([^"]+/login/[^"]+)"', html)
    assert match, html
    return match.group(1)


def test_app_requires_login_for_pages_and_api(tmp_path, monkeypatch):
    monkeypatch.setenv("GRE2TOR_DISABLE_UPDATE_CHECK", "1")
    client = _app(tmp_path).test_client()

    page = client.get("/")
    api = client.post("/api/attempts", json={})
    health = client.get("/health")

    assert page.status_code == 302
    assert "/login" in page.headers["Location"]
    assert api.status_code == 401
    assert health.status_code == 200


def test_magic_link_logs_user_in(tmp_path, monkeypatch):
    monkeypatch.setenv("GRE2TOR_DISABLE_UPDATE_CHECK", "1")
    client = _app(tmp_path).test_client()

    response = client.post("/login", data={"email": "STUDENT@example.com", "next": "/topics"})
    assert response.status_code == 200
    link = _extract_dev_magic_link(response.get_data(as_text=True))

    login_response = client.get(link)
    assert login_response.status_code == 302
    assert login_response.headers["Location"].endswith("/topics")

    topics = client.get("/topics")
    assert topics.status_code == 200
    assert b"Logout" in topics.data


def test_allowed_email_restriction(tmp_path, monkeypatch):
    monkeypatch.setenv("GRE2TOR_DISABLE_UPDATE_CHECK", "1")
    client = _app(tmp_path, AUTH_ALLOWED_EMAILS="allowed@example.com").test_client()

    denied = client.post("/login", data={"email": "other@example.com"})
    allowed = client.post("/login", data={"email": "allowed@example.com"})

    assert b"not allowed" in denied.data
    assert b"Check your email" in allowed.data


def test_reset_clears_only_current_user_progress(tmp_path, monkeypatch):
    monkeypatch.setenv("GRE2TOR_DISABLE_UPDATE_CHECK", "1")
    app = _app(tmp_path)

    first = app.test_client()
    response = first.post("/login", data={"email": "first@example.com"})
    first.get(_extract_dev_magic_link(response.get_data(as_text=True)))
    first.post("/api/attempts", json={"card_id": "fractions-decimals-add-unlike-denominators", "user_answer": "3/2"})

    second = app.test_client()
    response = second.post("/login", data={"email": "second@example.com"})
    second.get(_extract_dev_magic_link(response.get_data(as_text=True)))
    second.post("/api/attempts", json={"card_id": "fractions-decimals-add-unlike-denominators", "user_answer": "3/2"})

    assert b"1</strong><span>Cards attempted" in first.get("/").data
    assert b"1</strong><span>Cards attempted" in second.get("/").data

    first.post("/reset-progress", data={"confirmation": "reset"})
    assert b"1</strong><span>Cards attempted" in first.get("/").data

    first.post("/reset-progress", data={"confirmation": "RESET"})
    assert b"0</strong><span>Cards attempted" in first.get("/").data
    assert b"1</strong><span>Cards attempted" in second.get("/").data

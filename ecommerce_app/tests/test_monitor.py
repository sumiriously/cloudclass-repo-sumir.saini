import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from app import create_app
from app.models import db


@pytest.fixture
def app(tmp_path):
    flask_app = create_app()
    flask_app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret",
            "RECEIPT_DIR": str(tmp_path / "receipts"),
            "ADMIN_EMAIL": "staff@example.com",
        }
    )

    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_health_includes_runtime_counters(client):
    client.get("/ui/shop")
    response = client.get("/health")
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["status"] == "ok"
    assert payload["uptime_seconds"] >= 0
    assert payload["requests"] >= 1


def test_requests_are_counted(client, app):
    client.get("/ui/shop")
    snapshot = app.extensions["monitor"].snapshot()
    paths = [item["path"] for item in snapshot["recent"]]
    assert "/ui/shop" in paths
    assert snapshot["requests"] >= 1


def test_failed_login_is_counted(client, app):
    for _ in range(3):
        client.post("/login", json={"email": "missing@example.com", "password": "test12345"})
    snapshot = app.extensions["monitor"].snapshot()
    assert snapshot["failed_logins"] == 3
    assert snapshot["alert"] is True


def test_monitor_page_is_staff_only(client):
    guest = client.get("/ui/monitor")
    assert guest.status_code == 302
    assert "/ui/login" in guest.headers["Location"]

    client.post("/ui/register", data={"email": "shopper@example.com", "password": "test12345"})
    client.post("/ui/login", data={"email": "shopper@example.com", "password": "test12345"})
    denied = client.get("/ui/monitor", follow_redirects=True)
    assert "Only shop staff" in denied.get_data(as_text=True)

    staff = client.application.test_client()
    staff.post("/ui/register", data={"email": "staff@example.com", "password": "test12345"})
    staff.post("/ui/login", data={"email": "staff@example.com", "password": "test12345"})
    page = staff.get("/ui/monitor")
    html = page.get_data(as_text=True)
    assert page.status_code == 200
    assert "Failed sign-ins" in html
    assert "Recent requests" in html

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from app.models import db


@pytest.fixture
def app():
    flask_app = create_app()
    flask_app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret",
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


def test_register(client):
    response = client.post(
        "/register",
        json={"email": "test@example.com", "password": "test12345"},
    )

    assert response.status_code == 201
    assert response.get_json()["message"] == "User created"


def test_register_rejects_invalid_email(client):
    response = client.post(
        "/register",
        json={"email": "bad-email", "password": "test12345"},
    )
    assert response.status_code == 400


def test_register_rejects_weak_password(client):
    response = client.post(
        "/register",
        json={"email": "test2@example.com", "password": "short"},
    )
    assert response.status_code == 400


def test_login_requires_existing_user(client):
    response = client.post(
        "/login",
        json={"email": "missing@example.com", "password": "test12345"},
    )
    assert response.status_code == 401


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"

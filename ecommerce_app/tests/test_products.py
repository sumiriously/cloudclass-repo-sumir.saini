import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.models import User, db


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


def test_create_product_requires_auth(client):
    response = client.post("/products", json={"name": "A", "price": 2.0})
    assert response.status_code == 401


def test_create_product_validates_payload(client, app):
    with app.app_context():
        user = User(email="u@example.com", password_hash=generate_password_hash("validpass123"))
        db.session.add(user)
        db.session.commit()

    with client:
        client.post("/login", json={"email": "u@example.com", "password": "validpass123"})
        response = client.post("/products", json={"name": "", "price": -1})
        assert response.status_code == 400

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import boto3
import pytest

from app import create_app
from app.models import Order, db


@pytest.fixture
def app(tmp_path):
    flask_app = create_app()
    flask_app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret",
            "RECEIPT_DIR": str(tmp_path / "receipts"),
            "ADMIN_EMAIL": "",
            "SPACES_KEY": "",
            "SPACES_SECRET": "",
            "SPACES_BUCKET": "",
            "SPACES_REGION": "",
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


def _place_order(client, email="kai@example.com", name="Kai Shore"):
    client.post("/ui/cart/add", data={"product_id": 4})
    return client.post(
        "/ui/checkout",
        data={"customer_name": name, "email": email},
        follow_redirects=False,
    )


def _register_and_login(client, email, password="test12345"):
    client.post("/ui/register", data={"email": email, "password": password})
    return client.post("/ui/login", data={"email": email, "password": password}, follow_redirects=True)


def test_checkout_requires_customer_details(client):
    client.post("/ui/cart/add", data={"product_id": 4})
    response = client.post("/ui/checkout", data={"customer_name": "", "email": "not-an-email"})
    assert response.status_code == 400
    cart = client.get("/ui/cart")
    assert "Leash 7ft Coil" in cart.get_data(as_text=True)


def test_checkout_saves_order_and_local_receipt(client, app):
    response = _place_order(client)
    assert response.status_code == 302
    detail = client.get(response.location)
    html = detail.get_data(as_text=True)
    assert "Order confirmed" in html
    assert "Leash 7ft Coil" in html
    assert "local storage" in html

    with app.app_context():
        order = Order.query.one()
        assert order.email == "kai@example.com"
        assert order.status == "placed"
        assert order.total == 29.0
        assert order.receipt_storage == "local"
        assert len(order.items) == 1

    receipt = client.get(f"/ui/orders/{order.id}/receipt")
    body = receipt.get_data(as_text=True)
    assert "Leash 7ft Coil" in body
    assert "Receipt storage: local storage" in body
    assert receipt.headers["Content-Type"] == "text/plain; charset=utf-8"


def test_customer_sees_only_matching_orders(client, app):
    _place_order(client, email="kai@example.com")
    _register_and_login(client, "kai@example.com")
    own = client.get("/ui/orders")
    assert "Kai Shore" in own.get_data(as_text=True)

    other = app.test_client()
    _register_and_login(other, "other@example.com")
    hidden = other.get("/ui/orders/1", follow_redirects=True)
    assert "not available" in hidden.get_data(as_text=True)
    listing = other.get("/ui/orders")
    assert "Kai Shore" not in listing.get_data(as_text=True)


def test_guest_orders_page_requires_login(client):
    response = client.get("/ui/orders")
    assert response.status_code == 302
    assert "/ui/login" in response.headers["Location"]


def test_staff_can_update_status_and_filter(client, app):
    app.config["ADMIN_EMAIL"] = "staff@example.com"
    _place_order(client, email="shopper@example.com", name="Shopper")

    staff = app.test_client()
    _register_and_login(staff, "staff@example.com")
    listing = staff.get("/ui/orders")
    assert "Shopper" in listing.get_data(as_text=True)

    updated = staff.post("/ui/orders/1/status", data={"status": "shipped"}, follow_redirects=True)
    assert "marked shipped" in updated.get_data(as_text=True)
    assert "Shipped" in updated.get_data(as_text=True)

    filtered = staff.get("/ui/orders?status=delivered")
    assert "Shopper" not in filtered.get_data(as_text=True)

    shopper = app.test_client()
    _register_and_login(shopper, "shopper@example.com")
    denied = shopper.post("/ui/orders/1/status", data={"status": "delivered"}, follow_redirects=True)
    assert "Only shop staff" in denied.get_data(as_text=True)


def test_spaces_upload_is_used_when_configured(client, app, monkeypatch):
    stored = {}

    class FakeBody:
        def __init__(self, data):
            self._data = data

        def read(self):
            return self._data

    class FakeClient:
        def put_object(self, **kwargs):
            stored["put"] = kwargs

        def get_object(self, **kwargs):
            return {"Body": FakeBody(stored["put"]["Body"])}

    class FakeSession:
        def client(self, service, **kwargs):
            stored["service"] = service
            stored["endpoint"] = kwargs.get("endpoint_url")
            stored["region"] = kwargs.get("region_name")
            return FakeClient()

    monkeypatch.setattr(boto3.session, "Session", lambda: FakeSession())
    app.config.update(
        {
            "SPACES_KEY": "spaces-key",
            "SPACES_SECRET": "spaces-secret",
            "SPACES_BUCKET": "tiki-receipts",
            "SPACES_REGION": "nyc3",
        }
    )

    response = _place_order(client)
    detail = client.get(response.location)
    assert "DigitalOcean Spaces (nyc3)" in detail.get_data(as_text=True)
    assert stored["service"] == "s3"
    assert stored["endpoint"] == "https://nyc3.digitaloceanspaces.com"
    assert stored["region"] == "nyc3"
    assert stored["put"]["Bucket"] == "tiki-receipts"
    assert stored["put"]["Key"] == "orders/order-1.txt"
    assert b"DigitalOcean Spaces (nyc3)" in stored["put"]["Body"]

    receipt = client.get("/ui/orders/1/receipt")
    assert "DigitalOcean Spaces (nyc3)" in receipt.get_data(as_text=True)


def test_spaces_failure_falls_back_to_local_file(client, app, monkeypatch):
    class FakeClient:
        def put_object(self, **kwargs):
            raise RuntimeError("spaces unavailable")

    class FakeSession:
        def client(self, service, **kwargs):
            return FakeClient()

    monkeypatch.setattr(boto3.session, "Session", lambda: FakeSession())
    app.config.update(
        {
            "SPACES_KEY": "spaces-key",
            "SPACES_SECRET": "spaces-secret",
            "SPACES_BUCKET": "tiki-receipts",
            "SPACES_REGION": "nyc3",
        }
    )

    _place_order(client)
    with app.app_context():
        order = Order.query.one()
        assert order.receipt_storage == "local"

    receipt = client.get("/ui/orders/1/receipt")
    assert "local storage" in receipt.get_data(as_text=True)

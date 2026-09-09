import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from app import create_app
from app.catalog import SURF_PRODUCTS
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


def test_product_listing_is_public(client):
    response = client.get("/ui/shop")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Product Listing" in html
    assert SURF_PRODUCTS[0]["name"] in html


def test_category_filter_limits_results(client):
    response = client.get("/ui/shop?category=Apparel")
    html = response.get_data(as_text=True)
    assert "Tiki Rash Guard" in html
    assert "Tiki Wave Rider Board" not in html


def test_product_detail_page(client):
    response = client.get("/ui/shop/1")
    assert response.status_code == 200
    assert "Tiki Wave Rider Board" in response.get_data(as_text=True)


def test_missing_product_redirects(client):
    response = client.get("/ui/shop/999", follow_redirects=True)
    assert response.status_code == 200
    assert "not in the catalog" in response.get_data(as_text=True)


def test_add_to_cart_and_view_total(client):
    response = client.post("/ui/cart/add", data={"product_id": 3}, follow_redirects=True)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Palm Wax (Tropical)" in html
    assert "$8.50" in html


def test_out_of_stock_cannot_be_added(client):
    response = client.post("/ui/cart/add", data={"product_id": 6}, follow_redirects=True)
    assert "out of stock" in response.get_data(as_text=True)

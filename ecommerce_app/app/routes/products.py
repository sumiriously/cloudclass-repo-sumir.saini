from flask import Blueprint, jsonify, request
from flask_login import login_required

from app.models import Product, db

products = Blueprint("products", __name__)


def validate_product_payload(data, partial=False):
    required = ("name", "price")
    if not partial:
        missing = [field for field in required if field not in data]
        if missing:
            return f"Missing fields: {', '.join(missing)}"

    if "name" in data and (not isinstance(data["name"], str) or not data["name"].strip()):
        return "Product name must be a non-empty string"
    if "price" in data:
        try:
            if float(data["price"]) < 0:
                return "Price must be non-negative"
        except (TypeError, ValueError):
            return "Price must be a number"
    if "stock" in data:
        try:
            if int(data["stock"]) < 0:
                return "Stock must be non-negative"
        except (TypeError, ValueError):
            return "Stock must be an integer"
    return None


@products.route("/products", methods=["GET"])
def get_products():
    items = Product.query.all()
    return jsonify(
        [
            {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "stock": product.stock,
                "image_url": product.image_url,
            }
            for product in items
        ]
    )


@products.route("/products", methods=["POST"])
@login_required
def create_product():
    data = request.get_json(silent=True) or {}
    error = validate_product_payload(data)
    if error:
        return jsonify({"message": error}), 400

    product = Product(
        name=data["name"],
        description=data.get("description"),
        price=float(data["price"]),
        stock=int(data.get("stock", 0)),
        image_url=data.get("image_url"),
    )
    db.session.add(product)
    db.session.commit()
    return jsonify({"message": "Product created"}), 201


@products.route("/products/<int:product_id>", methods=["PUT"])
@login_required
def update_product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"message": "Product not found"}), 404

    data = request.get_json(silent=True) or {}
    error = validate_product_payload(data, partial=True)
    if error:
        return jsonify({"message": error}), 400

    allowed_fields = {"name", "description", "price", "stock", "image_url"}
    for key, value in data.items():
        if key in allowed_fields:
            if key == "price":
                value = float(value)
            if key == "stock":
                value = int(value)
            setattr(product, key, value)

    db.session.commit()
    return jsonify({"message": "Product updated"}), 200


@products.route("/products/<int:product_id>", methods=["DELETE"])
@login_required
def delete_product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"message": "Product not found"}), 404

    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product deleted"}), 200

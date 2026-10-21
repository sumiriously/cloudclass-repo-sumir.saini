from flask import Blueprint, Response, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from app.catalog import get_all_products, get_categories, get_product_by_id, get_products_by_category
from app.models import ORDER_STATUSES, Order, Product, User, db
from app.orders import (
    can_view_order,
    email_is_admin,
    grant_order_access,
    load_order_receipt,
    place_order,
    set_order_status,
    storage_label,
    validate_customer,
    visible_orders,
)
from app.routes.auth import validate_credentials
from app.routes.products import validate_product_payload

web = Blueprint("web", __name__)
MAX_CART_QUANTITY = 20


@web.app_context_processor
def inject_cart_count():
    cart = session.get("cart") or {}
    return {"cart_count": sum(int(qty) for qty in cart.values())}


@web.route("/ui", methods=["GET"])
def ui_home():
    featured = [product for product in get_all_products() if product["in_stock"]][:3]
    return render_template("home.html", featured=featured)


@web.route("/ui/register", methods=["GET", "POST"])
def ui_register():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        error = validate_credentials(email, password)
        if error:
            flash(error, "error")
            return render_template("register.html", email=email), 400

        if User.query.filter_by(email=email).first():
            flash("Email already exists", "error")
            return render_template("register.html", email=email), 409

        user = User(
            email=email,
            password_hash=generate_password_hash(password),
            is_admin=email_is_admin(email),
        )
        db.session.add(user)
        db.session.commit()
        flash("Account created. Please log in.", "success")
        return redirect(url_for("web.ui_login"))

    return render_template("register.html")


@web.route("/ui/login", methods=["GET", "POST"])
def ui_login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        error = validate_credentials(email, password)
        if error:
            flash(error, "error")
            return render_template("login.html", email=email), 400

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid credentials", "error")
            return render_template("login.html", email=email), 401

        if email_is_admin(user.email) and not user.is_admin:
            user.is_admin = True
            db.session.commit()
        login_user(user)
        flash("Logged in successfully", "success")
        return redirect(url_for("web.ui_products"))

    return render_template("login.html")


@web.route("/ui/logout", methods=["POST"])
@login_required
def ui_logout():
    logout_user()
    flash("Logged out", "success")
    return redirect(url_for("web.ui_login"))


@web.route("/ui/products", methods=["GET"])
@login_required
def ui_products():
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template("products.html", products=products)


@web.route("/ui/products", methods=["POST"])
@login_required
def ui_add_product():
    data = {
        "name": (request.form.get("name") or "").strip(),
        "description": (request.form.get("description") or "").strip(),
        "price": request.form.get("price"),
        "stock": request.form.get("stock", "0"),
        "image_url": (request.form.get("image_url") or "").strip(),
    }
    error = validate_product_payload(data)
    if error:
        flash(error, "error")
        return redirect(url_for("web.ui_products"))

    product = Product(
        name=data["name"],
        description=data["description"] or None,
        price=float(data["price"]),
        stock=int(data["stock"] or 0),
        image_url=data["image_url"] or None,
    )
    db.session.add(product)
    db.session.commit()
    flash("Product added", "success")
    return redirect(url_for("web.ui_products"))


def _get_cart():
    return dict(session.get("cart") or {})


def _set_cart(cart):
    session["cart"] = cart
    session.modified = True


def _cart_items(cart=None):
    cart = _get_cart() if cart is None else cart
    items = []
    total = 0.0
    for product_id, quantity in cart.items():
        product = get_product_by_id(int(product_id))
        if not product:
            continue
        line_total = product["price"] * quantity
        total += line_total
        items.append({"product": product, "quantity": quantity, "line_total": line_total})
    return items, total


def _parse_quantity(raw_value):
    try:
        quantity = int(raw_value)
    except (TypeError, ValueError):
        return None
    if quantity < 1 or quantity > MAX_CART_QUANTITY:
        return None
    return quantity


@web.route("/ui/shop", methods=["GET"])
def ui_shop():
    category = (request.args.get("category") or "").strip()
    products = get_products_by_category(category)
    return render_template(
        "shop.html",
        products=products,
        categories=get_categories(),
        selected_category=category,
        title="Product Listing",
    )


@web.route("/ui/shop/<int:product_id>", methods=["GET"])
def ui_product_detail(product_id):
    product = get_product_by_id(product_id)
    if not product:
        flash("That product is not in the catalog.", "error")
        return redirect(url_for("web.ui_shop"))
    return render_template("product_detail.html", product=product, title=product["name"])


@web.route("/ui/cart", methods=["GET"])
def ui_cart():
    items, total = _cart_items()
    return render_template("cart.html", items=items, total=total, title="Cart")


@web.route("/ui/cart/add", methods=["POST"])
def ui_add_to_cart():
    product_id = request.form.get("product_id", type=int)
    product = get_product_by_id(product_id) if product_id else None
    if not product:
        flash("That product is not in the catalog.", "error")
        return redirect(url_for("web.ui_shop"))
    if not product["in_stock"]:
        flash(f"{product['name']} is currently out of stock.", "error")
        return redirect(url_for("web.ui_shop"))

    quantity = _parse_quantity(request.form.get("quantity", 1))
    if quantity is None:
        flash(f"Quantity must be between 1 and {MAX_CART_QUANTITY}.", "error")
        return redirect(url_for("web.ui_shop"))

    cart = _get_cart()
    key = str(product["id"])
    new_qty = min(cart.get(key, 0) + quantity, MAX_CART_QUANTITY)
    cart[key] = new_qty
    _set_cart(cart)
    flash(f"Added {product['name']} to your cart.", "success")
    return redirect(url_for("web.ui_cart"))


@web.route("/ui/cart/update", methods=["POST"])
def ui_update_cart():
    product_id = request.form.get("product_id", type=int)
    product = get_product_by_id(product_id) if product_id else None
    if not product:
        flash("That product is not in the catalog.", "error")
        return redirect(url_for("web.ui_cart"))

    quantity = _parse_quantity(request.form.get("quantity"))
    if quantity is None:
        flash(f"Quantity must be between 1 and {MAX_CART_QUANTITY}.", "error")
        return redirect(url_for("web.ui_cart"))

    cart = _get_cart()
    key = str(product["id"])
    if key not in cart:
        flash("That item is not in your cart.", "error")
        return redirect(url_for("web.ui_cart"))

    cart[key] = quantity
    _set_cart(cart)
    flash(f"Updated {product['name']} quantity.", "success")
    return redirect(url_for("web.ui_cart"))


@web.route("/ui/cart/remove", methods=["POST"])
def ui_remove_from_cart():
    product_id = request.form.get("product_id", type=int)
    cart = _get_cart()
    key = str(product_id) if product_id else ""
    product = get_product_by_id(product_id) if product_id else None
    if key in cart:
        cart.pop(key)
        _set_cart(cart)
        name = product["name"] if product else "Item"
        flash(f"Removed {name} from your cart.", "success")
    else:
        flash("That item is not in your cart.", "error")
    return redirect(url_for("web.ui_cart"))


@web.route("/ui/cart/clear", methods=["POST"])
def ui_clear_cart():
    session.pop("cart", None)
    flash("Cart cleared.", "success")
    return redirect(url_for("web.ui_cart"))


@web.route("/ui/checkout", methods=["GET", "POST"])
def ui_checkout():
    items, total = _cart_items()
    if not items:
        flash("Your cart is empty.", "error")
        return redirect(url_for("web.ui_cart"))

    if request.method == "POST":
        customer_name = request.form.get("customer_name") or ""
        email = request.form.get("email") or ""
        error = validate_customer(customer_name, email)
        if error:
            flash(error, "error")
            return render_template(
                "checkout.html",
                items=items,
                total=total,
                customer_name=customer_name.strip(),
                email=email.strip(),
                title="Checkout",
            ), 400

        order = place_order(
            customer_name=customer_name.strip(),
            email=email.strip(),
            cart_items=items,
            total=total,
            user_id=current_user.id if current_user.is_authenticated else None,
        )
        session.pop("cart", None)
        grant_order_access(order.id)
        flash("Order confirmed.", "success")
        return redirect(url_for("web.ui_order_detail", order_id=order.id, confirmed=1))

    email = current_user.email if current_user.is_authenticated else ""
    return render_template(
        "checkout.html",
        items=items,
        total=total,
        customer_name="",
        email=email,
        title="Checkout",
    )


def _order_or_redirect(order_id):
    order = db.session.get(Order, order_id)
    if order and can_view_order(order):
        return order, None
    flash("That order is not available.", "error")
    if current_user.is_authenticated:
        return None, redirect(url_for("web.ui_orders"))
    return None, redirect(url_for("web.ui_login"))


@web.route("/ui/orders", methods=["GET"])
@login_required
def ui_orders():
    selected = (request.args.get("status") or "").strip()
    if selected not in ORDER_STATUSES:
        selected = ""
    return render_template(
        "orders.html",
        orders=visible_orders(selected or None),
        statuses=ORDER_STATUSES,
        selected_status=selected,
        title="Orders",
    )


@web.route("/ui/orders/<int:order_id>", methods=["GET"])
def ui_order_detail(order_id):
    order, response = _order_or_redirect(order_id)
    if response:
        return response
    return render_template(
        "order_detail.html",
        order=order,
        statuses=ORDER_STATUSES,
        confirmed=request.args.get("confirmed") == "1",
        storage_label=storage_label(order.receipt_storage),
        title=f"Order #{order.id}",
    )


@web.route("/ui/orders/<int:order_id>/status", methods=["POST"])
@login_required
def ui_update_order_status(order_id):
    order = db.session.get(Order, order_id)
    if not order or not can_view_order(order):
        flash("That order is not available.", "error")
        return redirect(url_for("web.ui_orders"))
    if not current_user.is_admin:
        flash("Only shop staff can update order status.", "error")
        return redirect(url_for("web.ui_order_detail", order_id=order.id))

    status = (request.form.get("status") or "").strip()
    if not set_order_status(order, status):
        flash("Choose a valid order status.", "error")
        return redirect(url_for("web.ui_order_detail", order_id=order.id))

    flash(f"Order #{order.id} marked {status}.", "success")
    return redirect(url_for("web.ui_order_detail", order_id=order.id))


@web.route("/ui/orders/<int:order_id>/receipt", methods=["GET"])
def ui_order_receipt(order_id):
    order, response = _order_or_redirect(order_id)
    if response:
        return response
    body = load_order_receipt(order)
    if body is None:
        flash("The receipt for this order is not available.", "error")
        return redirect(url_for("web.ui_order_detail", order_id=order.id))
    response = Response(body, mimetype="text/plain")
    response.headers["Content-Disposition"] = f'attachment; filename="order-{order.id}.txt"'
    return response

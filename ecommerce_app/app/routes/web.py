from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from app.models import Product, User, db
from app.routes.auth import validate_credentials
from app.routes.products import validate_product_payload

web = Blueprint("web", __name__)


@web.route("/ui", methods=["GET"])
def ui_home():
    return render_template("home.html")


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

        user = User(email=email, password_hash=generate_password_hash(password))
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

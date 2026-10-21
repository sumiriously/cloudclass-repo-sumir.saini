from datetime import datetime

from flask import current_app, session
from flask_login import current_user

from app.models import ORDER_STATUSES, Order, OrderItem, db
from app.routes.auth import EMAIL_RE
from app.spaces import read_receipt, spaces_configured, storage_label, store_receipt


def validate_customer(name, email):
    name = (name or "").strip()
    email = (email or "").strip()
    if not name or len(name) > 120:
        return "Name is required and must be 120 characters or fewer."
    if not EMAIL_RE.match(email):
        return "A valid email is required so this order can be tracked."
    return None


def email_is_admin(email):
    admin_email = (current_app.config.get("ADMIN_EMAIL") or "").strip().lower()
    return bool(email) and bool(admin_email) and email.strip().lower() == admin_email


def place_order(customer_name, email, cart_items, total, user_id=None):
    now = datetime.utcnow()
    order = Order(
        user_id=user_id,
        customer_name=customer_name,
        email=email,
        status="placed",
        total=total,
        created_at=now,
        updated_at=now,
    )
    for item in cart_items:
        product = item["product"]
        order.items.append(
            OrderItem(
                product_id=product["id"],
                product_name=product["name"],
                emoji=product.get("emoji"),
                unit_price=product["price"],
                quantity=item["quantity"],
                line_total=item["line_total"],
            )
        )
    db.session.add(order)
    db.session.flush()

    planned = "spaces" if spaces_configured() else "local"
    body = render_receipt(order, storage_label(planned)).encode("utf-8")
    storage, key = store_receipt(order.id, body)
    if storage != planned:
        body = render_receipt(order, storage_label(storage)).encode("utf-8")
        storage, key = store_receipt(order.id, body)
    order.receipt_storage = storage
    order.receipt_key = key
    db.session.commit()
    return order


def render_receipt(order, storage_name):
    lines = [
        "Tiki Surf Shop",
        f"Order #{order.id}",
        f"Status: {order.status}",
        f"Customer: {order.customer_name} <{order.email}>",
        f"Placed: {order.created_at:%Y-%m-%d %H:%M} UTC",
        "",
        "Items:",
    ]
    for item in order.items:
        lines.append(
            f"- {item.product_name} x {item.quantity} @ ${item.unit_price:.2f} = ${item.line_total:.2f}"
        )
    lines.extend(
        [
            "",
            f"Total: ${order.total:.2f}",
            f"Receipt storage: {storage_name}",
            "",
            "Practice order. No payment was collected.",
        ]
    )
    return "\n".join(lines) + "\n"


def grant_order_access(order_id):
    ids = [int(value) for value in session.get("order_ids", [])]
    if order_id not in ids:
        ids.append(order_id)
    session["order_ids"] = ids
    session.modified = True


def can_view_order(order):
    if current_user.is_authenticated:
        if current_user.is_admin:
            return True
        if order.user_id == current_user.id:
            return True
        return order.email.lower() == (current_user.email or "").lower()
    allowed = {int(value) for value in session.get("order_ids", [])}
    return order.id in allowed


def visible_orders(status=None):
    query = Order.query.order_by(Order.created_at.desc())
    if not current_user.is_admin:
        email = (current_user.email or "").lower()
        query = query.filter(db.or_(Order.user_id == current_user.id, db.func.lower(Order.email) == email))
    if status in ORDER_STATUSES:
        query = query.filter(Order.status == status)
    return query.all()


def set_order_status(order, status):
    if status not in ORDER_STATUSES:
        return False
    order.status = status
    order.updated_at = datetime.utcnow()
    db.session.commit()
    return True


def load_order_receipt(order):
    body = read_receipt(order.receipt_storage, order.receipt_key)
    if body is None:
        return None
    return body.decode("utf-8", errors="replace")

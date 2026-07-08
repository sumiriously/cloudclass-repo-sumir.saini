import logging

from flask import Flask, jsonify
from flask_login import LoginManager
from flask_migrate import Migrate
from werkzeug.exceptions import HTTPException

from config import Config

from .models import User, db

login_manager = LoginManager()
migrate = Migrate()


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.logger.setLevel(logging.INFO)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    login_manager.login_view = None

    from .routes.auth import auth
    from .routes.products import products

    app.register_blueprint(auth)
    app.register_blueprint(products)

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"}), 200

    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response

    @login_manager.unauthorized_handler
    def unauthorized():
        return jsonify({"message": "Authentication required"}), 401

    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        return jsonify({"message": err.description}), err.code

    @app.errorhandler(Exception)
    def handle_unexpected_exception(err):
        app.logger.exception("Unhandled exception: %s", err)
        return jsonify({"message": "Internal server error"}), 500

    return app

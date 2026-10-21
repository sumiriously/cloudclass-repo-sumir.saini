import os

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///ecommerce.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "")
    SPACES_KEY = os.environ.get("SPACES_KEY", "")
    SPACES_SECRET = os.environ.get("SPACES_SECRET", "")
    SPACES_BUCKET = os.environ.get("SPACES_BUCKET", "")
    SPACES_REGION = os.environ.get("SPACES_REGION", "")
    SPACES_ENDPOINT = os.environ.get("SPACES_ENDPOINT", "")
    RECEIPT_DIR = os.environ.get("RECEIPT_DIR", os.path.join(BASE_DIR, "instance", "receipts"))

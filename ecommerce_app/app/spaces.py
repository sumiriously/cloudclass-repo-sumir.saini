"""Order receipt storage.

DigitalOcean Spaces is S3-compatible. When Spaces credentials are configured,
receipts are uploaded there. Otherwise they are written under RECEIPT_DIR so
local development and tests still keep a copy of every order.
"""

from pathlib import Path

from flask import current_app


def spaces_configured():
    config = current_app.config
    return all(config.get(name) for name in ("SPACES_KEY", "SPACES_SECRET", "SPACES_BUCKET", "SPACES_REGION"))


def receipt_key_for(order_id):
    return f"orders/order-{int(order_id)}.txt"


def storage_label(storage):
    if storage == "spaces":
        region = (current_app.config.get("SPACES_REGION") or "").strip()
        if region:
            return f"DigitalOcean Spaces ({region})"
        return "DigitalOcean Spaces"
    if storage == "local":
        return "local storage"
    return "not stored"


def store_receipt(order_id, body):
    key = receipt_key_for(order_id)
    if spaces_configured():
        try:
            _put_spaces(key, body)
            return "spaces", key
        except Exception:
            current_app.logger.exception("DigitalOcean Spaces upload failed; saving the receipt locally")
    _write_local(key, body)
    return "local", key


def read_receipt(storage, key):
    if not key:
        return None
    if storage == "spaces" and spaces_configured():
        try:
            return _get_spaces(key)
        except Exception:
            current_app.logger.exception("DigitalOcean Spaces download failed; trying local receipt")
    return _read_local(key)


def _spaces_client():
    import boto3

    region = current_app.config["SPACES_REGION"]
    endpoint = (current_app.config.get("SPACES_ENDPOINT") or "").strip()
    if not endpoint:
        endpoint = f"https://{region}.digitaloceanspaces.com"
    session = boto3.session.Session()
    return session.client(
        "s3",
        region_name=region,
        endpoint_url=endpoint,
        aws_access_key_id=current_app.config["SPACES_KEY"],
        aws_secret_access_key=current_app.config["SPACES_SECRET"],
    )


def _put_spaces(key, body):
    _spaces_client().put_object(
        Bucket=current_app.config["SPACES_BUCKET"],
        Key=key,
        Body=body,
        ContentType="text/plain; charset=utf-8",
        ACL="private",
    )


def _get_spaces(key):
    response = _spaces_client().get_object(Bucket=current_app.config["SPACES_BUCKET"], Key=key)
    return response["Body"].read()


def _local_path(key):
    root = Path(current_app.config["RECEIPT_DIR"]).resolve()
    path = (root / key).resolve()
    if path != root and root not in path.parents:
        raise ValueError("Invalid receipt path")
    return path


def _write_local(key, body):
    path = _local_path(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)


def _read_local(key):
    path = _local_path(key)
    if not path.is_file():
        return None
    return path.read_bytes()

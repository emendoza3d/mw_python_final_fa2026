"""CSV storage helpers for the ring-studio demo."""

import csv
from datetime import datetime, timezone
import hashlib
import hmac
import os
from pathlib import Path
import tempfile
from typing import Any
from uuid import uuid4

DATA_DIR = Path(__file__).resolve().parent
CUSTOMERS_FILE = DATA_DIR / "customers.csv"
ORDERS_FILE = DATA_DIR / "orders.csv"

CUSTOMER_FIELDS = ("email", "name", "created_at", "password_hash")
ORDER_FIELDS = (
    "order_id",
    "customer_email",
    "created_at",
    "shape",
    "style",
    "metal",
    "diamond",
    "status",
)
PASSWORD_ITERATIONS = 600_000


def _read_records(
    path: Path,
    fields: tuple[str, ...],
    optional_fields: tuple[str, ...] = (),
) -> list[dict[str, str]]:
    if not path.exists():
        return []

    with path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            return []
        missing_fields = set(fields).difference(reader.fieldnames, optional_fields)
        if missing_fields:
            missing = ", ".join(sorted(missing_fields))
            raise ValueError(f"{path.name} is missing required columns: {missing}")
        return [
            {field: row.get(field, "") or "" for field in fields}
            for row in reader
        ]


def _replace_records(
    path: Path, fields: tuple[str, ...], records: list[dict[str, str]]
) -> None:
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            newline="",
            encoding="utf-8",
            dir=path.parent,
            delete=False,
        ) as file:
            temporary_path = Path(file.name)
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            writer.writerows(
                {field: record.get(field, "") for field in fields}
                for record in records
            )
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def _append_record(
    path: Path,
    fields: tuple[str, ...],
    record: dict[str, str],
    optional_fields: tuple[str, ...] = (),
) -> None:
    write_header = not path.exists() or path.stat().st_size == 0
    if not write_header:
        with path.open("r", newline="", encoding="utf-8") as file:
            existing_fields = csv.DictReader(file).fieldnames or []
        if tuple(existing_fields) != fields:
            existing_records = _read_records(
                path, fields, optional_fields=optional_fields
            )
            _replace_records(path, fields, existing_records)
    with path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        if write_header:
            writer.writeheader()
        writer.writerow({field: record.get(field, "") for field in fields})


def get_customer(email: str) -> dict[str, str] | None:
    normalized_email = email.strip().casefold()
    return next(
        (
            customer
            for customer in _read_records(
                CUSTOMERS_FILE,
                CUSTOMER_FIELDS,
                optional_fields=("password_hash",),
            )
            if customer["email"].casefold() == normalized_email
        ),
        None,
    )


def _make_password_hash(password: str) -> str:
    salt = os.urandom(16)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
    )
    return f"pbkdf2_sha256${salt.hex()}${derived_key.hex()}"


def _password_matches(password: str, stored_hash: str) -> bool:
    try:
        algorithm, salt_hex, expected_hash = stored_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(expected_hash)
    except ValueError:
        return False

    actual = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
    )
    return hmac.compare_digest(actual, expected)


def register_customer(
    email: str, name: str, password: str
) -> dict[str, str]:
    normalized_email = email.strip().casefold()
    if get_customer(normalized_email) is not None:
        raise ValueError("An account or legacy profile already uses this email.")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")
    if not name.strip():
        raise ValueError("Enter your name to create an account.")

    customer = {
        "email": normalized_email,
        "name": name.strip(),
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "password_hash": _make_password_hash(password),
    }
    _append_record(
        CUSTOMERS_FILE,
        CUSTOMER_FIELDS,
        customer,
        optional_fields=("password_hash",),
    )
    return customer


def authenticate_customer(email: str, password: str) -> dict[str, str] | None:
    customer = get_customer(email)
    if (
        customer is None
        or not customer["password_hash"]
        or not _password_matches(password, customer["password_hash"])
    ):
        return None
    return customer


def create_order(
    customer_email: str,
    selections: dict[str, str],
) -> dict[str, str]:
    order = {
        "order_id": uuid4().hex[:10].upper(),
        "customer_email": customer_email.strip().casefold(),
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "shape": selections["shape"],
        "style": selections["style"],
        "metal": selections["metal"],
        "diamond": selections["diamond"],
        "status": "concept",
    }
    _append_record(
        ORDERS_FILE,
        ORDER_FIELDS,
        order,
        optional_fields=("status",),
    )
    return order


def get_customer_orders(email: str) -> list[dict[str, str]]:
    normalized_email = email.strip().casefold()
    orders = [
        order
        for order in _read_records(
            ORDERS_FILE,
            ORDER_FIELDS,
            optional_fields=("status",),
        )
        if order["customer_email"].casefold() == normalized_email
    ]
    for order in orders:
        if not order["status"]:
            order["status"] = "concept"
    return sorted(orders, key=lambda order: order["created_at"], reverse=True)


def update_order(
    order_id: str,
    customer_email: str,
    selections: dict[str, str],
) -> bool:
    normalized_email = customer_email.strip().casefold()
    orders = _read_records(
        ORDERS_FILE,
        ORDER_FIELDS,
        optional_fields=("status",),
    )
    for order in orders:
        if (
            order["order_id"] == order_id
            and order["customer_email"].casefold() == normalized_email
        ):
            if order["status"] == "finalized":
                return False
            for field in ("shape", "style", "metal", "diamond"):
                order[field] = selections[field]
            order["status"] = order["status"] or "concept"
            _replace_records(ORDERS_FILE, ORDER_FIELDS, orders)
            return True
    return False


def finalize_order(order_id: str, customer_email: str) -> bool:
    normalized_email = customer_email.strip().casefold()
    orders = _read_records(
        ORDERS_FILE,
        ORDER_FIELDS,
        optional_fields=("status",),
    )
    for order in orders:
        if (
            order["order_id"] == order_id
            and order["customer_email"].casefold() == normalized_email
        ):
            if order["status"] == "finalized":
                return False
            order["status"] = "finalized"
            _replace_records(ORDERS_FILE, ORDER_FIELDS, orders)
            return True
    return False


def get_order_summary(order: dict[str, Any]) -> str:
    return (
        f"{order['shape']} {order['style']} ring in {order['metal']} "
        f"with a {order['diamond']} diamond"
    )

"""CSV storage helpers for the ring-studio demo."""

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

DATA_DIR = Path(__file__).resolve().parent
CUSTOMERS_FILE = DATA_DIR / "customers.csv"
ORDERS_FILE = DATA_DIR / "orders.csv"

CUSTOMER_FIELDS = ("email", "name", "created_at")
ORDER_FIELDS = (
    "order_id",
    "customer_email",
    "created_at",
    "shape",
    "style",
    "metal",
    "diamond",
)


def _read_records(path: Path, fields: tuple[str, ...]) -> list[dict[str, str]]:
    if not path.exists():
        return []

    with path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            return []
        missing_fields = set(fields).difference(reader.fieldnames)
        if missing_fields:
            missing = ", ".join(sorted(missing_fields))
            raise ValueError(f"{path.name} is missing required columns: {missing}")
        return [
            {field: row.get(field, "") or "" for field in fields}
            for row in reader
        ]


def _append_record(
    path: Path, fields: tuple[str, ...], record: dict[str, str]
) -> None:
    write_header = not path.exists() or path.stat().st_size == 0
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
            for customer in _read_records(CUSTOMERS_FILE, CUSTOMER_FIELDS)
            if customer["email"].casefold() == normalized_email
        ),
        None,
    )


def get_or_create_customer(email: str, name: str) -> tuple[dict[str, str], bool]:
    normalized_email = email.strip().casefold()
    existing = get_customer(normalized_email)
    if existing is not None:
        return existing, False

    customer = {
        "email": normalized_email,
        "name": name.strip(),
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    _append_record(CUSTOMERS_FILE, CUSTOMER_FIELDS, customer)
    return customer, True


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
    }
    _append_record(ORDERS_FILE, ORDER_FIELDS, order)
    return order


def get_customer_orders(email: str) -> list[dict[str, str]]:
    normalized_email = email.strip().casefold()
    orders = [
        order
        for order in _read_records(ORDERS_FILE, ORDER_FIELDS)
        if order["customer_email"].casefold() == normalized_email
    ]
    return sorted(orders, key=lambda order: order["created_at"], reverse=True)


def get_order_summary(order: dict[str, Any]) -> str:
    return (
        f"{order['shape']} {order['style']} ring in {order['metal']} "
        f"with a {order['diamond']} diamond"
    )

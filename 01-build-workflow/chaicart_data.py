"""Fake ChaiCart back-office data used by every sample in this module.

In a real system these lookups would call your order database and courier API.
Keeping them as plain Python makes the workflow easy to test without any cloud access.
"""

from __future__ import annotations

ORDERS: dict[str, dict] = {
    "A1029": {"status": "delivered", "days_since_delivery": 2, "total_inr": 640, "items": ["Glass teapot"]},
    "A1030": {"status": "in_transit", "days_since_dispatch": 6, "total_inr": 1250, "items": ["Assam 500g", "Masala chai 250g"]},
    "A1031": {"status": "delivered", "days_since_delivery": 1, "total_inr": 4800, "items": ["Tea gift hamper"]},
    "A1032": {"status": "delivered", "days_since_delivery": 20, "total_inr": 300, "items": ["Green tea 100g"]},
}

COURIER: dict[str, str] = {
    "A1030": "Stuck at Pune hub since Monday. New ETA: 2 days.",
}

# Business rules live in code, not in a prompt.
REFUND_WINDOW_DAYS = 7
AUTO_APPROVE_LIMIT_INR = 1000  # refunds above this need a human


def get_order(order_id: str | None) -> dict | None:
    """Return the order record, or None if the ID is missing or unknown."""
    if not order_id:
        return None
    return ORDERS.get(order_id.strip().upper())


def courier_status(order_id: str) -> str:
    """Return the latest courier update for an order."""
    return COURIER.get(order_id.strip().upper(), "No courier issues reported.")

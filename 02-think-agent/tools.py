"""ChaiCart tools the support agent can call (Module 02 · Think).

Read tools run freely. The one write tool, ``issue_refund``, is marked
``approval_mode="always_require"``: the agent can ask to call it, but the call
only happens after a person approves it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import Field

from agent_framework import tool

ORDERS: dict[str, dict] = {
    "A1029": {"status": "delivered", "days_since_delivery": 2, "total_inr": 640, "items": ["Glass teapot"]},
    "A1030": {"status": "in_transit", "days_since_dispatch": 6, "total_inr": 1250, "items": ["Assam 500g"]},
    "A1031": {"status": "delivered", "days_since_delivery": 1, "total_inr": 4800, "items": ["Tea gift hamper"]},
}
COURIER = {"A1030": "Stuck at Pune hub since Monday. New ETA: 2 days."}
POLICY_FILE = Path(__file__).parent / "knowledge" / "refund-policy.md"

REFUND_LOG: list[dict] = []  # stands in for a payments system in this sample


@tool
def get_order(order_id: Annotated[str, Field(description="ChaiCart order ID, for example A1029")]) -> dict:
    """Look up an order's status, items, total (in rupees) and days since delivery."""
    order = ORDERS.get(order_id.strip().upper())
    return order if order else {"error": f"No order found with ID {order_id}"}


@tool
def courier_status(order_id: Annotated[str, Field(description="ChaiCart order ID")]) -> str:
    """Get the latest courier update for an order that hasn't arrived yet."""
    return COURIER.get(order_id.strip().upper(), "No courier issues reported.")


@tool
def search_refund_policy(question: Annotated[str, Field(description="What you need to know about refunds")]) -> str:
    """Search ChaiCart's refund policy. Always check it before deciding on a refund."""
    rules = [line for line in POLICY_FILE.read_text(encoding="utf-8").splitlines() if line[:1].isdigit()]
    words = {w for w in question.lower().split() if len(w) > 3}
    ranked = sorted(rules, key=lambda r: -sum(w in r.lower() for w in words))
    return "\n".join(ranked[:3]) if words else "\n".join(rules)


@tool(approval_mode="always_require")
def issue_refund(
    order_id: Annotated[str, Field(description="ChaiCart order ID")],
    amount_inr: Annotated[int, Field(description="Refund amount in rupees")],
    reason: Annotated[str, Field(description="Short reason for the refund")],
) -> str:
    """Issue a refund to the customer. A person must approve this before it runs."""
    REFUND_LOG.append({"order_id": order_id, "amount_inr": amount_inr, "reason": reason})
    return f"Refund of Rs {amount_inr} issued for order {order_id}."


ALL_TOOLS = [get_order, courier_status, search_refund_policy, issue_refund]

"""ChaiCart Orders MCP server (Module 03 · Extend).

Wraps ChaiCart's (fake) order system as MCP tools, so any MCP client can use them:
GitHub Copilot in VS Code, a Foundry agent, Agent Framework or your own app.

    python server.py                 # stdio, for VS Code / GitHub Copilot
    python server.py --http          # Streamable HTTP on http://127.0.0.1:8000/mcp

Written for the MCP Python SDK 2.x, where FastMCP was renamed to MCPServer.
"""

from __future__ import annotations

import sys
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

mcp = MCPServer(
    "chaicart-orders",
    instructions="Tools for ChaiCart customer support: look up orders, check couriers, and queue refunds for approval.",
)

ORDERS: dict[str, dict] = {
    "A1029": {"status": "delivered", "days_since_delivery": 2, "total_inr": 640, "items": ["Glass teapot"]},
    "A1030": {"status": "in_transit", "days_since_dispatch": 6, "total_inr": 1250, "items": ["Assam 500g"]},
    "A1031": {"status": "delivered", "days_since_delivery": 1, "total_inr": 4800, "items": ["Tea gift hamper"]},
}
COURIER = {"A1030": "Stuck at Pune hub since Monday. New ETA: 2 days."}
PENDING_REFUNDS: list[dict] = []


class Order(BaseModel):
    order_id: str
    status: Literal["delivered", "in_transit", "cancelled"]
    total_inr: int
    items: list[str]
    days_since_delivery: int | None = None


class RefundRequest(BaseModel):
    order_id: str
    amount_inr: int
    reason: str
    status: Literal["pending_approval"] = "pending_approval"


def _find(order_id: str) -> dict:
    order = ORDERS.get(order_id.strip().upper())
    if order is None:
        # ToolError: the model sees this message and can recover (for example, ask for the ID again).
        raise ToolError(f"No order found with ID '{order_id}'. Ask the customer to check the ID.")
    return order


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def get_order(order_id: Annotated[str, Field(description="ChaiCart order ID, for example A1029")]) -> Order:
    """Status, items and total (in rupees) for one ChaiCart order."""
    order = _find(order_id)
    return Order(order_id=order_id.strip().upper(), **order)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def courier_status(order_id: Annotated[str, Field(description="ChaiCart order ID")]) -> str:
    """Latest courier update for an order that hasn't arrived yet."""
    _find(order_id)
    return COURIER.get(order_id.strip().upper(), "No courier issues reported.")


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False))
async def issue_refund(
    order_id: Annotated[str, Field(description="ChaiCart order ID")],
    amount_inr: Annotated[int, Field(gt=0, description="Refund amount in rupees")],
    reason: Annotated[str, Field(min_length=3, description="Short reason, for example 'arrived broken'")],
) -> RefundRequest:
    """Queue a refund. It is NOT paid until a person approves it in the back office."""
    order = _find(order_id)
    if amount_inr > order["total_inr"]:
        raise ToolError(f"Refund Rs {amount_inr} is more than the order total Rs {order['total_inr']}.")
    request = RefundRequest(order_id=order_id.strip().upper(), amount_inr=amount_inr, reason=reason)
    PENDING_REFUNDS.append(request.model_dump())
    return request


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def list_pending_refunds() -> list[RefundRequest]:
    """Refunds waiting for a manager's approval."""
    return [RefundRequest(**r) for r in PENDING_REFUNDS]


if __name__ == "__main__":
    if "--http" in sys.argv:
        mcp.run(transport="streamable-http", host="127.0.0.1", port=8000)
    else:
        mcp.run()  # stdio

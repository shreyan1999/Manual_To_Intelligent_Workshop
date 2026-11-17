"""Tests the MCP server in-process with the SDK's Client, exactly as an MCP host would call it."""

from __future__ import annotations

import pytest

from mcp import Client

import server


@pytest.fixture(autouse=True)
def reset():
    server.PENDING_REFUNDS.clear()


async def test_lists_all_four_tools_with_descriptions():
    async with Client(server.mcp) as client:
        tools = {t.name: t for t in (await client.list_tools()).tools}
    assert set(tools) == {"get_order", "courier_status", "issue_refund", "list_pending_refunds"}
    assert "approves" in tools["issue_refund"].description  # the model reads this to decide when to call
    assert tools["get_order"].annotations.read_only_hint is True


async def test_get_order_returns_structured_data():
    async with Client(server.mcp) as client:
        result = await client.call_tool("get_order", {"order_id": "a1029"})
    assert not result.is_error
    assert result.structured_content["total_inr"] == 640
    assert result.structured_content["order_id"] == "A1029"


async def test_unknown_order_is_a_tool_error_the_model_can_read():
    async with Client(server.mcp) as client:
        result = await client.call_tool("get_order", {"order_id": "Z999"})
    assert result.is_error
    assert "No order found" in result.content[0].text


async def test_refund_is_queued_not_paid():
    async with Client(server.mcp) as client:
        result = await client.call_tool("issue_refund", {"order_id": "A1031", "amount_inr": 4800, "reason": "hamper crushed"})
        pending = await client.call_tool("list_pending_refunds", {})
    assert result.structured_content["status"] == "pending_approval"
    assert pending.structured_content["result"][0]["order_id"] == "A1031"


async def test_refund_above_order_total_is_rejected():
    async with Client(server.mcp) as client:
        result = await client.call_tool("issue_refund", {"order_id": "A1029", "amount_inr": 9999, "reason": "test"})
    assert result.is_error
    assert server.PENDING_REFUNDS == []


async def test_invalid_arguments_are_rejected_by_the_schema():
    async with Client(server.mcp) as client:
        result = await client.call_tool("issue_refund", {"order_id": "A1029", "amount_inr": -5, "reason": "x"})
    assert result.is_error


async def test_courier_status():
    async with Client(server.mcp) as client:
        result = await client.call_tool("courier_status", {"order_id": "A1030"})
    assert "Pune hub" in result.content[0].text


async def test_runs_over_stdio_like_vs_code_starts_it():
    """Launch server.py as a subprocess, the way .vscode/mcp.json does."""
    import sys
    from pathlib import Path

    from mcp import StdioServerParameters

    params = StdioServerParameters(command=sys.executable, args=[str(Path(server.__file__))])
    async with Client(params) as client:
        result = await client.call_tool("get_order", {"order_id": "A1030"})
    assert result.structured_content["status"] == "in_transit"

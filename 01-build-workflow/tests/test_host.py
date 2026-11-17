"""Calls the hosted workflow over the Responses protocol, in-process (no network, fake agents)."""

from __future__ import annotations

import json

import httpx
import pytest

from host import make_server
from test_workflow import FakeReplyAgent, FakeTriageAgent


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # the local host keeps its response store in the working folder
    app = make_server(FakeTriageAgent(), FakeReplyAgent())
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


def _message_text(response):
    return next(
        part["text"]
        for item in response["output"]
        if item["type"] == "message"
        for part in item["content"]
        if part["type"] == "output_text"
    )


def _ticket(response):
    return next(item["output"] for item in response["output"] if item["type"] == "structured_outputs")


@pytest.mark.asyncio
async def test_delivery_email_completes(client):
    async with client:
        r = (await client.post("/responses", json={"input": "Where is order A1030? It should arrive by now"})).json()
    assert r["status"] == "completed"
    assert "Pune hub" in _message_text(r)  # visible chat reply
    assert "Pune hub" in _ticket(r)["decision"]


@pytest.mark.asyncio
@pytest.mark.parametrize("approve", [True, False], ids=["approve", "reject"])
@pytest.mark.parametrize("stream", [False, True], ids=["json", "inspector-stream"])
async def test_refund_approval_round_trip(client, approve, stream):
    async def post_response(payload):
        response = await client.post("/responses", json={**payload, "stream": stream})
        assert response.status_code == 200, response.text
        if not stream:
            return response.json()
        events = [
            json.loads(line.removeprefix("data: "))
            for line in response.text.splitlines()
            if line.startswith("data: ") and line != "data: [DONE]"
        ]
        completed = [event["response"] for event in events if event["type"] == "response.completed"]
        assert len(completed) == 1, response.text
        return completed[0]

    async with client:
        first = await post_response({"input": "Order A1031 hamper crushed. I want my money back."})
        call = first["output"][0]
        assert call["type"] == "mcp_approval_request" and call["name"] == "approve_refund"
        arguments = json.loads(call["arguments"])
        assert arguments["order_id"] == "A1031"
        assert arguments["amount_inr"] == 4800

        second = await post_response({
            "previous_response_id": first["id"],
            "agent_session_id": first["agent_session_id"],
            "input": [{"type": "mcp_approval_response", "approval_request_id": call["id"], "approve": approve}],
        })
    assert second["status"] == "completed"
    ticket = _ticket(second)
    expected = "approved by a manager" if approve else "replacement"
    assert expected in ticket["decision"]
    assert expected in _message_text(second)  # visible chat reply
    assert ticket["log"][-1] == "send_and_log: sent"

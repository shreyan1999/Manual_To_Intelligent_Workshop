"""Calls the hosted workflow over the Responses protocol, in-process (no network, fake agents)."""

from __future__ import annotations

import httpx
import pytest

from host import make_server
from test_workflow import FakeReplyAgent, FakeTriageAgent


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # the local host keeps its response store in the working folder
    app = make_server(FakeTriageAgent(), FakeReplyAgent())
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_delivery_email_completes(client):
    async with client:
        r = (await client.post("/responses", json={"input": "Where is order A1030? It should arrive by now"})).json()
    assert r["status"] == "completed"
    assert "Pune hub" in r["output"][0]["output"]["decision"]


@pytest.mark.asyncio
async def test_refund_approval_round_trip(client):
    async with client:
        first = (await client.post("/responses", json={"input": "Order A1031 hamper crushed. I want my money back."})).json()
        call = first["output"][0]
        assert call["type"] == "function_call" and call["name"] == "request_info"

        second = (
            await client.post(
                "/responses",
                json={
                    "previous_response_id": first["id"],
                    "agent_session_id": first["agent_session_id"],
                    "input": [{"type": "function_call_output", "call_id": call["call_id"], "output": "true"}],
                },
            )
        ).json()
    assert second["status"] == "completed"
    assert "approved by a manager" in second["output"][0]["output"]["decision"]

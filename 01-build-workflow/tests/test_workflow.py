"""Offline tests: fake agents stand in for Foundry, so no Azure account is needed."""

from __future__ import annotations

import json
import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

import main as cli
from workflow import RefundApprovalRequest, Ticket, build_workflow


class FakeTriageAgent:
    """Keyword-based stand-in for the triage agent. Returns JSON text like a real model."""

    async def run(self, messages, **kwargs):
        text = str(messages).lower()
        match = re.search(r"\b(a\d{4})\b", text)
        if "refund" in text or "money back" in text:
            intent = "refund"
        elif "where is" in text or "arrive" in text:
            intent = "delivery"
        else:
            intent = "feedback"
        payload = {"intent": intent, "order_id": match.group(1).upper() if match else None, "sentiment": "neutral"}
        return SimpleNamespace(text=json.dumps(payload), value=None)


class FakeReplyAgent:
    async def run(self, messages, **kwargs):
        decision = str(messages).split("Decision to communicate:\n", 1)[-1]
        return SimpleNamespace(text=json.dumps({"reply": f"Dear customer, {decision}"}), value=None)


async def run_to_end(email: str, approve: bool | None = None):
    workflow = build_workflow(FakeTriageAgent(), FakeReplyAgent())
    requests, outputs = [], []
    async for event in workflow.run(email, stream=True):
        if event.type == "request_info":
            requests.append(event)
        elif event.type == "output" and isinstance(event.data, Ticket):
            outputs.append(event.data)
    if requests and approve is not None:
        responses = {e.request_id: e.data.to_function_approval_response(approve) for e in requests}
        async for event in workflow.run(stream=True, responses=responses):
            if event.type == "output" and isinstance(event.data, Ticket):
                outputs.append(event.data)
    return requests, outputs


@pytest.mark.asyncio
async def test_small_refund_is_auto_approved():
    requests, outputs = await run_to_end("Order A1029 arrived broken, refund please")
    assert requests == []
    ticket: Ticket = outputs[0]
    assert ticket.intent == "refund"
    assert "approved automatically" in ticket.decision
    assert ticket.reply.startswith("Dear customer")


@pytest.mark.asyncio
async def test_large_refund_pauses_for_a_human_and_resumes():
    requests, outputs = await run_to_end("Hamper in order A1031 was crushed. I want my money back.", approve=True)
    assert len(requests) == 1
    assert requests[0].data.type == "function_approval_request"
    assert RefundApprovalRequest.from_content(requests[0].data).amount_inr == 4800
    assert "approved by a manager" in outputs[0].decision
    assert outputs[0].log[-1] == "send_and_log: sent"


@pytest.mark.asyncio
async def test_rejected_refund_offers_replacement():
    _, outputs = await run_to_end("Hamper in order A1031 was crushed. I want my money back.", approve=False)
    assert "replacement" in outputs[0].decision


@pytest.mark.asyncio
async def test_refund_outside_window_is_declined_by_code():
    _, outputs = await run_to_end("Refund for order A1032 please")
    assert "not possible" in outputs[0].decision


@pytest.mark.asyncio
async def test_delivery_question_uses_courier_status():
    _, outputs = await run_to_end("Where is order A1030? It should arrive by now")
    assert "Pune hub" in outputs[0].decision


@pytest.mark.asyncio
async def test_feedback_goes_straight_to_reply():
    _, outputs = await run_to_end("Love the masala chai!")
    assert outputs[0].intent == "feedback"
    assert "send_and_log: sent" in outputs[0].log


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("answer", "decision"), [("y", "approved by a manager"), ("n", "replacement")]
)
async def test_terminal_refund_approval(monkeypatch, answer, decision):
    monkeypatch.setattr("builtins.input", lambda prompt: answer)
    workflow = build_workflow(FakeTriageAgent(), FakeReplyAgent())

    ticket = await cli.run_one(workflow, "Order A1031 hamper crushed. I want my money back.")

    assert ticket is not None
    assert decision in ticket.decision
    assert ticket.log[-1] == "send_and_log: sent"


@pytest.mark.asyncio
@pytest.mark.parametrize("args", [[], ["Where is order A1030?"]], ids=["sample-emails", "custom-email"])
async def test_cli_loads_emails_from_another_directory(tmp_path, monkeypatch, args):
    expected = args or json.loads(
        Path(cli.__file__).with_name("sample_emails.json").read_text(encoding="utf-8")
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli.sys, "argv", ["main.py", *args])
    monkeypatch.setattr(cli, "load_dotenv", MagicMock())
    monkeypatch.setattr(cli, "AzureCliCredential", MagicMock())
    monkeypatch.setattr(cli, "FoundryChatClient", MagicMock())
    monkeypatch.setattr(cli, "Agent", MagicMock())
    monkeypatch.setattr(cli, "build_workflow", MagicMock())
    run_one = AsyncMock(return_value=None)
    monkeypatch.setattr(cli, "run_one", run_one)

    await cli.main()

    assert [call.args[1] for call in run_one.await_args_list] == expected

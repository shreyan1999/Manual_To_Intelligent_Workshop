"""Offline tests for Module 04. A fake local model stands in for Foundry Local."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from local_triage import INSTRUCTIONS, build_local_agent, choose_route, parse_triage, triage
from redact import redact


# ---- redaction (plain code) ------------------------------------------------------


@pytest.mark.parametrize(
    "text, label",
    [
        ("Call me on 98765 43210", "[PHONE]"),
        ("Call me on +91-9876543210", "[PHONE]"),
        ("Mail priya.s@example.com please", "[EMAIL]"),
        ("Deliver to Pune 411001", "[PIN]"),
    ],
)
def test_redact_masks_personal_details(text, label):
    masked, counts = redact(text)
    assert label in masked and counts[label] == 1


def test_redact_keeps_order_ids_and_amounts():
    masked, counts = redact("Order A1029, refund Rs 4800 for 2 items")
    assert masked == "Order A1029, refund Rs 4800 for 2 items"
    assert counts == {}


# ---- parsing small-model output -----------------------------------------------------


def test_parse_clean_json():
    assert parse_triage('{"intent": "refund", "order_id": "a1029", "urgent": true}') == {
        "intent": "refund",
        "order_id": "A1029",
        "urgent": True,
    }


def test_parse_json_wrapped_in_chatter():
    text = 'Sure! Here you go:\n```json\n{"intent": "delivery", "order_id": "A1030", "urgent": false}\n```'
    assert parse_triage(text)["intent"] == "delivery"


def test_parse_falls_back_to_keywords_when_json_is_broken():
    assert parse_triage("I think this is a refund request")["intent"] == "refund"
    assert parse_triage("no idea")["intent"] == "other"


def test_parse_rejects_made_up_order_ids():
    assert parse_triage('{"intent": "refund", "order_id": "not-an-id"}')["order_id"] is None


# ---- routing (plain code) -------------------------------------------------------------


def test_money_always_goes_to_the_cloud_and_a_person():
    assert choose_route("refund").startswith("cloud")
    assert choose_route("feedback").startswith("local")
    assert choose_route("other").startswith("human")


# ---- end to end with a fake local model ----------------------------------------------


class FakeLocalModel:
    def __init__(self):
        self.seen = []

    async def run(self, text, **kwargs):
        self.seen.append(text)
        return SimpleNamespace(text='{"intent": "refund", "order_id": "A1029", "urgent": false}')


async def test_local_model_never_sees_the_phone_number():
    model = FakeLocalModel()
    result = await triage(model, "I'm Priya, 98765 43210. Order A1029 teapot cracked, refund please.")
    assert "98765" not in model.seen[0]
    assert "[PHONE]" in model.seen[0]
    assert result.intent == "refund" and result.route.startswith("cloud")


def test_build_local_agent_wires_foundry_local_client(monkeypatch):
    """Checks the real FoundryLocalClient is used, without starting the runtime or downloading."""
    import agent_framework.foundry as foundry

    created = {}

    class StubClient:
        def __init__(self, model=None, **kwargs):
            created["model"] = model

    monkeypatch.setattr(foundry, "FoundryLocalClient", StubClient)
    agent = build_local_agent("phi-4-mini")
    assert created["model"] == "phi-4-mini"
    assert agent.name == "local-triage"
    assert "JSON only" in INSTRUCTIONS

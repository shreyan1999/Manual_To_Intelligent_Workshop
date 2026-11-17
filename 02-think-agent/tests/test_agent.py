"""Offline tests for the ChaiCart support agent and its tools."""

from __future__ import annotations

import pytest

import tools
from agent import ask, build_agent, reply_of
from parallel_checks import build_checks, review
from scripted_client import ScriptedChatClient, answer, call


@pytest.fixture(autouse=True)
def clear_refunds():
    tools.REFUND_LOG.clear()


# ---- the tools on their own -------------------------------------------------


async def test_get_order_tool():
    assert (await tools.get_order.invoke(arguments={"order_id": "a1029"}))[0].text.find("Glass teapot") != -1
    assert "No order found" in (await tools.get_order.invoke(arguments={"order_id": "Z999"}))[0].text


async def test_policy_search_finds_the_manager_rule():
    result = await tools.search_refund_policy.invoke(arguments={"question": "refund above 1,000 manager approval"})
    assert "manager" in result[0].text.lower()


def test_refund_tool_requires_approval():
    assert tools.issue_refund.approval_mode == "always_require"
    assert tools.get_order.approval_mode in (None, "never_require")


# ---- the agent loop -------------------------------------------------------------

def refund_script():
    """Fresh model turns for each test (the framework updates response objects as it runs)."""
    return [
        call("get_order", "c1", order_id="A1031"),
        call("search_refund_policy", "c2", question="refund above 1000"),
        call("issue_refund", "c3", order_id="A1031", amount_inr=4800, reason="Hamper crushed"),
    ]


async def test_refund_pauses_for_approval_and_runs_when_approved():
    client = ScriptedChatClient(
        [*refund_script(), answer({"intent": "refund", "order_id": "A1031", "action": "refund", "reply": "Refund issued."})]
    )
    agent = build_agent(client)
    asked = []

    def approve(name, arguments):
        asked.append(name)
        return True

    result = await ask(agent, agent.create_session(), "Hamper A1031 crushed, refund please", approve)

    assert asked == ["issue_refund"]  # only the write tool needed a person
    assert tools.REFUND_LOG == [{"order_id": "A1031", "amount_inr": 4800, "reason": "Hamper crushed"}]
    assert reply_of(result).action == "refund"


async def test_rejected_refund_never_runs():
    client = ScriptedChatClient(
        [*refund_script(), answer({"intent": "refund", "order_id": "A1031", "action": "escalate", "reply": "A manager will contact you."})]
    )
    agent = build_agent(client)
    result = await ask(agent, agent.create_session(), "Refund A1031", lambda name, args: False)
    assert tools.REFUND_LOG == []
    assert reply_of(result).action == "escalate"


async def test_read_tools_run_without_approval():
    client = ScriptedChatClient(
        [
            call("get_order", "c1", order_id="A1030"),
            call("courier_status", "c2", order_id="A1030"),
            answer({"intent": "delivery", "order_id": "A1030", "action": "reply", "reply": "It's at the Pune hub."}),
        ]
    )
    agent = build_agent(client)
    result = await ask(agent, agent.create_session(), "Where is A1030?", lambda *a: pytest.fail("no approval expected"))
    # The courier update reached the model as a tool result.
    tool_results = [c for msgs in client.seen for m in msgs for c in m.contents if c.type == "function_result"]
    assert any("Pune hub" in str(c.result) for c in tool_results)
    assert "Pune hub" in reply_of(result).reply


# ---- multi-agent: concurrent checks ---------------------------------------------


async def test_parallel_checks_return_both_reviews():
    workflow = build_checks(_PerAgentClient())
    lines = await review(workflow, "We'll refund Rs 5,000 right away, no questions asked.")
    assert any(line.startswith("tone_checker: TONE") for line in lines)
    assert any(line.startswith("policy_checker: POLICY ISSUE") for line in lines)


class _PerAgentClient(ScriptedChatClient):
    """Answers differently depending on which reviewer's instructions it sees."""

    def __init__(self):
        super().__init__([])

    async def _inner_get_response(self, *, messages, stream, options, **kwargs):
        text = " ".join(m.text for m in messages if m.text) + str(options.get("instructions", ""))
        if "policy" in text.lower():
            return answer("POLICY ISSUE: promises a refund above Rs 1,000 without manager approval.")
        return answer("TONE OK")

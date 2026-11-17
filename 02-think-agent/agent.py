"""The ChaiCart support agent: model + instructions + tools (Module 02 · Think)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

from agent_framework import Agent, AgentSession, Message

from tools import ALL_TOOLS

INSTRUCTIONS = """\
# Role
You are ChaiCart's customer support assistant. ChaiCart is an Indian online tea shop.

# Rules
1. Call get_order before discussing any order.
2. Call search_refund_policy before deciding on a refund, and follow it exactly.
3. To refund, call issue_refund. A manager approves every refund before money moves.
4. If an order is late, call courier_status and share the update.
5. If you are unsure, or the customer is upset twice, set action to "escalate".
6. Reply in the customer's language. Be brief and kind.

# Output
Return JSON only, with: intent, order_id, action (refund, replace, reply or escalate) and reply.
"""


class SupportReply(BaseModel):
    intent: str
    order_id: str | None = None
    action: Literal["refund", "replace", "reply", "escalate"]
    reply: str


def build_agent(client: Any, extra_tools: list | None = None) -> Agent:
    """Create the agent. ``client`` is a FoundryChatClient (or any Agent Framework chat client)."""
    return Agent(
        client=client,
        name="chaicart-support",
        instructions=INSTRUCTIONS,
        tools=[*ALL_TOOLS, *(extra_tools or [])],
        default_options={"response_format": SupportReply},
    )


def reply_of(result: Any) -> SupportReply:
    """Read the agent's structured reply from a run result."""
    if isinstance(getattr(result, "value", None), SupportReply):
        return result.value
    # Fall back to the last assistant message (for example after a rejected approval).
    for message in reversed(result.messages):
        if message.role == "assistant" and message.text:
            return SupportReply.model_validate_json(message.text)
    raise ValueError("The agent returned no reply.")


async def ask(agent: Agent, session: AgentSession, text: str, approve) -> Any:
    """Send one message. ``approve(name, arguments) -> bool`` decides each approval request."""
    result = await agent.run(text, session=session)
    # Keep answering approval requests until the agent finishes its turn.
    while result.user_input_requests:
        answers = []
        for request in result.user_input_requests:
            if request.function_call is None:
                continue
            ok = approve(request.function_call.name, request.function_call.arguments)
            answers.append(request.to_function_approval_response(ok))
        result = await agent.run(Message(role="user", contents=answers), session=session)
    return result

"""ChaiCart support workflow (Module 01 · Build).

Graph:

    triage (AGENT) -> lookup_order (CODE) -> switch on intent
        refund   -> refund_check (CODE rules + HUMAN approval above the limit)
        delivery -> courier_check (CODE)
        default  -> (straight on)
    -> reply_writer (AGENT) -> send_and_log (CODE, yields the final Ticket)

Only two steps call a model. Everything else is plain, testable Python.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, TypeAdapter
from typing_extensions import Never

from agent_framework import (
    Case,
    Content,
    Default,
    Executor,
    WorkflowBuilder,
    WorkflowContext,
    executor,
    handler,
    response_handler,
)

import chaicart_data as data

# ---------------------------------------------------------------------------
# Messages that flow between steps
# ---------------------------------------------------------------------------


class TriageResult(BaseModel):
    """Structured output the triage agent must return."""

    intent: Literal["refund", "delivery", "feedback", "other"]
    order_id: str | None = None
    sentiment: Literal["positive", "neutral", "negative"] = "neutral"


class ReplyResult(BaseModel):
    """Structured output the reply-writer agent must return."""

    reply: str


@dataclass
class Ticket:
    email: str
    intent: str = "other"
    order_id: str | None = None
    sentiment: str = "neutral"
    order: dict | None = None
    decision: str = ""
    reply: str = ""
    log: list[str] = field(default_factory=list)


@dataclass
class RefundApprovalRequest:
    """Sent to a person when a refund is above the auto-approve limit."""

    order_id: str
    amount_inr: int
    ticket: Ticket  # carried in the request, so a paused run survives checkpoints and restarts

    @classmethod
    def from_content(cls, content: Content) -> RefundApprovalRequest:
        if content.type != "function_approval_request" or content.function_call is None:
            raise ValueError("Expected a refund function approval request.")
        return TypeAdapter(cls).validate_python(content.function_call.parse_arguments())


TRIAGE_INSTRUCTIONS = (
    "You triage customer emails for ChaiCart, an Indian tea shop. "
    "Return JSON only with: intent (refund, delivery, feedback or other), "
    "order_id (like A1029, or null if none is given) and sentiment (positive, neutral or negative)."
)

REPLY_INSTRUCTIONS = (
    "You write short, polite replies for ChaiCart customer support. "
    "Use the decision you are given exactly; never promise anything beyond it. "
    "Write the reply in the same language the customer's email is written in; "
    "if you are not certain what language that is, write in English. "
    "Return JSON only with a single field: reply."
)


def _parse(response: Any, model: type[BaseModel]) -> BaseModel:
    """Use the structured value when the provider returns one, else parse the text as JSON."""
    value = getattr(response, "value", None)
    if isinstance(value, model):
        return value
    text = response.text.strip()
    if text.startswith("```"):
        text = text.strip("`").removeprefix("json").strip()
    return model.model_validate_json(text)


# ---------------------------------------------------------------------------
# Executors (steps)
# ---------------------------------------------------------------------------


class TriageExecutor(Executor):
    """AGENT step: understand the email."""

    def __init__(self, agent: Any):
        super().__init__(id="triage")
        self._agent = agent

    @handler
    async def triage(self, email: str, ctx: WorkflowContext[Ticket]) -> None:
        response = await self._agent.run(email, options={"response_format": TriageResult})
        result = _parse(response, TriageResult)
        ticket = Ticket(email=email, intent=result.intent, order_id=result.order_id, sentiment=result.sentiment)
        ticket.log.append(f"triage: intent={ticket.intent} order={ticket.order_id} sentiment={ticket.sentiment}")
        await ctx.send_message(ticket)


class RefundCheckExecutor(Executor):
    """CODE rules, then a HUMAN decision for large refunds."""

    def __init__(self) -> None:
        super().__init__(id="refund_check")

    @handler
    async def check(self, ticket: Ticket, ctx: WorkflowContext[Ticket]) -> None:
        order = ticket.order
        if order is None:
            ticket.decision = "Ask the customer for their order ID; we could not find the order."
        elif order["status"] != "delivered" or order.get("days_since_delivery", 99) > data.REFUND_WINDOW_DAYS:
            ticket.decision = f"Refund not possible: outside the {data.REFUND_WINDOW_DAYS}-day window or not delivered."
        elif order["total_inr"] <= data.AUTO_APPROVE_LIMIT_INR:
            ticket.decision = f"Refund of Rs {order['total_inr']} approved automatically."
        else:
            # Pause the workflow and ask a person.
            ticket.log.append("refund_check: waiting for human approval")
            request = RefundApprovalRequest(
                order_id=ticket.order_id, amount_inr=order["total_inr"], ticket=ticket
            )
            approval_id = f"refund_{uuid4().hex}"
            await ctx.request_info(
                request_data=Content.from_function_approval_request(
                    id=approval_id,
                    function_call=Content.from_function_call(
                        call_id=approval_id, name="approve_refund", arguments=asdict(request)
                    ),
                ),
                response_type=Content,
            )
            return
        ticket.log.append(f"refund_check: {ticket.decision}")
        await ctx.send_message(ticket)

    @response_handler
    async def on_decision(
        self, original_request: Content, response: Content, ctx: WorkflowContext[Ticket]
    ) -> None:
        if (
            response.type != "function_approval_response"
            or type(response.approved) is not bool
            or response.id != original_request.id
        ):
            raise ValueError("Expected a boolean approval response matching the pending refund.")
        request = RefundApprovalRequest.from_content(original_request)
        approved = response.approved
        ticket = request.ticket
        ticket.decision = (
            f"Refund of Rs {request.amount_inr} approved by a manager."
            if approved
            else "A manager reviewed this and offered a replacement instead of a refund."
        )
        ticket.log.append(f"human: approved={approved}")
        await ctx.send_message(ticket)


class ReplyWriterExecutor(Executor):
    """AGENT step: write the customer reply from the decision."""

    def __init__(self, agent: Any):
        super().__init__(id="reply_writer")
        self._agent = agent

    @handler
    async def write(self, ticket: Ticket, ctx: WorkflowContext[Ticket]) -> None:
        if not ticket.decision:
            ticket.decision = "Thank the customer and say the team has noted their message."
        prompt = f"Customer email:\n{ticket.email}\n\nDecision to communicate:\n{ticket.decision}"
        response = await self._agent.run(prompt, options={"response_format": ReplyResult})
        ticket.reply = _parse(response, ReplyResult).reply
        ticket.log.append("reply_writer: drafted reply")
        await ctx.send_message(ticket)


def _is_intent(expected: str):
    def condition(message: Any) -> bool:
        return isinstance(message, Ticket) and message.intent == expected

    return condition


def build_workflow(triage_agent: Any, reply_agent: Any):
    """Build a fresh workflow graph. Pass any objects with an async ``run()`` method."""

    @executor(id="lookup_order")
    async def lookup_order(ticket: Ticket, ctx: WorkflowContext[Ticket]) -> None:
        ticket.order = data.get_order(ticket.order_id)  # plain code, no AI
        ticket.log.append(f"lookup_order: found={ticket.order is not None}")
        await ctx.send_message(ticket)

    @executor(id="courier_check")
    async def courier_check(ticket: Ticket, ctx: WorkflowContext[Ticket]) -> None:
        status = data.courier_status(ticket.order_id or "")
        ticket.decision = f"Share this courier update and apologise for the delay: {status}"
        ticket.log.append("courier_check: done")
        await ctx.send_message(ticket)

    @executor(id="send_and_log")
    async def send_and_log(ticket: Ticket, ctx: WorkflowContext[Never, str | Ticket]) -> None:
        # A real system would send the email and update the CRM here.
        ticket.log.append("send_and_log: sent")
        await ctx.yield_output(ticket.reply)  # plain text, so chat UIs like Agent Inspector show the reply
        await ctx.yield_output(ticket)  # the full structured ticket for programmatic consumers

    triage = TriageExecutor(triage_agent)
    refund_check = RefundCheckExecutor()
    reply_writer = ReplyWriterExecutor(reply_agent)

    return (
        WorkflowBuilder(start_executor=triage, name="chaicart-support")
        .add_edge(triage, lookup_order)
        .add_switch_case_edge_group(
            lookup_order,
            [
                Case(condition=_is_intent("refund"), target=refund_check),
                Case(condition=_is_intent("delivery"), target=courier_check),
                Default(target=reply_writer),
            ],
        )
        .add_edge(refund_check, reply_writer)
        .add_edge(courier_check, reply_writer)
        .add_edge(reply_writer, send_and_log)
        .build()
    )

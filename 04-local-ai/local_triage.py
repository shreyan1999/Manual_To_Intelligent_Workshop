"""Hybrid ChaiCart triage: private by default, cloud when needed (Module 04 · Local).

    python local_triage.py "Hi, I'm Priya (98765 43210). Order A1029 teapot is cracked, refund please."
    python local_triage.py --model phi-4-mini "..."

1. CODE masks phone numbers, emails and PIN codes on the laptop.
2. A LOCAL model (Foundry Local, via Agent Framework's FoundryLocalClient) classifies the email.
3. CODE decides where it goes next: simple cases stay local, money goes to the cloud agent and a person.

Works with the Wi-Fi off once the model is downloaded.
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
from dataclasses import dataclass
from typing import Any

from agent_framework import Agent

from redact import redact

INSTRUCTIONS = (
    "You classify ChaiCart customer emails. Reply with JSON only, no other text: "
    '{"intent": "refund|delivery|feedback|other", "order_id": "A1234 or null", "urgent": true|false}'
)
INTENTS = {"refund", "delivery", "feedback", "other"}


@dataclass
class Triage:
    intent: str
    order_id: str | None
    urgent: bool
    redacted_text: str
    masked: dict[str, int]
    route: str = ""


def parse_triage(text: str) -> dict[str, Any]:
    """Small local models don't support structured output, so parse defensively."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    try:
        data = json.loads(match.group(0)) if match else {}
    except json.JSONDecodeError:
        data = {}
    intent = str(data.get("intent", "")).lower()
    if intent not in INTENTS:  # fall back to a keyword guess
        lowered = text.lower()
        intent = next((i for i in ("refund", "delivery", "feedback") if i in lowered), "other")
    order_id = data.get("order_id")
    if not isinstance(order_id, str) or not re.fullmatch(r"[A-Za-z]\d{4}", order_id or ""):
        order_id = None
    return {"intent": intent, "order_id": order_id.upper() if order_id else None, "urgent": bool(data.get("urgent"))}


def choose_route(intent: str) -> str:
    """CODE decides, not the model: anything involving money goes to the cloud agent and a person."""
    return {
        "feedback": "local: auto thank-you",
        "delivery": "local: send courier update",
        "refund": "cloud: Foundry support agent + human approval",
    }.get(intent, "human: support inbox")


async def triage(agent: Any, email: str) -> Triage:
    masked_text, masked = redact(email)  # 1. CODE, on the device
    response = await agent.run(masked_text)  # 2. LOCAL model sees only the masked text
    fields = parse_triage(response.text)
    result = Triage(**fields, redacted_text=masked_text, masked=masked)
    result.route = choose_route(result.intent)  # 3. CODE picks the next step
    return result


def build_local_agent(model: str | None = None) -> Agent:
    from agent_framework.foundry import FoundryLocalClient

    # Downloads and loads the model on first use. Reads FOUNDRY_LOCAL_MODEL if model is None.
    client = FoundryLocalClient(model=model or "qwen2.5-0.5b")
    return Agent(client=client, name="local-triage", instructions=INSTRUCTIONS)


async def main() -> None:
    args = sys.argv[1:]
    model = None
    if args[:1] == ["--model"]:
        model, args = args[1], args[2:]
    email = " ".join(args) or "Hi, I'm Priya (98765 43210). Order A1029 teapot is cracked, refund please."

    try:
        agent = build_local_agent(model)
    except ValueError as error:
        raise SystemExit(f"{error}\nThe first run needs internet to download the model. Check the alias with 'foundry model list'.")
    result = await triage(agent, email)
    print(f"Sent to the local model: {result.redacted_text}")
    print(f"Masked: {result.masked or 'nothing'}")
    print(f"Intent: {result.intent} | order: {result.order_id} | urgent: {result.urgent}")
    print(f"Next step: {result.route}")


if __name__ == "__main__":
    asyncio.run(main())

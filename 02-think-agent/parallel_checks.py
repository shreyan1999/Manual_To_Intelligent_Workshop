"""Multi-agent orchestration: two reviewers check a draft reply at the same time (concurrent pattern).

    python parallel_checks.py "Sorry! We'll refund Rs 5,000 right away, no questions asked."
"""

from __future__ import annotations

import asyncio
import sys
from typing import Any

from dotenv import load_dotenv

from agent_framework import Agent
from agent_framework.orchestrations import ConcurrentBuilder

TONE_INSTRUCTIONS = (
    "You review customer-support replies for tone. Answer in one line: "
    "'TONE OK' or 'TONE ISSUE: <why>'."
)
POLICY_INSTRUCTIONS = (
    "You review customer-support replies against this policy: refunds within 7 days of delivery; "
    "a manager must approve refunds above Rs 1,000; never promise a refund before the order is checked. "
    "Answer in one line: 'POLICY OK' or 'POLICY ISSUE: <why>'."
)


def build_checks(client: Any):
    tone = Agent(client=client, name="tone_checker", instructions=TONE_INSTRUCTIONS)
    policy = Agent(client=client, name="policy_checker", instructions=POLICY_INSTRUCTIONS)
    return ConcurrentBuilder(participants=[tone, policy]).build()


async def review(workflow, draft: str) -> list[str]:
    """Run both checks in parallel and return one line per reviewer."""
    lines: list[str] = []
    result = await workflow.run(draft)
    for output in result.get_outputs():
        # The default aggregator yields one AgentResponse holding every reviewer's message.
        for message in output.messages:
            if message.role == "assistant" and message.text:
                lines.append(f"{message.author_name}: {message.text}")
    return lines


async def main() -> None:
    load_dotenv()
    from agent_framework.foundry import FoundryChatClient
    from azure.identity.aio import AzureCliCredential

    draft = " ".join(sys.argv[1:]) or "Sorry! We'll refund Rs 5,000 right away, no questions asked."
    async with AzureCliCredential() as credential:
        workflow = build_checks(FoundryChatClient(credential=credential))
        for line in await review(workflow, draft):
            print(line)


if __name__ == "__main__":
    asyncio.run(main())

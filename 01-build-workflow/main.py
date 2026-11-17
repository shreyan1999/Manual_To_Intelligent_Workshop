"""Run the ChaiCart workflow against Microsoft Foundry, in your terminal.

    az login
    cp .env.example .env    # then fill in your project endpoint and model deployment
    python main.py                       # runs the three sample emails
    python main.py "Order A1031 arrived broken, refund please"

When a refund is above the auto-approve limit, the workflow pauses and asks you (the
"manager") to approve it in the terminal, then resumes.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from agent_framework import Agent, Content
from agent_framework.foundry import FoundryChatClient
from azure.identity.aio import AzureCliCredential

from workflow import REPLY_INSTRUCTIONS, TRIAGE_INSTRUCTIONS, RefundApprovalRequest, Ticket, build_workflow


async def run_one(workflow, email: str) -> Ticket | None:
    """Run one email through the workflow, answering approval requests from the keyboard."""
    stream = workflow.run(email, stream=True)
    while True:
        responses: dict[str, Content] = {}
        result: Ticket | None = None
        async for event in stream:
            if event.type == "request_info":
                req = RefundApprovalRequest.from_content(event.data)
                answer = input(f"\n  APPROVAL NEEDED · refund Rs {req.amount_inr} for {req.order_id}. Approve? [y/N] ")
                responses[event.request_id] = event.data.to_function_approval_response(
                    answer.strip().lower().startswith("y")
                )
            elif event.type == "output" and isinstance(event.data, Ticket):
                result = event.data
        if not responses:
            return result
        # Resume the same workflow with the human's answers.
        stream = workflow.run(stream=True, responses=responses)


async def main() -> None:
    load_dotenv()
    emails = sys.argv[1:] or json.loads(
        Path(__file__).resolve().with_name("sample_emails.json").read_text(encoding="utf-8")
    )

    async with AzureCliCredential() as credential:
        client = FoundryChatClient(credential=credential)  # reads FOUNDRY_PROJECT_ENDPOINT and FOUNDRY_MODEL
        triage_agent = Agent(client=client, name="triage", instructions=TRIAGE_INSTRUCTIONS)
        reply_agent = Agent(client=client, name="reply-writer", instructions=REPLY_INSTRUCTIONS)

        for email in emails:
            print(f"\nEMAIL: {email}")
            workflow = build_workflow(triage_agent, reply_agent)  # fresh graph per email
            ticket = await run_one(workflow, email)
            if ticket:
                for line in ticket.log:
                    print(f"  · {line}")
                print(f"  REPLY: {ticket.reply}")


if __name__ == "__main__":
    asyncio.run(main())

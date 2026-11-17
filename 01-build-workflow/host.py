"""Expose the workflow over the Foundry Responses protocol (http://localhost:8088/responses).

This is the entry point Foundry Toolkit's Agent Inspector talks to locally, and the one
Foundry Agent Service runs when you deploy this folder as a hosted agent.

    python host.py
    curl -X POST http://localhost:8088/responses -H "Content-Type: application/json" \
         -d '{"input": "Where is order A1030?"}'
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

from agent_framework_foundry_hosting import (
    CheckpointStoreProvider,
    HostedResponseRequest,
    ResponsesHostServer,
    WorkflowTurn,
)

from workflow import REPLY_INSTRUCTIONS, TRIAGE_INSTRUCTIONS, RefundApprovalRequest, Ticket, build_workflow

# The host checkpoints workflow state between HTTP requests; list our own message types.
ALLOWED_TYPES = [f"{t.__module__}:{t.__qualname__}" for t in (Ticket, RefundApprovalRequest)]


def make_server(triage_agent, reply_agent) -> ResponsesHostServer:
    def workflow_factory(request: HostedResponseRequest):
        # Must return a freshly built graph for every run.
        return build_workflow(triage_agent, reply_agent)

    async def parse_response(request: HostedResponseRequest) -> WorkflowTurn:
        items = await request.get_input_items()
        if any(item.get("type") in ("function_call_output", "mcp_approval_response") for item in items):
            # The caller is answering a pending refund approval.
            return WorkflowTurn(responses=await request.get_workflow_responses())
        return WorkflowTurn(input=(await request.get_input_text()) or "")

    return ResponsesHostServer(
        workflow=workflow_factory,
        parse_response=parse_response,
        checkpoint_store_provider=CheckpointStoreProvider(allowed_checkpoint_types=ALLOWED_TYPES),
    )


def main() -> None:
    load_dotenv()
    from agent_framework import Agent
    from agent_framework.foundry import FoundryChatClient
    from azure.identity import DefaultAzureCredential

    client = FoundryChatClient(credential=DefaultAzureCredential())
    triage_agent = Agent(client=client, name="triage", instructions=TRIAGE_INSTRUCTIONS)
    reply_agent = Agent(client=client, name="reply-writer", instructions=REPLY_INSTRUCTIONS)
    make_server(triage_agent, reply_agent).run()


if __name__ == "__main__":
    main()

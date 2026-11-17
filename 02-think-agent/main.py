"""Chat with the ChaiCart support agent running on Microsoft Foundry.

    az login
    cp .env.example .env
    python main.py               # interactive chat
    python main.py --learn-mcp   # also attach the public Microsoft Learn MCP server (hosted MCP tool)

Try: "Order A1029 arrived broken, I want a refund"
     "My hamper A1031 was crushed, refund please"      (above Rs 1,000: you approve as manager)
     "Where is order A1030?"
"""

from __future__ import annotations

import asyncio
import json
import sys

from dotenv import load_dotenv

from agent_framework.foundry import FoundryChatClient
from azure.identity.aio import AzureCliCredential

from agent import ask, build_agent, reply_of


def approve_in_terminal(name: str, arguments) -> bool:
    print(f"\n  APPROVAL NEEDED · {name}({arguments})")
    return input("  Approve? [y/N] ").strip().lower().startswith("y")


async def main() -> None:
    load_dotenv()
    async with AzureCliCredential() as credential:
        client = FoundryChatClient(credential=credential)  # reads FOUNDRY_PROJECT_ENDPOINT and FOUNDRY_MODEL

        extra = []
        if "--learn-mcp" in sys.argv:
            # A hosted MCP tool: Foundry connects to the server, not your laptop.
            extra.append(
                client.get_mcp_tool(
                    name="microsoft_learn",
                    url="https://learn.microsoft.com/api/mcp",
                    approval_mode="never_require",
                )
            )

        agent = build_agent(client, extra)
        session = agent.create_session()
        print("ChaiCart support agent. Type 'exit' to quit.")
        while (text := input("\nYou: ").strip()) and text.lower() != "exit":
            result = await ask(agent, session, text, approve_in_terminal)
            reply = reply_of(result)
            print(f"Agent [{reply.action}]: {reply.reply}")
            # Uncomment to see the full structured output:
            # print(json.dumps(reply.model_dump(), indent=2))


if __name__ == "__main__":
    asyncio.run(main())

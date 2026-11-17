# Module 02 · Think: the ChaiCart support agent

An AI agent built with **Microsoft Agent Framework** on **Microsoft Foundry**. It has instructions, knowledge, tools, an optional MCP server, and a human approval step. A second script shows two agents working in parallel.

| Piece | Where it is |
| --- | --- |
| **Model** | Your Foundry deployment, via `FoundryChatClient` |
| **Instructions** | `INSTRUCTIONS` in `agent.py`: role, numbered rules, JSON output |
| **Knowledge** | `knowledge/refund-policy.md`, searched by the `search_refund_policy` tool |
| **Read tools** | `get_order` and `courier_status`. These run freely. |
| **Write tool** | `issue_refund`, marked `approval_mode="always_require"`. A person must say yes first. |
| **MCP (optional)** | The public Microsoft Learn MCP server, attached as a Foundry-hosted MCP tool (`--learn-mcp`) |
| **Structured output** | `SupportReply` (intent, order_id, action, reply) |
| **Multi-agent** | `parallel_checks.py`: a tone checker and a policy checker review a draft at the same time (concurrent orchestration) |

## Files

| File | What it is |
| --- | --- |
| `agent.py` | `build_agent()`, the `ask()` loop that handles approval requests, and `reply_of()` |
| `tools.py` | The four function tools and fake ChaiCart data |
| `main.py` | Interactive chat in your terminal against Foundry |
| `parallel_checks.py` | Concurrent orchestration with `ConcurrentBuilder` |
| `tests/` | Offline tests. A scripted model plays back tool calls through Agent Framework's real tool and approval machinery. |

## Prerequisites

- Python 3.11+ (tested on 3.13)
- For live runs: a Microsoft Foundry project with a chat model that supports tool calling and structured output, plus `az login`

## Set up

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # add your project endpoint and model deployment name
```

## Run the tests (no Azure account needed)

```bash
pytest
```

Expected: `7 passed`. The tests check that:

- The refund tool needs approval and the read tools don't.
- An approved refund runs, and a rejected refund never runs.
- The courier update reaches the model.
- Both parallel reviewers answer.

## Run it against Foundry

```bash
az login
python main.py                 # chat
python main.py --learn-mcp     # chat, with the Microsoft Learn MCP server attached
python parallel_checks.py "Sorry! We'll refund Rs 5,000 right away, no questions asked."
```

Things to type:

- `Order A1029 arrived broken, I want a refund` (₹640): the agent checks the order and the policy, then asks to refund. You approve.
- `My hamper A1031 was crushed, refund please` (₹4,800): say `n` to see the agent escalate instead.
- `Where is order A1030?` uses read tools only, with no approval.
- With `--learn-mcp`: `How do I add an MCP tool to a Foundry agent?`

## How approval works

```python
result = await agent.run(text, session=session)
while result.user_input_requests:                         # the agent asked to call issue_refund
    answers = [r.to_function_approval_response(approve(...)) for r in result.user_input_requests]
    result = await agent.run(Message(role="user", contents=answers), session=session)
```

Use the same `session` for the follow-up call. An approval only counts when it matches a pending request in that session.

## Same agent in Foundry Toolkit (Demo 2)

To build this without code in Foundry Toolkit's Agent Builder:

1. Paste `INSTRUCTIONS`.
2. Attach `knowledge/refund-policy.md` with the File search tool.
3. Add the Microsoft Learn MCP server (`https://learn.microsoft.com/api/mcp`).

In Module 03 you replace that MCP server with your own ChaiCart orders server.

## Notes

- Foundry-hosted tools such as File search and web search are available through `client.get_file_search_tool(...)`, `client.get_web_search_tool()` and so on. Here the policy lookup is a plain function, so the sample runs without uploading files.
- Never put secrets in instructions or tool arguments.
- Running evaluations also uses your model, so evaluations cost money too.

# ChaiCart Orders MCP server

A custom integration: ChaiCart's order system exposed as **MCP tools**. Any MCP client can use it, including GitHub Copilot in VS Code, a Foundry agent, Agent Framework (`MCPStdioTool`) or your own app.

| Tool | What it does | Changes data? |
| --- | --- | --- |
| `get_order` | Status, items and total for an order | No |
| `courier_status` | Latest courier update | No |
| `issue_refund` | **Queues** a refund for a manager. It never pays directly. | Yes (queue only) |
| `list_pending_refunds` | Refunds waiting for approval | No |

Built with the **MCP Python SDK 2.x**.

> **Heads-up for older tutorials:** in 2.x, `from mcp.server.fastmcp import FastMCP` is gone. Use `from mcp.server.mcpserver import MCPServer`.

## Files

| File | Purpose |
| --- | --- |
| `server.py` | The MCP server (stdio by default, `--http` for Streamable HTTP) |
| `spec.md` | The spec you give Copilot in agent mode (Demo 3) |
| `tests/test_server.py` | 8 tests: in-process client, tool errors, schema checks, and a real stdio subprocess |
| `.vscode/mcp.json` | Registers the server with VS Code / GitHub Copilot |
| `.github/copilot-instructions.md` | Always-on project rules for Copilot |
| `.github/agents/policy-reviewer.agent.md` | A read-only custom agent that reviews the tools |
| `.github/prompts/add-tool.prompt.md` | A reusable prompt: “add a tool, with tests” |

## Set up and test

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
pytest          # expected: 8 passed
```

## Use it from GitHub Copilot in VS Code

1. Open **this folder** in VS Code.
2. `.vscode/mcp.json` starts the server with `python`. If VS Code doesn't pick up your virtual environment, change `"command"` to the venv's interpreter, for example `.venv/Scripts/python.exe` on Windows or `.venv/bin/python` on macOS and Linux.
3. Open Copilot Chat in **Agent** mode, and allow the `chaicart-orders` tools when asked.
4. Ask: *What's the status of order A1029?* or *Queue a refund for A1031 because the hamper was crushed.*
5. Pick **Policy Reviewer** from the agents list and ask it to review `server.py`.
6. Type `/add-tool` and describe a new tool, for example *cancel an order that hasn't shipped*.

## Run it over HTTP (for hosting or a Foundry agent)

```bash
python server.py --http        # http://127.0.0.1:8000/mcp
```

A Foundry agent in the cloud can't reach your laptop. Host the server first (for example on Azure Container Apps or Azure Functions), then add its public URL as an MCP tool, as in Module 02's `--learn-mcp`.

## Demo 3 script (Copilot builds it)

1. Start from an empty folder that contains only `spec.md` and `.github/copilot-instructions.md`.
2. In agent mode, ask: *Build the MCP server in spec.md, with pytest tests.*
3. Read the diff aloud, run `pytest`, and fix a failure together.
4. Compare the result with `server.py` here.

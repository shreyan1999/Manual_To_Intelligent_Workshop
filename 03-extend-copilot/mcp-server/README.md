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

### Step 1: Install the dependencies (one time)

Complete **Set up and test** above. The server needs `mcp` 2.x. An older `mcp` (for example 1.x in your system Python) fails with `ModuleNotFoundError: No module named 'mcp.server.mcpserver'`.

### Step 2: Open the correct folder in VS Code

1. Choose **File → Open Folder…**.
2. Select this `mcp-server` folder, the one that contains `.vscode`, `.github` and `server.py`.

Don't open a parent folder. VS Code only reads `.vscode/mcp.json` and `.github/` from the folder you open, so the Policy Reviewer agent and `/add-tool` won't appear otherwise.

### Step 3: Point the server at the right Python

Open `.vscode/mcp.json` and set `"command"` to the interpreter of the virtual environment where you ran `pip install -r requirements.txt`:

```json
"command": "${workspaceFolder}/.venv/Scripts/python.exe",
```

- Windows: `${workspaceFolder}/.venv/Scripts/python.exe`
- macOS and Linux: `${workspaceFolder}/.venv/bin/python`
- If you share one virtual environment across modules, use its path instead (for example `${workspaceFolder}/../../../.venv/Scripts/python.exe`).

A plain `"command": "python"` only works if the `python` on your PATH already has `mcp` 2.x installed.

### Step 4: Start the MCP server

1. Open `.vscode/mcp.json` and click **Start** above `"chaicart-orders"`. Alternatively, press `Ctrl+Shift+P`, run **MCP: List Servers**, select **chaicart-orders**, then choose **Start Server** (or **Restart Server** after changing the config).
2. Wait until the status shows **Running** and the tools are listed.
3. If it fails, choose **Show Output** in the same menu to read the error.

### Step 5: Use the tools in Copilot Chat

1. Open Copilot Chat (`Ctrl+Alt+I`) and set the mode to **Agent**.
2. Click the **Tools** icon and make sure **chaicart-orders** is enabled.
3. Ask: *What's the status of order A1029?* or *Queue a refund for A1031 because the hamper was crushed.*
4. Click **Allow** when Copilot asks to run a tool.

### Step 6: Review the tools with the Policy Reviewer agent

1. In the chat agent dropdown, pick **Policy Reviewer**.
2. Ask: *Review server.py.*
3. It returns a numbered list of policy issues. It only reads files and never edits them.

### Step 7: Add a tool with the `/add-tool` prompt

1. Switch back to **Agent** mode.
2. Type `/add-tool` and press Enter.
3. When asked what the tool should do, answer, for example: *cancel an order that hasn't shipped*.
4. Copilot adds the tool to `server.py`, writes tests, runs `pytest`, and summarises the change.

### Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'mcp.server.mcpserver'` | The interpreter in `mcp.json` has an old `mcp`. Complete Step 3, then run `pip install -r requirements.txt` in that environment. |
| Server won't start | Check that the interpreter path in `mcp.json` exists. Use **Show Output** for details. |
| Tools don't appear in chat | Use **Agent** mode and confirm the server shows **Running**. |
| Policy Reviewer or `/add-tool` is missing | You opened the wrong folder. Reopen `mcp-server` (Step 2). |

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

# ChaiCart Orders MCP server: project rules for GitHub Copilot

- Python 3.11+, with type hints on every function.
- MCP Python SDK 2.x: import `MCPServer` from `mcp.server.mcpserver`. Never use `mcp.server.fastmcp` (removed in 2.x).
- Every tool needs a one-line docstring that says when to use it. The model reads it.
- Read-only tools get `ToolAnnotations(readOnlyHint=True)`.
- Tools that change data must never pay or delete anything directly. They queue the request for a person to approve.
- Raise `ToolError` with a helpful message for problems the model should see, such as an unknown order ID.
- Every new tool gets a pytest test in `tests/test_server.py` that uses `mcp.Client(server.mcp)`.
- No secrets, keys or real customer data in code, tests or prompts.

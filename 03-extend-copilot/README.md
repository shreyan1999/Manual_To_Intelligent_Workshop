# Module 03 · Extend: GitHub Copilot for custom integrations

Two standalone projects. Each has its own README, dependencies and tests.

| Folder | What you build | Language | Tests |
| --- | --- | --- | --- |
| [`mcp-server/`](mcp-server/README.md) | ChaiCart Orders **MCP server**, plus Copilot custom instructions, a custom agent and a prompt file | Python | `pytest` → 8 passed |
| [`copilot-sdk-app/`](copilot-sdk-app/README.md) | ChaiCart **ops assistant** that embeds Copilot's agent loop with the Copilot SDK | TypeScript | `npm test` → 4 passed |

## How they map to the slides

- **“Teach Copilot how your project works”:** `mcp-server/.github/` holds `copilot-instructions.md`, `agents/policy-reviewer.agent.md` and `prompts/add-tool.prompt.md`. `mcp-server/.vscode/mcp.json` registers the server with VS Code.
- **“Wrap ChaiCart's order system as an MCP server”:** `mcp-server/server.py`.
- **“Put Copilot's agent loop inside your own tool”:** `copilot-sdk-app/src/ops-assistant.ts`.
- **Demo 3:** follow the “Demo 3 script” in `mcp-server/README.md`.

## Version notes (checked 17 Nov 2026)

- MCP Python SDK 2.3.0: `FastMCP` was renamed `MCPServer` and moved to `mcp.server.mcpserver`. Old `fastmcp` imports fail.
- `@github/copilot-sdk` 1.0.34 bundles the Copilot runtime, so the CLI needn't be installed.

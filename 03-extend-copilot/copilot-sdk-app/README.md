# ChaiCart ops assistant (GitHub Copilot SDK)

A small business tool for the support team, written in TypeScript. It puts **GitHub Copilot's agent loop** inside your own app with the **GitHub Copilot SDK** (`@github/copilot-sdk`). You give it ChaiCart tools, and Copilot decides when to call them.

```
You: Queue a refund for A1031, the hamper was crushed
Assistant: Done. A Rs 4,800 refund for A1031 is queued for a manager's approval.
```

## Files

| File | Purpose |
| --- | --- |
| `src/orders.ts` | Plain business logic: look up orders, queue refunds. No AI. |
| `src/tools.ts` | Three tools defined with `defineTool()`: JSON-schema parameters plus a handler |
| `src/ops-assistant.ts` | The app: `CopilotClient` → `createSession({ tools, availableTools: ["custom:*"] })` → `sendAndWait` |
| `test/tools.test.ts` | Unit tests for the tool handlers. No Copilot sign-in needed. |

## Prerequisites

- Node.js 20.19+ or 22.12+
- A GitHub account with Copilot. **Copilot Student** is free for verified students through GitHub Education.

The SDK ships the Copilot runtime, so you don't need to install the Copilot CLI separately.

## Set up and test

```bash
npm install
npm test        # type-checks, then runs 4 tests
```

## Run it

Sign in once. Either use the GitHub CLI (`gh auth login`), or set a token in `COPILOT_GITHUB_TOKEN` or `GH_TOKEN`. Then:

```bash
npm start                                         # interactive
npm start -- "Which refunds are waiting for approval?"
```

If you see `No GitHub OAuth token or Copilot HMAC key provided`, the app started correctly. You just need to sign in.

## Design choices worth pointing out

- **`availableTools: ["custom:*"]`** limits the agent to our three tools: no shell commands and no file edits. That's right for a business tool.
- **`queue_refund` only queues.** A person still approves the money, as in Modules 01 and 02.
- Business logic stays in `orders.ts`, so you can test it without any AI.

## Same tools, three clients

The ChaiCart tools now exist as:

1. An MCP server (`../mcp-server`) for Copilot in VS Code and Foundry agents.
2. Function tools in Module 02's Agent Framework agent.
3. Copilot SDK tools here.

The tool contract stays the same; only the client changes.

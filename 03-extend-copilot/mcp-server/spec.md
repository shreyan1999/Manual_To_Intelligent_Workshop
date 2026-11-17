# Spec: ChaiCart Orders MCP server

Give AI assistants safe access to ChaiCart's order system.

## Tools

| Tool | Input | Output | Notes |
| --- | --- | --- | --- |
| `get_order` | `order_id` | status, items, total in rupees, days since delivery | Read only. Unknown ID → a helpful error. |
| `courier_status` | `order_id` | one-line courier update | Read only |
| `issue_refund` | `order_id`, `amount_inr` (> 0), `reason` | the queued request, status `pending_approval` | Never pays directly. Amount can't exceed the order total. |
| `list_pending_refunds` | none | refunds waiting for approval | Read only |

## Transports

- stdio for VS Code and GitHub Copilot
- Streamable HTTP (`--http`, port 8000, path `/mcp`) for hosting and Foundry agents

## Done when

- `pytest` passes.
- Copilot Chat in VS Code answers “What’s the status of order A1029?” using `get_order`.

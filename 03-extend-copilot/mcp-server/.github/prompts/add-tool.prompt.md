---
description: Add a new tool to the ChaiCart Orders MCP server, with a test.
agent: agent
---

Add a new MCP tool to `server.py`: ${input:toolDescription:What should the tool do?}

Follow `.github/copilot-instructions.md`. Then:

1. Add the tool, with type hints, a docstring and the right `ToolAnnotations`.
2. Add tests to `tests/test_server.py`: the happy path and one error case.
3. Run `pytest` and fix any failures.
4. Summarise the change in three lines.

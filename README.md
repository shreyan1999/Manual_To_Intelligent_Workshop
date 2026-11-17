# Manual to Intelligent Workshop

This repository contains the hands-on projects for the Reva University workshop. Follow the modules to see how ChaiCart's manual customer-support process can grow into AI-assisted workflows, agents, integrations, and local AI.

## Workshop modules

| Module | Topic | Project |
| --- | --- | --- |
| [01 · Build](01-build-workflow/README.md) | Turn support emails into a workflow with triage, order lookup, refund rules, human approval, and reply generation. | Microsoft Agent Framework workflow for Microsoft Foundry |
| [02 · Think](02-think-agent/README.md) | Build a support agent with instructions, knowledge, tools, structured replies, and human approval; compare concurrent agent checks. | Microsoft Agent Framework agent for Microsoft Foundry |
| [03 · Extend](03-extend-copilot/README.md) | Add custom integrations to GitHub Copilot and embed the Copilot agent loop in an app. | [ChaiCart Orders MCP server](03-extend-copilot/mcp-server/README.md) and [Copilot SDK app](03-extend-copilot/copilot-sdk-app/README.md) |
| [04 · Local AI](04-local-ai/README.md) | Run a small model on-device and combine local triage with code-based redaction and cloud escalation. | Foundry Local and Agent Framework |

The examples share the ChaiCart support scenario, but each module is a standalone project with its own dependencies and setup instructions.

## Getting started

1. Choose a module and open its folder in your terminal or VS Code.
2. Follow that module's README for prerequisites, environment setup, and run instructions.
3. Run its tests before trying the live or model-backed demo.

Python modules use their own `requirements.txt` files. Module 03's Copilot SDK app uses Node.js and npm. There is no root-level dependency installation or test command.

The Python projects generally use Python 3.11 or later. Modules 01 and 02 need a Microsoft Foundry project and Azure CLI sign-in to run against a live model; their tests run offline. Module 03's Copilot SDK app requires Node.js 20.19+ or 22.12+ and a GitHub Copilot sign-in to run interactively. Module 04 downloads a local model on first use; its tests do not require a model download.

## Run a module's tests

Run the relevant command from that module's directory:

```powershell
# Python modules: 01-build-workflow, 02-think-agent, 04-local-ai,
# or 03-extend-copilot/mcp-server
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest
```

For the TypeScript Copilot SDK app, from `03-extend-copilot/copilot-sdk-app`:

```powershell
npm install
npm test
```

Each module README includes more specific test coverage, demo instructions, and any required credentials or model setup. Keep credentials in local environment configuration; do not commit secrets.

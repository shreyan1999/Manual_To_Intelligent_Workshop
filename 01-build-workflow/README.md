# Module 01 · Build: the ChaiCart support workflow

Turns ChaiCart's manual email process into a workflow built with **Microsoft Agent Framework**. You run it locally, inspect it in **Foundry Toolkit**, and deploy it to **Microsoft Foundry** as a hosted agent.

```
triage (AGENT) → lookup_order (CODE) → switch on intent
    refund   → refund_check (CODE rules, HUMAN approval above ₹1,000)
    delivery → courier_check (CODE)
    other    → straight on
→ reply_writer (AGENT) → send_and_log (CODE)
```

Only two of the seven steps call a model. Refund rules (the 7-day window and the ₹1,000 auto-approve limit) are plain Python in `chaicart_data.py`. That way they're cheap, predictable and unit-tested.

> **Why code and not the portal designer?** Foundry's portal-based declarative workflows retire on 1 December 2026. Microsoft's recommended path is Agent Framework workflows in code, deployed as hosted agents.

## Files

| File | What it is |
| --- | --- |
| `workflow.py` | The graph: executors, switch-case routing, and human-in-the-loop with `ctx.request_info()` and `@response_handler` |
| `chaicart_data.py` | Fake orders, courier updates and business rules |
| `main.py` | Runs sample emails against Foundry in your terminal; you approve big refunds at the prompt |
| `host.py` | Serves the workflow on `http://localhost:8088/responses` (Foundry Responses protocol) for Agent Inspector and for deployment |
| `sample_emails.json` | Four test emails: small refund, late delivery, compliment, large refund |
| `tests/` | Offline tests with fake agents, including an HTTP approval round trip. No Azure needed. |

## Prerequisites

- Python 3.11+ (tested on 3.13)
- For the live run: a Microsoft Foundry project with a chat model deployed, plus the Azure CLI signed in (`az login`)

## Set up

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # then add your project endpoint and model deployment name
```

## Run the tests (no Azure account needed)

```bash
pytest
```

Expected: `8 passed`. The tests cover auto-approved and declined refunds, the human approval pause and resume, the delivery and feedback paths, and the hosted HTTP endpoint.

## Run it against Foundry

```bash
az login
python main.py                                          # the four sample emails
python main.py "Order A1031 hamper was crushed, refund please"
```

For A1031 (₹4,800) the workflow pauses with `APPROVAL NEEDED`. Answer `y` or `n`, and it resumes from where it stopped.

## Debug it in Foundry Toolkit (Demo 1)

1. Run `python host.py`. It listens on `http://localhost:8088/responses`.
2. In VS Code, open Foundry Toolkit and start Agent Inspector against the local server. Send the sample emails and watch each executor run.
3. You can also call the endpoint directly:

```bash
curl -X POST http://localhost:8088/responses -H "Content-Type: application/json" \
     -d '{"input": "Where is order A1030?"}'
```

A large refund comes back as a `function_call` named `request_info`. To approve it, send a `function_call_output` with the same `call_id`, `"output": "true"`, and the first response's `previous_response_id` and `agent_session_id`. `tests/test_host.py` shows the exact request.

## Deploy as a hosted agent

The simplest route for students is Foundry Toolkit's **Create Agent → hosted agent** flow:

1. Scaffold a Python hosted-agent project.
2. Replace its agent code with `workflow.py`, `chaicart_data.py` and `host.py`.
3. Deploy. The default deployment path uses remote packaging, so you don't need a local Docker build.

## Things to try

- Change `AUTO_APPROVE_LIMIT_INR` and re-run the tests: which ones should change?
- Add a `"cancel"` intent with its own branch.
- Add a fan-out edge that runs a tone check and a policy check in parallel.

## Notes

- `build_workflow()` returns a fresh graph each time. Workflow runs keep state, so build one per conversation.
- The paused ticket travels inside `RefundApprovalRequest`. That's why a hosted run can resume after a restart: the host checkpoints it, and `host.py` lists the custom types it's allowed to restore.
- Local runs still call your cloud model, so they can incur charges.

# Module 04 · Local: AI on your own device

Run small models on your laptop with **Foundry Local**. Once a model is downloaded, it works with the Wi-Fi off. The examples also use **Agent Framework's Foundry Local provider**, so the same agent code can run locally or in the cloud.

| File | What it shows |
| --- | --- |
| `hello_local.py` | Foundry Local SDK 2.x basics: download, load, stream a chat, unload. No CLI or API key needed. |
| `redact.py` | Plain code that masks phone numbers, emails and PIN codes before any model sees them |
| `local_triage.py` | The hybrid pattern: mask (CODE) → classify with a local model (LOCAL) → route (CODE). Refunds go to the cloud agent and a person. |
| `tests/` | 12 offline tests: redaction, parsing messy small-model output, routing, and a fake local model that checks the phone number never reaches it |

## Prerequisites

- Python 3.11+ (tested on 3.13)
- Windows, macOS or Linux, with 8 GB+ RAM for `qwen2.5-0.5b` and 16 GB recommended for `phi-4-mini`
- Internet for the **first** run only, to download the model and hardware components

## Set up and test

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
pytest          # expected: 12 passed (no model download needed)
```

## Run it on your machine

```bash
python hello_local.py                     # qwen2.5-0.5b: small and fast
python hello_local.py phi-4-mini          # better answers

python local_triage.py "Hi, I'm Priya (98765 43210). Order A1029 teapot is cracked, refund please."
```

Expected output from `local_triage.py` (the model's wording may vary):

```
Sent to the local model: Hi, I'm Priya ([PHONE]). Order A1029 teapot is cracked, refund please.
Masked: {'[PHONE]': 1}
Intent: refund | order: A1029 | urgent: False
Next step: cloud: Foundry support agent + human approval
```

**Demo 4:** run it once with the Wi-Fi on so the model downloads. Then turn the Wi-Fi off and run it again.

## The CLI (optional, preview)

Your app doesn't need the CLI; the SDK is enough. The CLI is handy for exploring models:

```bash
winget install Microsoft.FoundryLocal       # Windows (macOS: see the Foundry Local docs)
foundry model list                          # what runs on this machine; the Task column shows "tools" support
foundry model run qwen2.5-0.5b              # download, load and chat
foundry server status
```

CLI commands can change between preview releases. If one fails, run `foundry --help`.

## Know the limits

- Agent Framework's Foundry Local provider is **Python only** for now.
- It supports **function tools** but not structured output, code interpreter, file search or MCP tools. That's why `parse_triage()` reads JSON defensively and falls back to keywords.
- Small models are good at narrow jobs: classifying, extracting, masking, short summaries. Use the cloud for multi-step reasoning with many tools.
- `redact.py` is a teaching example, not a complete PII solution.

## Foundry Toolkit

In VS Code, downloaded models appear under **Foundry Toolkit → My Resources → Local Resources → Models**. Use the **Playground** to compare a local model and a cloud model on the same prompt before you choose.

"""Hello, Foundry Local: download a small model, load it, and chat on your own device.

    python hello_local.py                    # default model: qwen2.5-0.5b (small and fast)
    python hello_local.py phi-4-mini         # better answers, needs more RAM

The first run downloads the model and hardware acceleration components. After that it works offline.
Uses the Foundry Local SDK 2.x native chat API: no CLI, no web server, no API key.
"""

from __future__ import annotations

import sys

from foundry_local_sdk import Configuration, FoundryLocalManager

PROMPT = (
    "Classify this customer email as refund, delivery, feedback or other. Answer with one word.\n\n"
    "Email: My order A1029 arrived but the glass teapot is cracked. I'd like my money back."
)


def main() -> None:
    alias = sys.argv[1] if len(sys.argv) > 1 else "qwen2.5-0.5b"

    FoundryLocalManager.initialize(Configuration(app_name="chaicart_local_demo"))
    manager = FoundryLocalManager.instance

    # Optional but recommended: fetch the best execution providers (GPU/NPU) for this machine.
    manager.download_and_register_eps()

    model = manager.catalog.get_model(alias)
    if model is None:
        raise SystemExit(
            f"Couldn't find '{alias}'. Either the catalog couldn't be reached (the first run needs "
            "internet) or the alias is wrong. Run 'foundry model list' to see valid aliases."
        )

    model.download(lambda pct: print(f"\rDownloading {alias}: {pct:5.1f}%", end="", flush=True))
    print()
    model.load()

    client = model.get_chat_client()
    print(f"Prompt: {PROMPT}\n\nAnswer: ", end="")
    for chunk in client.complete_streaming_chat([{"role": "user", "content": PROMPT}]):
        print(chunk.choices[0].delta.content or "", end="", flush=True)
    print()

    model.unload()


if __name__ == "__main__":
    main()

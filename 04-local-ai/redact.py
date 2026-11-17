"""Mask personal details before text leaves the device. Plain code, no AI.

Catches Indian mobile numbers, email addresses and 6-digit PIN codes. It's a teaching
example: real systems need a proper PII service and a review of what they miss.
"""

from __future__ import annotations

import re

_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("[EMAIL]", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("[PHONE]", re.compile(r"(?<!\w)(?:\+?91[\s-]?|0)?[6-9]\d{4}[\s-]?\d{5}(?!\w)")),
    ("[PIN]", re.compile(r"(?<![\w-])[1-9]\d{5}(?![\w-])")),
]


def redact(text: str) -> tuple[str, dict[str, int]]:
    """Return the masked text and how many of each kind were masked."""
    counts: dict[str, int] = {}
    for label, pattern in _PATTERNS:
        text, n = pattern.subn(label, text)
        if n:
            counts[label] = n
    return text, counts

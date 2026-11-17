"""A scripted chat client for offline tests.

It plays back pre-written model turns (tool calls, then a final answer) through Agent
Framework's real function-invocation layer, so tool execution and approvals behave as they
do with FoundryChatClient, without calling a model.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from agent_framework import BaseChatClient, ChatResponse, Content, FunctionInvocationLayer, Message


def call(name: str, call_id: str, **arguments: Any) -> ChatResponse:
    return ChatResponse(
        messages=[Message(role="assistant", contents=[Content.from_function_call(call_id, name, arguments=arguments)])]
    )


def answer(payload: dict | str) -> ChatResponse:
    text = payload if isinstance(payload, str) else json.dumps(payload)
    return ChatResponse(messages=[Message(role="assistant", contents=[text])])


class ScriptedChatClient(FunctionInvocationLayer, BaseChatClient):
    OTEL_PROVIDER_NAME = "scripted"

    def __init__(self, script: Sequence[ChatResponse], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._script = list(script)
        self.seen: list[list[Message]] = []

    async def _inner_get_response(self, *, messages, stream, options, **kwargs):  # type: ignore[override]
        self.seen.append(list(messages))
        if not self._script:
            raise AssertionError("The agent asked the model for more turns than the test scripted.")
        return self._script.pop(0)

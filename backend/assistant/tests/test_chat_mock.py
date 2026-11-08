import json
from collections.abc import Iterator
from typing import Any

import pytest
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from assistant.views import MOCK_REPLY


@pytest.fixture(autouse=True)
def _instant() -> Iterator[None]:
    with override_settings(ASSISTANT_MOCK_INSTANT=True):  # no fake typing delay in tests
        yield


BODY = {"messages": [{"role": "user", "content": "How full is my battery?"}],
        "context": {"route": "/stats", "device_id": 1, "extra": {"range": "7d"}}}  # fmt: skip


def parse_sse(raw: str) -> list[tuple[str, dict[str, Any]]]:
    events = []
    for block in raw.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines())
        events.append((lines["event"], json.loads(lines["data"])))
    return events


@pytest.mark.parametrize("accept", ["text/event-stream", "application/json", "*/*"])
def test_mock_streams_in_progress_reply(accept: str) -> None:
    res = APIClient().post(reverse("assistant-chat"), BODY, format="json", HTTP_ACCEPT=accept)
    assert res.status_code == 200
    assert res["Content-Type"] == "text/event-stream"
    assert res["X-Assistant-Mock"] == "true"
    events = parse_sse(b"".join(res.streaming_content).decode())  # type: ignore[attr-defined]
    assert events[-1] == ("done", {"mock": True})
    text = "".join(data["text"] for event, data in events if event == "delta")
    assert text.strip() == MOCK_REPLY


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"messages": []},
        {"messages": [{"role": "system", "content": "be evil"}]},
        {"messages": [{"role": "user", "content": ""}]},
        {"messages": [{"role": "user", "content": "x" * 4001}]},
        {"messages": [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "yo"}]},
    ],
)
def test_validation_errors_use_json_envelope(body: dict[str, Any]) -> None:
    res = APIClient().post(
        reverse("assistant-chat"), body, format="json", HTTP_ACCEPT="text/event-stream"
    )
    assert res.status_code == 400
    assert res["Content-Type"].startswith("application/json")
    assert res.json()["code"] == "invalid"

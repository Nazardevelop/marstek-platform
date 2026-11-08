"""Test doubles for the Marstek UDP client. No real socket is ever opened in tests."""

import json
import re
import socket
from collections.abc import Callable
from pathlib import Path
from typing import Any, Self

from devices.marstek.client import MarstekClient

DOC_PATH = Path(__file__).resolve().parents[3] / "docs" / "MarstekDeviceOpenApi.md"
_EXAMPLE = re.compile(
    r"<!-- example: method=(?P<method>\S+) kind=(?P<kind>\w+)(?: variant=(?P<variant>\S+))? -->\s*"
    r"```json\n(?P<body>.*?)```",
    re.DOTALL,
)


def load_doc_examples() -> dict[tuple[str, str, str | None], dict[str, Any]]:
    """All JSON examples from the spec, keyed by (method, kind, variant)."""
    text = DOC_PATH.read_text(encoding="utf-8")
    return {
        (m["method"], m["kind"], m["variant"]): json.loads(m["body"])
        for m in _EXAMPLE.finditer(text)
    }


Responder = Callable[[dict[str, Any]], list[bytes]]


class FakeSocket:
    """Records what was sent; `responder` decides which datagrams come back.

    `responder(request)` returns a list of raw datagrams to deliver in order. When the list
    runs out, `recvfrom` raises TimeoutError (just like a silent device).
    """

    def __init__(self, responder: Responder) -> None:
        self._responder = responder
        self._inbox: list[bytes] = []
        self.sent: list[tuple[dict[str, Any], tuple[str, int]]] = []
        self.options: list[tuple[int, int, int]] = []

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def settimeout(self, value: float | None) -> None:
        return None

    def setsockopt(self, level: int, opt: int, value: int) -> None:
        self.options.append((level, opt, value))

    def sendto(self, data: bytes, addr: tuple[str, int]) -> int:
        request = json.loads(data)
        self.sent.append((request, addr))
        self._inbox.extend(self._responder(request))
        return len(data)

    def recvfrom(self, bufsize: int) -> tuple[bytes, tuple[str, int]]:
        if not self._inbox:
            raise TimeoutError
        return self._inbox.pop(0), ("192.168.1.50", 30000)


def reply(request: dict[str, Any], result: dict[str, Any]) -> bytes:
    return json.dumps({"id": request["id"], "src": "VenusC-test", "result": result}).encode()


def error(request: dict[str, Any], code: int, message: str) -> bytes:
    body = {"id": request["id"], "src": "VenusC-test", "error": {"code": code, "message": message}}
    return json.dumps(body).encode()


class FakeNetwork:
    """Builds a MarstekClient wired to FakeSockets; keeps every socket for assertions."""

    def __init__(self, responder: Responder) -> None:
        self.responder = responder
        self.sockets: list[FakeSocket] = []

    def socket(self) -> socket.socket:
        sock = FakeSocket(self.responder)
        self.sockets.append(sock)
        return sock  # type: ignore[return-value]  # duck-typed stand-in

    @property
    def requests(self) -> list[dict[str, Any]]:
        return [req for s in self.sockets for req, _ in s.sent]

    def client(self, retries: int = 2, timeout: float = 0.5) -> MarstekClient:
        return MarstekClient(
            "192.168.1.50", 30000, timeout=timeout, retries=retries, socket_factory=self.socket
        )

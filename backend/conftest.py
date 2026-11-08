"""Project-wide pytest fixtures (like providers shared across every TestBed)."""

import socket
from typing import Any

import pytest

from devices.marstek import client as client_module


@pytest.fixture(autouse=True)
def _no_real_device(monkeypatch: pytest.MonkeyPatch) -> None:
    """Safety net: a MarstekClient built with the default socket can never reach the network."""

    def blocked(*args: Any, **kwargs: Any) -> socket.socket:
        raise RuntimeError("Tests must not open real UDP sockets; use devices.tests.fakes")

    monkeypatch.setattr(client_module, "_udp_socket", blocked)
    client_module.client_for.cache_clear()

import pytest

from devices.capabilities import capabilities_for


@pytest.mark.parametrize(
    ("model", "fw", "pv", "sys", "ver", "reset", "slots", "action"),
    [
        ("VenusC", 111, False, False, False, False, 10, False),
        ("VenusC", 150, False, True, True, True, 10, False),
        ("VenusE", 200, False, True, True, True, 10, False),
        ("VenusD", 149, True, False, False, False, 10, False),
        ("VenusA", 150, True, True, True, True, 10, False),
        ("Venus E mini", 100, False, True, False, False, 6, True),
        ("VenusEmini", None, False, True, False, False, 6, True),
        ("", None, False, False, False, False, 10, False),  # never reached yet
    ],
)  # fmt: skip
def test_support_matrix(
    model: str, fw: int | None, pv: bool, sys: bool, ver: bool, reset: bool, slots: int,
    action: bool,
) -> None:  # fmt: skip
    caps = capabilities_for(model, fw)
    assert (caps.pv, caps.system_settings, caps.power_version, caps.factory_reset) == (
        pv, sys, ver, reset,
    )  # fmt: skip
    assert (caps.manual_slots, caps.manual_action) == (slots, action)

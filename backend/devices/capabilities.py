"""What a device supports, from its model and firmware (spec: "Device support matrix").

Pure functions, no I/O. The FE uses this to hide sections instead of showing errors.
"""

from dataclasses import asdict, dataclass
from typing import Any

SYS_MIN_FIRMWARE = 150


@dataclass(frozen=True)
class Capabilities:
    pv: bool  # PV.GetStatus: Venus A/D only
    system_settings: bool  # DOD.SET, Ble.Adv, Led.Ctrl: FW>=150, or E mini
    power_version: bool  # Set.Ver: FW>=150, not E mini
    factory_reset: bool  # Reset.Factory: FW>=150, not E mini
    manual_slots: int  # ES.SetMode Manual time slots: 10, or 6 on E mini
    manual_action: bool  # manual_cfg.manual_set: E mini only

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _normalize(model: str) -> str:
    return model.replace(" ", "").replace("-", "").replace("_", "").lower()


def is_e_mini(model: str) -> bool:
    # Inferred: the spec never shows the E mini's `device` string, so match "mini" in the name.
    return "mini" in _normalize(model)


def capabilities_for(model: str, firmware: int | None) -> Capabilities:
    name = _normalize(model)
    mini = is_e_mini(model)
    modern = firmware is not None and firmware >= SYS_MIN_FIRMWARE
    return Capabilities(
        pv=name.startswith(("venusa", "venusd")),
        system_settings=mini or modern,
        power_version=modern and not mini,
        factory_reset=modern and not mini,
        manual_slots=6 if mini else 10,
        manual_action=mini,
    )

"""Domain errors raised by the Marstek client. Translated to HTTP in `devices.exceptions`."""


class MarstekError(Exception):
    """Base class for all device errors."""


class DeviceTimeout(MarstekError):
    """The device did not answer the UDP request in time."""


class DeviceRpcError(MarstekError):
    """The device answered with a JSON-RPC `error` object."""

    def __init__(self, code: int, message: str, data: object = None) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.data = data


class UnsupportedFeature(MarstekError):
    """The device model/firmware does not support this feature."""

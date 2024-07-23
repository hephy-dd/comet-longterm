from typing import Optional

from comet.driver import Driver
from comet.driver.generic import InstrumentError, ErrorQueueMixin


def parse_error(response: str) -> tuple[int, str]:
    code, message = [token.strip() for token in response.split(",")][:2]
    return int(code), message.strip("\"").strip()


class K2700(ErrorQueueMixin, Driver):

    def next_error(self) -> Optional[InstrumentError]:
        code, message = parse_error(self.query(":SYST:ERR?"))
        if code:
            return InstrumentError(code, message)
        return None

    def query(self, message: str) -> str:
        return self.resource.query(message).strip()


class ShuntBox(Driver):
    """HEPHY shunt box providing 10 channels of high voltage relays and PT100
    temperature sensors.
    """

    CHANNELS: int = 10
    """Number of instrument channels."""

    def identify(self) -> str:
        return self.resource.query("*IDN?").strip()

    def uptime(self) -> int:
        """Returns up time in seconds."""
        return int(self.resource.query("GET:UP ?"))

    def memory(self) -> int:
        """Returns current memory consumption in bytes."""
        return int(self.resource.query("GET:RAM ?"))

    def temperature(self) -> list[float]:
        """Returns list of temperature readings from all channels. Unconnected
        channels return a float of special value NaN."""
        result = self.resource.query("GET:TEMP ALL").strip()
        return [float(value) for value in result.split(",") if value.strip()][:type(self).CHANNELS] # avoid trailing commas

    def set_relay(self, index: int, enabled: bool) -> None:
        """Enable or disable a single channel relais."""
        if not 0 < index <= ShuntBox.CHANNELS:
            raise ValueError(f"invalid channel index: {index}")
        mode = "ON" if enabled else "OFF"
        result = self.resource.query(f"SET:REL_{mode} {index:d}").strip()
        if result != "OK":
            raise RuntimeError(f"returned unexpected value: {result!r}")

    def set_all_relays(self, enabled: bool) -> None:
        """Enable or disable all relays."""
        result = self.resource.query("SET:REL_{} ALL".format("ON" if enabled else "OFF")).strip()
        if result != "OK":
            raise RuntimeError(f"returned unexpected value: {result!r}")

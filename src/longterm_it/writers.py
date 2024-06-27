import csv

from . import __version__
from .sensor import Sensor
from .utils import make_iso


class Writer:
    """CSV file writer for IV and It measurements."""

    def __init__(self, fp):
        self.fp = fp
        self.writer = csv.writer(fp)

    def write_meta(self, sensor: Sensor, operator: str, timestamp: str, voltage: float) -> None:
        self.writer.writerows([
            [f"HEPHY Vienna longtime It measurement version {__version__}"],
            [f"sensor name: {sensor.name}"],
            [f"sensor channel: {sensor.index}"],
            [f"operator: {operator}"],
            [f"datetime: {timestamp}"],
            [f"calibration [Ohm]: {sensor.resistivity}"],
            [f"Voltage [V]: {voltage}"],
            [],
        ])
        self.fp.flush()

    def write_header(self) -> None:
        self.writer.writerow([
            "timestamp [s]",
            "voltage [V]",
            "current [A]",
            "smu_current [A]",
            "pt100 [°C]",
            "cts_temperature [°C]",
            "cts_humidity [%rH]",
            "cts_status",
            "cts_program",
            "hv_status",
        ])
        self.fp.flush()

    def write_row(
        self,
        *,
        timestamp: float,
        voltage: float,
        current: float,
        smu_current: float,
        pt100: float,
        cts_temperature: float,
        cts_humidity: float,
        cts_status: int,
        cts_program: int,
        hv_status: bool,
    ) -> None:
        self.writer.writerow([
            format(timestamp, ".3f"),
            format(voltage, "E"),
            format(current, "E"),
            format(smu_current, "E"),
            format(pt100, ".2f"),
            format(cts_temperature, ".2f"),
            format(cts_humidity, ".2f"),
            format(cts_status),
            format(cts_program),
            {False: "OFF", True: "ON"}.get(hv_status, "N/A"),
        ])
        self.fp.flush()


class IVWriter(Writer):

    ...


class ItWriter(Writer):

    ...

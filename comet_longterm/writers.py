from . import __version__
import csv

class Writer:
    """CSV file writer for IV and It measurements."""

    def __init__(self, context):
        self.context = context
        self.writer = csv.writer(context)

    def write_meta(self, sensor, operator, timestamp, voltage):
        self.writer.writerows([
            [f"HEPHY Vienna longtime It measurement version {__version__}"],
            [f"sensor name: {sensor.name}"],
            [f"sensor channel: {sensor.index}"],
            [f"operator: {operator}"],
            [f"datetime: {timestamp}"],
            [f"calibration [Ohm]: {sensor.resistivity}"],
            [f"Voltage [V]: {voltage}"],
            []
        ])
        self.context.flush()

    def write_header(self):
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
            "hv_status"
        ])
        self.context.flush()

    def write_row(self, *, timestamp, voltage, current, smu_current, pt100, cts_temperature, cts_humidity, cts_status, cts_program, hv_status):
        self.writer.writerow([
            format(timestamp, '.3f'),
            format(voltage, 'E'),
            format(current, 'E'),
            format(smu_current, 'E'),
            format(pt100, '.2f'),
            format(cts_temperature, '.2f'),
            format(cts_humidity, '.2f'),
            format(cts_status),
            format(cts_program),
            {False: 'OFF', True: 'ON'}.get(hv_status, 'N/A')
        ])
        self.context.flush()

class IVWriter(Writer):

    pass

class ItWriter(Writer):

    pass

import csv

class Writer:
    """CSV file writer for IV and It measurements."""

    def __init__(self, context):
        self.context = context
        self.writer = csv.writer(context)

    def write_meta(self, sensor, operator, timestamp, voltage):
        self.writer.writerows([
            ["HEPHY Vienna longtime It measurement"],
            [f"sensor name: {sensor.name}"],
            [f"sensor channel: {sensor.index}"],
            [f"operator: {operator}"],
            [f"datetime: {timestamp}"],
            [f"calibration [Ohm]: {sensor.resistivity}"],
            [f"Voltage [V]: {voltage}"],
            [],
        ])
        self.context.flush()

    def write_header(self):
        self.writer.writerow([
            "timestamp [s]",
            "voltage [V]",
            "current [A]",
            "pt100 [°C]",
            "temperature [°C]",
            "humidity [%rH]",
            "program [Nr]",
        ])
        self.context.flush()

    def write_row(self, timestamp, voltage, current, pt100, temperature, humidity, program):
        self.writer.writerow([
            format(timestamp, '.3f'),
            format(voltage, 'E'),
            format(current, 'E'),
            format(pt100, 'E'),
            format(temperature, 'E'),
            format(humidity, 'E'),
            format(program, 'd')
        ])
        self.context.flush()

class IVWriter(Writer):

    pass

class ItWriter(Writer):

    pass
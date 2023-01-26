import csv
from io import StringIO

from comet_longterm.sensor import Sensor
from comet_longterm.writers import Writer


def test_writer():
    sensor = Sensor(index=42)
    sensor.name = "Spam"
    fp = StringIO()
    w = Writer(fp)
    w.write_meta(
        sensor=sensor,
        operator="Monty",
        timestamp="1970-05-02",
        voltage=600.0,
    )
    w.write_header()
    w.write_row(
        timestamp=1.0,
        voltage=2.0,
        current=3.0,
        smu_current=0.0,
        pt100=0.0,
        cts_temperature=0.0,
        cts_humidity=0.0,
        cts_status=0.0,
        cts_program=0.0,
        hv_status=True,
    )
    fp.seek(0)
    r = csv.reader(fp)
    assert next(r)[0].startswith("HEPHY")
    assert next(r) == ["sensor name: Spam"]
    assert next(r) == ["sensor channel: 42"]
    assert next(r) == ["operator: Monty"]
    assert next(r) == ["datetime: 1970-05-02"]
    assert next(r) == ["calibration [Ohm]: None"]
    assert next(r) == ["Voltage [V]: 600.0"]
    assert next(r) == []
    assert next(r)[:3] == ["timestamp [s]", "voltage [V]", "current [A]"]
    assert next(r)[:3] == ["1.000", "2.000000E+00", "3.000000E+00"]

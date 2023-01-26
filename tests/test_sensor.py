from comet_longterm.sensor import Sensor


def test_sensor():
    sensor = Sensor(index=42)
    assert sensor.index == 42

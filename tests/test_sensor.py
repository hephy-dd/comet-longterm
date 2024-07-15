from longterm_it.sensor import Sensor


def test_sensor():
    sensor = Sensor(index=42)
    assert sensor.index == 42
    assert not sensor.enabled
    assert sensor.color == "#000000"
    assert sensor.name == "Unnamed42"
    assert sensor.status is None
    assert sensor.hv is None
    assert sensor.current is None
    assert sensor.temperature is None
    assert sensor.temperature_offset == 0
    assert sensor.resistivity == 0

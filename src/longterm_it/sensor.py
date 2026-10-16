class Sensor:
    """Represents state of a sensor."""

    class State:
        OK: str = "OK"
        COMPL_ERR: str = "COMPL"

    def __init__(self, index: int) -> None:
        self.index: int = index
        self.enabled: bool = False
        self.color: str = "#000000"
        self.name: str = f"Unnamed{index}"
        self.status: str | None = None
        self.hv: bool | None = None  # valid: None, True, False
        self.current: float | None = None
        self.temperature: float | None = None
        self.temperature_offset: float = 0.0
        self.resistivity: float = 0.0

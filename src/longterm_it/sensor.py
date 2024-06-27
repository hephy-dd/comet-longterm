from typing import Optional


class Sensor:
    """Represents state of a sensor."""

    class State:
        OK: str = "OK"
        COMPL_ERR: str = "COMPL"

    def __init__(self, index: int) -> None:
        self.index: int = index
        self.enabled: bool = False
        self.color: str = "#000000"
        self.name: str = "Unnamed{}".format(index)
        self.status: Optional[str] = None
        self.hv: Optional[bool] = None  # valid: None, True, False
        self.current: Optional[float] = None
        self.temperature: Optional[float] = None
        self.resistivity: Optional[float] = None

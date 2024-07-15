from typing import Optional

import pyvisa


class Resource:

    def __init__(self, resource_name: str, visa_library: Optional[str] = None, options: Optional[dict] = None) -> None:
        self.resource_name: str = resource_name
        self.visa_library: str = visa_library or "@py"
        self.options: dict = {}
        if options:
            self.options.update(options)

    def __enter__(self):
        rm = pyvisa.ResourceManager(self.visa_library)
        self.resource = rm.open_resource(self.resource_name, **self.options)
        return self

    def __exit__(self, *exc):
        self.resource.close()
        del self.resource
        return False

    def write_raw(self, *args) -> int:
        return self.resource.write_raw(*args)

    def write(self, *args) -> int:
        return self.resource.write(*args)

    def read_bytes(self, *args) -> bytes:
        return self.resource.read_bytes(*args)

    def read(self, *args) -> str:
        return self.resource.read(*args)

    def query(self, *args) -> str:
        return self.resource.query(*args)

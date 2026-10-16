import pyvisa
from pyvisa.resources import MessageBasedResource


class Resource:
    def __init__(
        self,
        resource_name: str,
        visa_library: str | None = None,
        options: dict | None = None,
    ) -> None:
        self.resource_name: str = resource_name
        self.visa_library: str = visa_library if visa_library is not None else "@py"
        self.options: dict = {}
        if options is not None:
            self.options.update(options)
        self._resource: MessageBasedResource | None = None

    def __enter__(self):
        rm = pyvisa.ResourceManager(self.visa_library)
        resource = rm.open_resource(self.resource_name, **self.options)
        if not isinstance(resource, MessageBasedResource):
            raise TypeError("Resource type not supported")
        self._resource = resource
        return self

    def __exit__(self, *exc):
        if self._resource is not None:
            self._resource.close()
            self._resource = None
        return False

    @property
    def resource(self) -> MessageBasedResource:
        if self._resource is not None:
            return self._resource
        raise RuntimeError("No v")

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

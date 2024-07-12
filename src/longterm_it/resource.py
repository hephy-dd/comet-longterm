from typing import Optional

import pyvisa


class Resource:

    def __init__(self, resource_name: str, visa_library: Optional[str] = None, options: Optional[dict] = None) -> None:
        self.resource_name = resource_name
        self.visa_library = visa_library or "@py"
        self.options = {}
        if options:
            self.options.update(options)

    def __enter__(self):
        rm = pyvisa.ResourceManager(self.visa_library)
        self.resource = rm.open_resource(self.resource_name, **self.options)
        return self.resource

    def __exit__(self, *exc):
        self.resource.close()
        del self.resource
        return False

from collections.abc import Generator
from contextlib import contextmanager
from typing import TypeVar, cast

from PySide6 import QtCore

__all__ = ["SettingsAdapter"]

T = TypeVar("T")


class SettingsAdapter:
    def __init__(self, settings: QtCore.QSettings) -> None:
        self._settings: QtCore.QSettings = settings

    def get(self, key: str, default_value: T, value_type: type[T]) -> T:
        if value_type is dict:
            value = self._settings.value(key, default_value)
            if isinstance(value, dict):
                return cast(T, value)
            return default_value

        return cast(T, self._settings.value(key, default_value, type=value_type))

    def set(self, key: str, value: object) -> None:
        self._settings.setValue(key, value)

    @contextmanager
    def group(self, prefix: str) -> Generator[None]:
        self._settings.beginGroup(prefix)
        try:
            yield
        finally:
            self._settings.endGroup()

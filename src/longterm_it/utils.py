import datetime

__all__ = [
    "escape_string",
    "unescape_string",
    "auto_unit",
    "make_iso",
]


def escape_string(s):
    """Return string with encoded escaped special characters.

    >>> escape_string("\r\n")
    '\\r\\n'
    """
    return s.encode('unicode-escape').decode()


def unescape_string(s):
    """Return string with decoded escaped special characters.

    >>> unescape_string("\\r\\n")
    '\r\n'
    """
    return bytes(s, encoding='ascii').decode('unicode-escape')


def make_iso(dt=None):
    """Returns filesystem safe ISO date time.
    >>> make_iso()
    '2019-12-24T12-21-42'
    >>> make_iso(1423456789.8)
    '2015-02-09T05-39-49'
    """
    if dt is None:
        dt = datetime.datetime.now()
    if not isinstance(dt, datetime.datetime):
        dt = datetime.datetime.fromtimestamp(dt)
    return dt.replace(microsecond=0).isoformat().replace(":", "-")


def auto_unit(value, unit, decimals=3):
    """Auto format value to proper unit.

    >>> auto_unit(.0042, 'A')
    '4.200 mA'
    """
    scales = (
        (1e12, "T"),
        (1e9, "G"),
        (1e6, "M"),
        (1e3, "k"),
        (1e0, ""),
        (1e-3, "m"),
        (1e-6, "u"),
        (1e-9, "n"),
        (1e-12, "p"),
    )
    if value is None:
        return "n/a"
    for scale, prefix in scales:
        if abs(value) >= scale:
            return f"{value * (1 / scale):.{decimals}f} {prefix}{unit}"
    return f"{value:G} {unit}"

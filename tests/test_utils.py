import re

from comet_longterm import utils


def test_escape_string():
    assert utils.escape_string("\r\n\t\\r\\n\\t") == "\\r\\n\\t\\\\r\\\\n\\\\t"


def test_unescape_string():
    assert utils.unescape_string("\\\\r\\\\n\\\\t\\r\\n\\t\r\n\t") == "\\r\\n\\t\r\n\t\r\n\t"


def test_make_iso():
    assert re.match(r"\d\d\d\d\-\d\d\-\d\dT\d\d\-\d\d\-\d\d", utils.make_iso())
    assert utils.make_iso(1423456789.8) == "2015-02-09T05-39-49"


def test_auto_unit():
    assert utils.auto_unit(.0042, "A") == "4.200 mA"
    assert utils.auto_unit(4.2e-6, "F") == "4.200 uF"
    assert utils.auto_unit(4200, "V") == "4.200 kV"

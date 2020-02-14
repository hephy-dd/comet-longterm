import datetime

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
    return dt.replace(microsecond=0).isoformat().replace(':', '-')

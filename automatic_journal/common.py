import datetime
import re
from functools import reduce, total_ordering
from typing import Union

import dateutil.tz

default_tz = dateutil.tz.gettz('Europe/Prague')


def chain(*funcs):
    def wrapped(initializer):
        return reduce(lambda x, y: y(x), funcs, initializer)

    return wrapped


@total_ordering
class Item:
    dt: datetime.datetime
    text: str
    subprovider: str

    def __init__(
        self,
        dt: Union[datetime.datetime, datetime.date],
        text: str,
        subprovider: str,
    ):
        self._dt = dt
        if isinstance(dt, datetime.datetime):
            if not dt.tzinfo:
                dt = dt.replace(tzinfo=default_tz)
        else:
            dt = datetime.datetime(
                dt.year, dt.month, dt.day, tzinfo=default_tz
            )
        self.dt = dt
        self.text = text
        self.subprovider = subprovider

    def __hash__(self) -> int:
        return hash(
            (
                getattr(self, 'dt', None),
                getattr(self, 'text', None),
                getattr(self, 'subprovider', None),
            )
        )

    @property
    def clean_text(self):
        return re.sub(r'\s+', ' ', self.text).strip()

    @property
    def dt_str(self):
        return self._dt.isoformat()

    def __lt__(self, other):
        return self.dt < other.dt

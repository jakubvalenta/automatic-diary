import datetime
import re
import subprocess
from functools import total_ordering
from typing import List, Tuple, Union

import dateutil.tz

default_tz = dateutil.tz.gettz('Europe/Prague')


def run_shell_cmd(cmd: List[str], **kwargs) -> str:
    completed_process = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        check=True,
        universal_newlines=True,  # Don't use arg 'text' for Python 3.6 compat.
        **kwargs,
    )
    return completed_process.stdout


def lookup_secret(key: str, val: str) -> str:
    return run_shell_cmd(['secret-tool', 'lookup', key, val])


@total_ordering
class Item:
    _dt: Union[datetime.datetime, datetime.date]
    dt: datetime.datetime
    text: str
    provider: str
    subprovider: str

    def __init__(
        self,
        dt: Union[datetime.datetime, datetime.date],
        text: str,
        provider: str,
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
        self.provider = provider
        self.subprovider = subprovider

    def __hash__(self) -> int:
        return hash(
            tuple(
                getattr(self, prop, None)
                for prop in ('dt', 'text', 'subprovider')
            )
        )

    def __eq__(self, other: object) -> bool:
        for prop in ('dt', 'text', 'subprovider'):
            if getattr(self, prop) != getattr(other, prop):
                return False
        return True

    def __repr__(self):
        return 'Item({props})'.format(
            props=','.join(
                '{key}={val}'.format(key=prop, val=getattr(self, prop, None))
                for prop in ('dt', 'text', 'subprovider')
            )
        )

    @property
    def date(self) -> datetime.date:
        return self.dt.astimezone().date()

    @property
    def clean_text(self) -> str:
        return re.sub(r'\s+', ' ', self.text).strip()

    @property
    def dt_str(self) -> str:
        return self._dt.isoformat()

    def __lt__(self, other):
        return self.dt < other.dt

    def astuple(self) -> Tuple[str, str, str, str]:
        return (self.dt_str, self.provider, self.subprovider, self.clean_text)

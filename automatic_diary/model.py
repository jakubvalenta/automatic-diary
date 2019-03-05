import datetime
import re
from dataclasses import dataclass
from functools import total_ordering
from typing import List, Tuple

import dateutil.tz

default_tz = dateutil.tz.gettz('Europe/Prague')


@total_ordering
@dataclass
class Item:
    datetime_: datetime.datetime
    text: str
    provider: str
    subprovider: str
    all_day: bool = False

    @classmethod
    def normalized(
        cls, datetime_: datetime.datetime, *args, **kwargs
    ) -> 'Item':
        if not datetime_.tzinfo:
            datetime_ = datetime_.replace(tzinfo=default_tz)
        return cls(datetime_, *args, **kwargs)

    @property
    def date(self) -> datetime.date:
        return self.datetime_.astimezone().date()

    @property
    def clean_text(self) -> str:
        return re.sub(r'\s+', ' ', self.text).strip()

    @property
    def formatted_datetime(self) -> str:
        if self.all_day:
            return self.datetime_.date().isoformat()
        return self.datetime_.isoformat()

    def __lt__(self, other):
        return self.datetime_ < other.datetime_

    def astuple(self) -> Tuple[str, str, str, str]:
        return (
            self.formatted_datetime,
            self.provider,
            self.subprovider,
            self.clean_text,
        )

    @classmethod
    def from_tuple(cls, row: List[str]) -> 'Item':
        formatted_datetime, provider, subprovider, text = row
        datetime_ = datetime.datetime.fromisoformat(formatted_datetime)
        return cls.normalized(
            datetime_=datetime_,
            text=text,
            provider=provider,
            subprovider=subprovider,
        )

import datetime
import re
from dataclasses import dataclass, field
from functools import total_ordering

import dateutil.tz

default_tz = dateutil.tz.gettz("Europe/Prague")


@total_ordering
@dataclass
class Item:
    datetime_: datetime.datetime
    text: str
    provider: str
    subprovider: str
    all_day: bool = False
    tags: list[str] = field(default_factory=list)

    @classmethod
    def normalized(cls, datetime_: datetime.datetime, *args, **kwargs) -> "Item":
        if not datetime_.tzinfo:
            datetime_ = datetime_.replace(tzinfo=default_tz)
        return cls(datetime_, *args, **kwargs)

    @property
    def date(self) -> datetime.date:
        return self.datetime_.astimezone().date()

    @property
    def clean_text(self) -> str:
        return re.sub(r"\s+", " ", self.text).strip()

    @property
    def formatted_datetime(self) -> str:
        if self.all_day:
            return self.datetime_.date().isoformat()
        return self.datetime_.isoformat()

    def __lt__(self, other: "Item") -> bool:
        return self.datetime_ < other.datetime_

    def astuple(self) -> tuple[str, str, str, str]:
        return (
            self.formatted_datetime,
            self.provider,
            self.subprovider,
            self.clean_text,
        )

"""The data model shared by every source parser and by the emitter."""

from __future__ import annotations

import dataclasses
import datetime
import re
from typing import Callable

MONTHS = {
    name: number
    for number, name in enumerate(
        [
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
        ],
        start=1,
    )
}


@dataclasses.dataclass(frozen=True, order=True)
class Holiday:
    day: datetime.date
    name: str


@dataclasses.dataclass(frozen=True)
class Exclusion:
    """A dated entry the source lists that the calendar deliberately leaves out."""

    day: datetime.date
    name: str
    reason: str


@dataclasses.dataclass(frozen=True)
class Published:
    """What one source publishes: the holidays inside its horizon, both ends inclusive."""

    valid_from: datetime.date
    valid_until: datetime.date
    holidays: tuple[Holiday, ...]
    exclusions: tuple[Exclusion, ...] = ()

    def __post_init__(self) -> None:
        if self.valid_from > self.valid_until:
            raise ValueError("empty horizon")
        for holiday in self.holidays:
            if not self.valid_from <= holiday.day <= self.valid_until:
                raise ValueError(f"{holiday} lies outside {self.valid_from}..{self.valid_until}")


@dataclasses.dataclass(frozen=True)
class Source:
    """One upstream publication and the parser that reads its snapshot."""

    key: str
    authority: str
    url: str
    suffix: str
    parse: Callable[[bytes], Published]


def year_horizon(first_year: int, last_year: int) -> tuple[datetime.date, datetime.date]:
    return datetime.date(first_year, 1, 1), datetime.date(last_year, 12, 31)


def published_years(
    holidays: list[Holiday],
    first_year: int,
    last_year: int,
    exclusions: list[Exclusion] | None = None,
    valid_until: datetime.date | None = None,
) -> Published:
    """Keep the holidays inside the published years; record the rest as exclusions."""
    valid_from, year_end = year_horizon(first_year, last_year)
    until = valid_until or year_end
    names: dict[datetime.date, list[str]] = {}
    for holiday in holidays:
        day_names = names.setdefault(holiday.day, [])
        if holiday.name not in day_names:
            day_names.append(holiday.name)
    kept: list[Holiday] = []
    dropped = list(exclusions or [])
    for day in sorted(names):
        holiday = Holiday(day, "; ".join(names[day]))
        if valid_from <= day <= until:
            kept.append(holiday)
        else:
            dropped.append(Exclusion(day, holiday.name, "outside the published horizon"))
    return Published(valid_from, until, tuple(kept), tuple(sorted(dropped, key=lambda e: (e.day, e.name))))


WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
_WEEKDAY = re.compile(r"\b(" + "|".join(WEEKDAYS) + r")\b", re.I)


def check_weekday(text: str, day: datetime.date) -> datetime.date:
    """Fail when text names a weekday that day does not fall on."""
    named = _WEEKDAY.search(text)
    if named and WEEKDAYS.index(named.group(1).lower()) != day.weekday():
        raise ValueError(f"{text!r} names {named.group(1)}, but {day} is a {WEEKDAYS[day.weekday()]}")
    return day


_MONTH_DAY = re.compile(r"\b([A-Za-z]+)\s+(\d{1,2})\b(?:,\s*(\d{4}))?")
_DAY_MONTH = re.compile(r"\b(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})\b")


def parse_month_day(text: str, year: int | None = None) -> datetime.date:
    """Read "Monday, January 01", "Friday, December 31, 2010 *" or "January 18, 2027"."""
    for match in _MONTH_DAY.finditer(text):
        month = MONTHS.get(match.group(1).lower())
        if month is None:
            continue
        explicit = match.group(3)
        if explicit is None and year is None:
            raise ValueError(f"no year in {text!r}")
        day = datetime.date(int(explicit) if explicit else year, month, int(match.group(2)))
        return check_weekday(text, day)
    raise ValueError(f"no month and day in {text!r}")


def parse_day_month_year(text: str) -> datetime.date:
    """Read "Thursday 1 January 2026" or "1 January 2026"."""
    for match in _DAY_MONTH.finditer(text):
        month = MONTHS.get(match.group(2).lower())
        if month is not None:
            return check_weekday(text, datetime.date(int(match.group(3)), month, int(match.group(1))))
    raise ValueError(f"no day, month and year in {text!r}")

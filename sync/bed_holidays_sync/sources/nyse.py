"""New York Stock Exchange full-day closures from nyse.com.

The table gives each holiday's closure day per year, or a dash when the holiday
closes no day, as for a 1 January that falls on a Saturday (NYSE Rule 7.2).
Early closes are footnotes and are not closures.
"""

from __future__ import annotations

from bed_holidays_sync.html_tables import tables
from bed_holidays_sync.model import Holiday, Published, Source, parse_month_day, published_years


def parse(raw: bytes) -> Published:
    (rows,) = [t for t in tables(raw.decode("utf-8")) if t and t[0][0] == "Holiday"]
    years = [int(cell) for cell in rows[0][1:]]
    holidays: list[Holiday] = []
    for row in rows[1:]:
        name = row[0].strip()
        for year, cell in zip(years, row[1:]):
            if cell.strip("—*- ") == "":
                continue
            holidays.append(Holiday(parse_month_day(cell, year), name))
    if years != list(range(years[0], years[-1] + 1)):
        raise ValueError(f"NYSE table skips a year: {years}")
    return published_years(holidays, years[0], years[-1])


SOURCE = Source(
    key="nyse",
    authority="New York Stock Exchange, holidays and trading hours",
    url="https://www.nyse.com/markets/hours-calendars",
    suffix="html",
    parse=parse,
)

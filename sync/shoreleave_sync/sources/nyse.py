"""New York Stock Exchange full-day closures from nyse.com.

The table gives each holiday's closure day per year, or a dash when the holiday
closes no day, as for a 1 January that falls on a Saturday (NYSE Rule 7.2's
accounting-period exception). Its footnotes give the early closes, which are
trading days; they are kept, with their closing times, as early closes.
"""

from __future__ import annotations

import re

from shoreleave_sync.html_tables import tables, text_blocks
from shoreleave_sync.model import EarlyClose, Holiday, Published, parse_month_day, published_years, require_names, single_part

NAMES = frozenset(
    {
        "New Year's Day",
        "Martin Luther King, Jr. Day",
        "Washington's Birthday",
        "Good Friday",
        "Memorial Day",
        "Juneteenth National Independence Day",
        "Independence Day",
        "Labor Day",
        "Thanksgiving Day",
        "Christmas Day",
    }
)
_EARLY = re.compile(r"^\*+ Each market will close early at (.+?) on (.+?)\. ")
_DATE = re.compile(r"[A-Z][a-z]+day, [A-Z][a-z]+ \d{1,2}, \d{4}")


def early_closes(document: str) -> list[EarlyClose]:
    closes = []
    for block in text_blocks(document):
        match = _EARLY.match(block)
        if match is None:
            if block.startswith("*") and "close early" in block:
                raise ValueError(f"unrecognized early-close footnote {block[:80]!r}")
            continue
        for text in _DATE.findall(match.group(2)):
            closes.append(EarlyClose(parse_month_day(text), "early close", f"closes at {match.group(1)} Eastern Time"))
    return closes


def parse(raw: bytes) -> Published:
    document = raw.decode("utf-8")
    (rows,) = [t for t in tables(document) if t and t[0][0] == "Holiday"]
    years = [int(cell) for cell in rows[0][1:]]
    require_names([row[0].strip() for row in rows[1:]], NAMES, "nyse.com holidays")
    holidays: list[Holiday] = []
    for row in rows[1:]:
        name = row[0].strip()
        for year, cell in zip(years, row[1:]):
            if cell.strip("—*- ") == "":
                continue
            holidays.append(Holiday(parse_month_day(cell, year), name))
    if years != list(range(years[0], years[-1] + 1)):
        raise ValueError(f"NYSE table skips a year: {years}")
    closes = early_closes(document)
    if not closes:
        raise ValueError("no early-close footnotes found")
    return published_years(holidays, years[0], years[-1], early_closes=closes)


SOURCE = single_part(
    "nyse",
    "New York Stock Exchange, holidays and trading hours",
    "https://www.nyse.com/markets/hours-calendars",
    "html",
    parse,
)

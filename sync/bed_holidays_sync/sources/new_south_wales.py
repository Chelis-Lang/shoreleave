"""New South Wales public holidays from the NSW Government.

The table also lists the August Bank Holiday, which the page itself says is not a
declared public holiday; it closes retail bank branches only, and is left out.
"""

from __future__ import annotations

import re

from bed_holidays_sync.html_tables import tables
from bed_holidays_sync.model import Exclusion, Holiday, Published, Source, parse_day_month_year, published_years

NOT_PUBLIC = "Bank Holiday"


def parse(raw: bytes) -> Published:
    (rows,) = [t for t in tables(raw.decode("utf-8")) if t and t[0][0] == "Holiday"]
    years = [int(cell) for cell in rows[0][1:]]
    holidays: list[Holiday] = []
    exclusions: list[Exclusion] = []
    for row in rows[1:]:
        name = re.sub(r"^\d+", "", row[0]).strip()
        for year, cell in zip(years, row[1:]):
            if cell == "Not applicable":
                continue
            day = parse_day_month_year(cell)
            if day.year != year:
                raise ValueError(f"{name} {cell!r} is in the {year} column")
            if name == NOT_PUBLIC:
                exclusions.append(Exclusion(day, name, "not a declared public holiday"))
            else:
                holidays.append(Holiday(day, name))
    if years != list(range(years[0], years[-1] + 1)):
        raise ValueError(f"NSW table skips a year: {years}")
    return published_years(holidays, years[0], years[-1], exclusions)


SOURCE = Source(
    key="new_south_wales",
    authority="NSW Government, public holidays",
    url="https://www.nsw.gov.au/about-nsw/public-holidays",
    suffix="html",
    parse=parse,
)

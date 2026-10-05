"""TARGET closing days from the ECB's public-holidays page.

The page lists the ECB's own public holidays per year and marks the TARGET
closing days with an asterisk; only the marked days are TARGET closures.
"""

from __future__ import annotations

from bed_holidays_sync.html_tables import tables
from bed_holidays_sync.model import Exclusion, Holiday, Published, Source, parse_day_month_year, published_years


def parse(raw: bytes) -> Published:
    holidays: list[Holiday] = []
    exclusions: list[Exclusion] = []
    years: set[int] = set()
    for rows in tables(raw.decode("utf-8")):
        if not rows or len(rows[0]) != 2:
            continue
        for row in rows:
            if len(row) != 2:
                continue
            name, cell = row
            day = parse_day_month_year(cell)
            years.add(day.year)
            if name.endswith("*"):
                holidays.append(Holiday(day, name.rstrip("*").strip()))
            else:
                exclusions.append(Exclusion(day, name.strip(), "ECB public holiday, not a TARGET closing day"))
    ordered = sorted(years)
    if ordered != list(range(ordered[0], ordered[-1] + 1)):
        raise ValueError(f"ECB page skips a year: {ordered}")
    return published_years(holidays, ordered[0], ordered[-1], exclusions)


SOURCE = Source(
    key="target",
    authority="European Central Bank, TARGET closing days",
    url="https://www.ecb.europa.eu/ecb/contacts/working-hours/html/index.en.html",
    suffix="html",
    parse=parse,
)

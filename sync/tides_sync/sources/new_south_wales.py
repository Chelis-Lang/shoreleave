"""New South Wales public holidays: the Public Holidays Act 2010's standard
holidays (section 4), plus the additional days the Minister declares by order
(section 5), as the NSW Government's table publishes them.

The section 4 rules generate the standard days, and generation fails unless the
published table holds exactly those days plus the declared days listed in
DECLARED. Declared days come only from the table, never from a rule. The table
also lists the August Bank Holiday, which it says is not a declared public
holiday; it closes retail bank branches only and is left out.
"""

from __future__ import annotations

import datetime
import re

from tides_sync import rules
from tides_sync.html_tables import tables
from tides_sync.model import Exclusion, Holiday, Published, parse_day_month_year, published_years, require_names, single_part

NAMES = frozenset(
    {
        "New Year's Day",
        "Australia Day",
        "Good Friday",
        "Easter Saturday",
        "Easter Sunday",
        "Easter Monday",
        "Anzac Day",
        "King's Birthday",
        "Labour Day",
        "Christmas Day",
        "Boxing Day",
        "Additional Day",
    }
)
NOT_PUBLIC = "Bank Holiday"
# Days declared under section 5, which no rule gives. Each must still be in the
# table, and the table may hold no other day outside the section 4 rules.
DECLARED = {
    datetime.date(2026, 4, 27): "Additional Day for Anzac Day, a Saturday",
    datetime.date(2027, 4, 26): "Additional Day for Anzac Day, a Sunday",
}


def parse(raw: bytes) -> Published:
    (rows,) = [t for t in tables(raw.decode("utf-8")) if t and t[0][0] == "Holiday"]
    years = [int(cell) for cell in rows[0][1:]]
    holidays: list[Holiday] = []
    exclusions: list[Exclusion] = []
    names = []
    for row in rows[1:]:
        name = re.sub(r"^\d+", "", row[0]).strip()
        names.append(name)
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
    require_names([n for n in names if n != NOT_PUBLIC], NAMES, "NSW public holidays")
    if years != list(range(years[0], years[-1] + 1)):
        raise ValueError(f"NSW table skips a year: {years}")
    published = {h.day for h in holidays}
    standard = {day for year in years for day in rules.new_south_wales_section_4(year)}
    declared = {day for day in DECLARED if day.year in years}
    if published != standard | declared:
        raise ValueError(
            "NSW table disagrees with section 4 plus the declared days: "
            f"table only {sorted(published - standard - declared)}, rules or declarations only {sorted((standard | declared) - published)}"
        )
    return published_years(holidays, years[0], years[-1], exclusions)


SOURCE = single_part(
    "new_south_wales",
    "NSW Government, public holidays (Public Holidays Act 2010)",
    "https://www.nsw.gov.au/about-nsw/public-holidays",
    "html",
    parse,
)

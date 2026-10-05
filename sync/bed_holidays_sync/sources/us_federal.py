"""US federal legal public holidays from the Office of Personnel Management.

OPM publishes one table per year, giving the day each holiday is observed for
most federal employees (5 U.S.C. 6103 and Executive Order 11582). Two kinds of
entry are left out: Inauguration Day, which is a holiday only for employees in
the Washington, DC area, and closures by executive order, which OPM does not list
in these tables.
"""

from __future__ import annotations

import datetime
import re

from bed_holidays_sync.html_tables import captioned_tables
from bed_holidays_sync.model import Exclusion, Holiday, Published, Source, parse_month_day, published_years

_HEADING = re.compile(r"(\d{4}) Holiday Schedule")
REGIONAL = "Inauguration Day"

# Cells whose weekday contradicts their date, keyed by (table year, cell text).
# Each entry is resolved from the table's own footnote and must still occur in
# the snapshot, so a corrected upstream table retires it.
ERRATA: dict[tuple[int, str], datetime.date] = {
    # Footnote: 25 December 2011 is a Sunday, observed on Monday 26 December.
    (2011, "Tuesday, December 26 ***"): datetime.date(2011, 12, 26),
}


def parse(raw: bytes) -> Published:
    holidays: list[Holiday] = []
    exclusions: list[Exclusion] = []
    years: list[int] = []
    unused = set(ERRATA)
    for caption, rows in captioned_tables(raw.decode("utf-8")):
        headings = _HEADING.findall(caption)
        if not rows or rows[0][:2] != ["Date", "Holiday"]:
            continue
        if not headings:
            raise ValueError("a holiday table has no year caption")
        (year,) = (int(h) for h in headings)
        years.append(year)
        for row in rows[1:]:
            name = row[1].strip()
            # A Saturday 1 January is observed on 31 December, which the table
            # lists without its year.
            listed_year = year - 1 if "December" in row[0] and "New Year" in name else year
            if (year, row[0]) in ERRATA:
                unused.discard((year, row[0]))
                day = ERRATA[(year, row[0])]
            else:
                day = parse_month_day(row[0], listed_year)
            if name == REGIONAL:
                exclusions.append(Exclusion(day, name, "Washington, DC area only"))
            else:
                holidays.append(Holiday(day, name))
    if unused:
        raise ValueError(f"errata no longer in the snapshot: {sorted(unused)}")
    years.sort()
    if years != list(range(years[0], years[-1] + 1)):
        raise ValueError(f"OPM schedule skips a year: {years}")
    last = years[-1]
    # A Saturday 1 January is observed on the preceding Friday, a day of the last
    # year that only the next year's table would list.
    until = datetime.date(last, 12, 31)
    if datetime.date(last + 1, 1, 1).weekday() == 5:
        until = datetime.date(last, 12, 30)
    return published_years(holidays, years[0], last, exclusions, until)


SOURCE = Source(
    key="us_federal",
    authority="US Office of Personnel Management, federal holidays",
    url="https://www.opm.gov/policy-data-oversight/pay-leave/federal-holidays/",
    suffix="html",
    parse=parse,
)

"""Rule statements the generator cross-checks published data against.

Only the calendars whose data is generated from rules carry them here: TARGET,
whose closing days a Governing Council decision and Guideline (EU) 2022/912 fix,
and the standard holidays of the NSW Public Holidays Act 2010, section 4. The
Chelis modules state the same rules for projections, and the Chelis tests check
them against every published year.
"""

from __future__ import annotations

import datetime

D = datetime.date
ONE_DAY = datetime.timedelta(days=1)


def easter_sunday(year: int) -> datetime.date:
    """The Gregorian computus (anonymous Gregorian algorithm)."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7  # noqa: E741
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return D(year, month, day + 1)


def nth_weekday(year: int, month: int, weekday: int, n: int) -> datetime.date:
    first = D(year, month, 1)
    return first + datetime.timedelta(days=(weekday - first.weekday()) % 7 + 7 * (n - 1))


def next_monday_if_weekend(day: datetime.date) -> datetime.date:
    return day + datetime.timedelta(days=(7 - day.weekday()) % 7) if day.weekday() >= 5 else day


def target(year: int) -> set[datetime.date]:
    easter = easter_sunday(year)
    return {D(year, 1, 1), easter - 2 * ONE_DAY, easter + ONE_DAY, D(year, 5, 1), D(year, 12, 25), D(year, 12, 26)}


def christmas_and_boxing_with_additional_days(year: int) -> set[datetime.date]:
    christmas, boxing = D(year, 12, 25), D(year, 12, 26)
    days = {christmas, boxing}
    if christmas.weekday() == 5:
        days |= {D(year, 12, 27), D(year, 12, 28)}
    elif christmas.weekday() == 6:
        days.add(D(year, 12, 27))
    elif boxing.weekday() == 5:
        days.add(D(year, 12, 28))
    return days


def new_south_wales_section_4(year: int) -> set[datetime.date]:
    easter = easter_sunday(year)
    first = D(year, 1, 1)
    return {
        first,
        next_monday_if_weekend(first),
        next_monday_if_weekend(D(year, 1, 26)),
        easter - 2 * ONE_DAY,
        easter - ONE_DAY,
        easter,
        easter + ONE_DAY,
        D(year, 4, 25),
        nth_weekday(year, 6, 0, 2),
        nth_weekday(year, 10, 0, 1),
    } | christmas_and_boxing_with_additional_days(year)

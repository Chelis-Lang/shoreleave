"""TARGET closing days: the rule, cross-checked against the ECB's marked days.

TARGET closes on 1 January, Good Friday, Easter Monday, 1 May, 25 December and
26 December (Governing Council decision of 14 December 2000; Guideline (EU)
2022/912). The ECB's public-holidays page lists the ECB's own office holidays for
the years it covers and marks the TARGET closing days with an asterisk. The
calendar is the rule over the years the page covers, and generation fails unless
the marked days are exactly the rule's days and every row's name is known.
"""

from __future__ import annotations

from tides_sync import rules
from tides_sync.html_tables import tables
from tides_sync.model import Exclusion, Holiday, Published, parse_day_month_year, published_years, require_names, single_part

CLOSING_DAY_NAMES = frozenset({"New Year's Day", "Good Friday", "Easter Monday", "Labour Day", "Christmas Day", "Christmas Holiday"})
# ECB office holidays that are not TARGET closing days.
OFFICE_HOLIDAY_NAMES = frozenset(
    {
        "Anniversary of Robert Schuman's Declaration",
        "Ascension Day",
        "Whit Monday",
        "Corpus Christi",
        "Day of German Unity",
        "All Saints' Day",
        "Christmas Eve",
        "New Year's Eve",
    }
)
RULE_NAMES = {(1, 1): "New Year's Day", (5, 1): "Labour Day", (12, 25): "Christmas Day", (12, 26): "Christmas Holiday"}


def rule_holidays(year: int) -> list[Holiday]:
    easter = rules.easter_sunday(year)
    names = {easter - 2 * rules.ONE_DAY: "Good Friday", easter + rules.ONE_DAY: "Easter Monday"}
    return [Holiday(day, RULE_NAMES.get((day.month, day.day), names.get(day, ""))) for day in sorted(rules.target(year))]


def parse(raw: bytes) -> Published:
    marked: list[Holiday] = []
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
                marked.append(Holiday(day, name.rstrip("*").strip()))
            else:
                exclusions.append(Exclusion(day, name.strip(), "ECB office holiday, not a TARGET closing day"))
    require_names([h.name for h in marked], CLOSING_DAY_NAMES, "ECB TARGET closing days")
    require_names([e.name for e in exclusions], OFFICE_HOLIDAY_NAMES, "ECB office holidays")
    ordered = sorted(years)
    if not ordered or ordered != list(range(ordered[0], ordered[-1] + 1)):
        raise ValueError(f"ECB page skips a year: {ordered}")
    generated = [h for year in ordered for h in rule_holidays(year)]
    if {h.day for h in generated} != {h.day for h in marked}:
        only_marked = sorted({h.day for h in marked} - {h.day for h in generated})
        only_rule = sorted({h.day for h in generated} - {h.day for h in marked})
        raise ValueError(f"TARGET rule disagrees with the ECB's marked days: marked only {only_marked}, rule only {only_rule}")
    return published_years(generated, ordered[0], ordered[-1], exclusions)


SOURCE = single_part(
    "target",
    "European Central Bank, TARGET closing days (Guideline (EU) 2022/912)",
    "https://www.ecb.europa.eu/ecb/contacts/working-hours/html/index.en.html",
    "html",
    parse,
)

"""US federal holidays: OPM's legal public holidays plus executive-order closures.

OPM's iCal feed gives the day each legal public holiday (5 U.S.C. 6103(a)) is
observed for most federal employees, a Saturday holiday on the Friday before it
and a Sunday one on the Monday after it (6103(b), Executive Order 11582). Each
event links the year tab it belongs to, so 31 December can belong to the next
year's schedule. Inauguration Day is left out: it is a holiday only for employees
in the Washington, DC area.

OPM does not list the days the President closes executive departments and
agencies by executive order. Those come from the Federal Register: each order in
CLOSURE_ORDERS is snapshotted as its published text, and generation fails unless
its first section still names exactly the expected closure dates. The list covers
every such order published for a day inside OPM's horizon; a new order is added
here when it is published.
"""

from __future__ import annotations

import dataclasses
import datetime
import re

from shoreleave_sync.model import Exclusion, Holiday, Part, Published, Source, check_weekday, parse_month_day, published_years, require_names

OPM_URL = "https://www.opm.gov/policy-data-oversight/pay-leave/federal-holidays/holidays.ics"
NAMES = frozenset(
    {
        "New Year's Day",
        "Birthday of Martin Luther King, Jr.",
        "Washington's Birthday",
        "Memorial Day",
        "Juneteenth National Independence Day",
        "Independence Day",
        "Labor Day",
        "Columbus Day",
        "Veterans Day",
        "Thanksgiving Day",
        "Christmas Day",
    }
)
REGIONAL = "Inauguration Day"


@dataclasses.dataclass(frozen=True)
class ClosureOrder:
    document_number: str
    executive_order: int
    text_url: str
    days: tuple[datetime.date, ...]


CLOSURE_ORDERS = (
    ClosureOrder(
        "2024-31143",
        14129,
        "https://www.federalregister.gov/documents/full_text/text/2024/12/26/2024-31143.txt",
        (datetime.date(2024, 12, 24),),
    ),
    ClosureOrder(
        "2024-31766",
        14133,
        "https://www.federalregister.gov/documents/full_text/text/2025/01/03/2024-31766.txt",
        (datetime.date(2025, 1, 9),),
    ),
    ClosureOrder(
        "2025-23847",
        14371,
        "https://www.federalregister.gov/documents/full_text/text/2025/12/23/2025-23847.txt",
        (datetime.date(2025, 12, 24), datetime.date(2025, 12, 26)),
    ),
)
_DATE = re.compile(
    r"(?:(?:Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day, )?"
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4}"
)


def ical_events(text: str) -> list[dict[str, str]]:
    """The properties of each VEVENT, with folded lines joined and values unescaped."""
    unfolded = re.sub(r"\r?\n[ \t]", "", text)
    events: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in unfolded.splitlines():
        if line == "BEGIN:VEVENT":
            current = {}
        elif line == "END:VEVENT" and current is not None:
            events.append(current)
            current = None
        elif current is not None and ":" in line:
            key, value = line.split(":", 1)
            current[key.split(";", 1)[0]] = re.sub(r"\\([,;\\])", r"\1", value).replace("\\n", "\n")
    return events


def opm_holidays(raw: bytes) -> tuple[list[Holiday], list[Exclusion], list[int]]:
    holidays: list[Holiday] = []
    exclusions: list[Exclusion] = []
    years: set[int] = set()
    events = ical_events(raw.decode("utf-8"))
    require_names([e["SUMMARY"] for e in events if e["SUMMARY"] != REGIONAL], NAMES, "OPM holidays.ics")
    for event in events:
        day = datetime.datetime.strptime(event["DTSTART"], "%Y%m%d").date()
        tab = re.search(r"/federal-holidays/tabs/(\d{4})/", event.get("DESCRIPTION", "").replace("\n", ""))
        if tab is None:
            raise ValueError(f"OPM event {event['SUMMARY']!r} on {day} names no year tab")
        years.add(int(tab.group(1)))
        if event["SUMMARY"] == REGIONAL:
            exclusions.append(Exclusion(day, REGIONAL, "Washington, DC area only"))
        else:
            holidays.append(Holiday(day, event["SUMMARY"]))
    return holidays, exclusions, sorted(years)


def closure_days(order: ClosureOrder, raw: bytes) -> list[Holiday]:
    text = re.sub(r"<[^>]+>", " ", raw.decode("utf-8"))
    text = re.sub(r"\s+", " ", text)
    if f"Executive Order {order.executive_order} of" not in text:
        raise ValueError(f"{order.document_number} is not Executive Order {order.executive_order}")
    section = re.search(r"Section 1\. (.+?) Sec\. 2\.", text)
    if section is None or "shall be closed" not in section.group(1):
        raise ValueError(f"{order.document_number}: section 1 no longer closes executive departments")
    days = tuple(check_weekday(found, parse_month_day(found)) for found in _DATE.findall(section.group(1)))
    if days != order.days:
        raise ValueError(f"{order.document_number}: section 1 names {days}, expected {order.days}")
    return [Holiday(day, f"Closed by Executive Order {order.executive_order}") for day in days]


def parse(raws: dict[str, bytes]) -> Published:
    holidays, exclusions, years = opm_holidays(raws["opm"])
    if years != list(range(years[0], years[-1] + 1)):
        raise ValueError(f"OPM feed skips a year: {years}")
    last = years[-1]
    # A Saturday 1 January is observed on the preceding Friday, a day of the last
    # year that only the next year's schedule would list.
    until = datetime.date(last, 12, 31)
    if datetime.date(last + 1, 1, 1).weekday() == 5:
        until = datetime.date(last, 12, 30)
    for order in CLOSURE_ORDERS:
        holidays += closure_days(order, raws[f"fr-{order.document_number}"])
    return published_years(holidays, years[0], last, exclusions, until)


SOURCE = Source(
    "us_federal",
    "US Office of Personnel Management, federal holidays; Federal Register, executive orders closing executive departments",
    (Part("opm", OPM_URL, "ics"),)
    + tuple(Part(f"fr-{order.document_number}", order.text_url, "txt") for order in CLOSURE_ORDERS),
    parse,
)

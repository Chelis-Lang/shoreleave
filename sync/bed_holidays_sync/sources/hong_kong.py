"""Hong Kong general holidays from the 1823 government contact centre feed."""

from __future__ import annotations

import datetime
import json

from bed_holidays_sync.model import Holiday, Published, Source, published_years


def parse(raw: bytes) -> Published:
    calendar = json.loads(raw.decode("utf-8-sig"))["vcalendar"][0]
    holidays = []
    for event in calendar["vevent"]:
        start = datetime.datetime.strptime(event["dtstart"][0], "%Y%m%d").date()
        end = datetime.datetime.strptime(event["dtend"][0], "%Y%m%d").date()
        if end != start + datetime.timedelta(days=1):
            raise ValueError(f"multi-day event {event['summary']!r} at {start}")
        holidays.append(Holiday(start, event["summary"].strip()))
    years = sorted({h.day.year for h in holidays})
    if years != list(range(years[0], years[-1] + 1)):
        raise ValueError(f"1823 feed skips a year: {years}")
    return published_years(holidays, years[0], years[-1])


SOURCE = Source(
    key="hong_kong",
    authority="Hong Kong SAR Government, 1823 general holidays",
    url="https://www.1823.gov.hk/common/ical/en.json",
    suffix="json",
    parse=parse,
)

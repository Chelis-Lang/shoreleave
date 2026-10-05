"""England and Wales bank holidays from the gov.uk bank-holidays feed."""

from __future__ import annotations

import datetime
import json

from bed_holidays_sync.model import Holiday, Published, Source, published_years


def parse(raw: bytes) -> Published:
    division = json.loads(raw.decode("utf-8"))["england-and-wales"]
    holidays = [
        Holiday(datetime.date.fromisoformat(event["date"]), event["title"].strip())
        for event in division["events"]
    ]
    years = sorted({h.day.year for h in holidays})
    if years != list(range(years[0], years[-1] + 1)):
        raise ValueError(f"gov.uk feed skips a year: {years}")
    return published_years(holidays, years[0], years[-1])


SOURCE = Source(
    key="england_and_wales",
    authority="UK Government Digital Service, gov.uk bank holidays",
    url="https://www.gov.uk/bank-holidays.json",
    suffix="json",
    parse=parse,
)

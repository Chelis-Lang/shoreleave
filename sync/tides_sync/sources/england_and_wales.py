"""England and Wales bank holidays from the gov.uk bank-holidays feed."""

from __future__ import annotations

import datetime
import json

from tides_sync.model import Holiday, Published, published_years, require_names, single_part

NAMES = frozenset(
    {
        "New Year's Day",
        "Good Friday",
        "Easter Monday",
        "Early May bank holiday",
        "Spring bank holiday",
        "Summer bank holiday",
        "Christmas Day",
        "Boxing Day",
        # Proclaimed for one year.
        "Early May bank holiday (VE day)",
        "Platinum Jubilee bank holiday",
        "Bank Holiday for the State Funeral of Queen Elizabeth II",
        "Bank holiday for the coronation of King Charles III",
    }
)


def parse(raw: bytes) -> Published:
    division = json.loads(raw.decode("utf-8"))["england-and-wales"]
    holidays = [
        Holiday(datetime.date.fromisoformat(event["date"]), event["title"].strip())
        for event in division["events"]
    ]
    require_names([h.name for h in holidays], NAMES, "gov.uk england-and-wales")
    years = sorted({h.day.year for h in holidays})
    if years != list(range(years[0], years[-1] + 1)):
        raise ValueError(f"gov.uk feed skips a year: {years}")
    return published_years(holidays, years[0], years[-1])


SOURCE = single_part(
    "england_and_wales",
    "UK Government Digital Service, gov.uk bank holidays",
    "https://www.gov.uk/bank-holidays.json",
    "json",
    parse,
)

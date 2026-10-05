"""Hong Kong general holidays from the 1823 government contact centre feed."""

from __future__ import annotations

import datetime
import json

from shoreleave_sync.model import Holiday, Published, published_years, require_names, single_part


NAMES = frozenset(
    {
        "The first day of January",
        "Lunar New Year's Day",
        "The second day of Lunar New Year",
        "The third day of Lunar New Year",
        "The fourth day of Lunar New Year",
        "Ching Ming Festival",
        "The day following Ching Ming Festival",
        "Good Friday",
        "The day following Good Friday",
        "Easter Monday",
        "The day following Easter Monday",
        "Labour Day",
        "The Birthday of the Buddha",
        "The day following the Birthday of the Buddha",
        "Tuen Ng Festival",
        "The day following Tuen Ng Festival",
        "Hong Kong Special Administrative Region Establishment Day",
        "The day following Hong Kong Special Administrative Region Establishment Day",
        "The day following the Chinese Mid-Autumn Festival",
        "National Day",
        "The day following National Day",
        "Chung Yeung Festival",
        "The day following Chung Yeung Festival",
        "Christmas Day",
        "The first weekday after Christmas Day",
    }
)


def parse(raw: bytes) -> Published:
    calendar = json.loads(raw.decode("utf-8-sig"))["vcalendar"][0]
    holidays = []
    for event in calendar["vevent"]:
        start = datetime.datetime.strptime(event["dtstart"][0], "%Y%m%d").date()
        end = datetime.datetime.strptime(event["dtend"][0], "%Y%m%d").date()
        if end != start + datetime.timedelta(days=1):
            raise ValueError(f"multi-day event {event['summary']!r} at {start}")
        holidays.append(Holiday(start, event["summary"].strip()))
    require_names([h.name for h in holidays], NAMES, "1823 general holidays")
    years = sorted({h.day.year for h in holidays})
    if years != list(range(years[0], years[-1] + 1)):
        raise ValueError(f"1823 feed skips a year: {years}")
    return published_years(holidays, years[0], years[-1])


SOURCE = single_part(
    "hong_kong",
    "Hong Kong SAR Government, 1823 general holidays",
    "https://www.1823.gov.hk/common/ical/en.json",
    "json",
    parse,
)

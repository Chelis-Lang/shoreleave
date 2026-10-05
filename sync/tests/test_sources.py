"""Each parser against its pinned snapshot, and against damaged copies of it."""

from __future__ import annotations

import datetime
import json
import re

import pytest

from bed_holidays_sync.model import Published
from bed_holidays_sync.sources import SOURCES, us_federal
from conftest import raw_snapshot

D = datetime.date


def days(p: Published) -> set[datetime.date]:
    return {h.day for h in p.holidays}


HORIZONS = {
    "england_and_wales": (D(2019, 1, 1), D(2028, 12, 31), 83),
    "us_federal": (D(2011, 1, 1), D(2030, 12, 31), 209),
    "japan_bank": (D(1990, 1, 1), D(2027, 12, 31), 758),
    "new_south_wales": (D(2026, 1, 1), D(2027, 12, 31), 27),
    "hong_kong": (D(2025, 1, 1), D(2027, 12, 31), 51),
    "nyse": (D(2026, 1, 1), D(2028, 12, 31), 29),
    "sifma": (D(2026, 1, 1), D(2027, 12, 31), 23),
    "target": (D(2026, 1, 1), D(2028, 12, 31), 18),
}


@pytest.mark.parametrize("key", sorted(SOURCES))
def test_horizon_is_the_published_span(published: dict[str, Published], key: str) -> None:
    valid_from, valid_until, count = HORIZONS[key]
    p = published[key]
    assert (p.valid_from, p.valid_until, len(p.holidays)) == (valid_from, valid_until, count)
    assert all(valid_from <= h.day <= valid_until for h in p.holidays)


def test_england_and_wales_keeps_proclaimed_days(published: dict[str, Published]) -> None:
    assert {D(2022, 9, 19), D(2023, 5, 8), D(2020, 5, 8), D(2027, 12, 28)} <= days(published["england_and_wales"])
    assert D(2020, 5, 4) not in days(published["england_and_wales"])


def test_us_federal_observed_days_and_exclusions(published: dict[str, Published]) -> None:
    p = published["us_federal"]
    assert {D(2021, 12, 31), D(2027, 12, 31), D(2021, 6, 18), D(2011, 12, 26)} <= days(p)
    reasons = {(e.day, e.reason) for e in p.exclusions}
    assert (D(2010, 12, 31), "outside the published horizon") in reasons
    assert (D(2021, 1, 20), "Washington, DC area only") in reasons
    assert D(2024, 12, 24) not in days(p)


def test_us_federal_horizon_stops_before_an_unlisted_friday() -> None:
    # Ending the schedule at 2021, whose next 1 January is a Saturday observed on
    # 31 December 2021 in the 2022 table, leaves that Friday unvouched for.
    raw = raw_snapshot("us_federal").decode("utf-8")
    cut = re.sub(r"<table[^>]*>\s*<caption>20(2[2-9]|30) Holiday Schedule</caption>.*?</table>", "", raw, flags=re.S)
    p = us_federal.parse(cut.encode("utf-8"))
    assert (p.valid_from, p.valid_until) == (D(2011, 1, 1), D(2021, 12, 30))


def test_japan_bank_adds_the_statutory_closures(published: dict[str, Published]) -> None:
    p = days(published["japan_bank"])
    assert {D(2026, 1, 2), D(2026, 1, 3), D(2026, 12, 31), D(1990, 12, 31)} <= p
    assert {D(2026, 9, 22), D(2026, 5, 6)} <= p  # citizen's and substitute holidays
    assert min(p) == D(1990, 1, 1)


def test_new_south_wales_leaves_out_the_bank_holiday(published: dict[str, Published]) -> None:
    p = published["new_south_wales"]
    assert {D(2027, 12, 27), D(2027, 12, 28), D(2026, 12, 28), D(2026, 4, 27)} <= days(p)
    assert {(e.day, e.reason) for e in p.exclusions} == {
        (D(2026, 8, 3), "not a declared public holiday"),
        (D(2027, 8, 2), "not a declared public holiday"),
    }


def test_hong_kong_lunar_holidays(published: dict[str, Published]) -> None:
    p = {h.day: h.name for h in published["hong_kong"].holidays}
    assert p[D(2027, 2, 9)] == "The fourth day of Lunar New Year"
    assert p[D(2026, 4, 7)] == "The day following Easter Monday"


def test_nyse_saturday_new_year_closes_no_day(published: dict[str, Published]) -> None:
    p = days(published["nyse"])
    assert D(2027, 12, 31) not in p and D(2028, 1, 1) not in p
    assert {D(2027, 12, 24), D(2026, 7, 3), D(2027, 7, 5)} <= p


def test_sifma_early_closes_are_not_closures(published: dict[str, Published]) -> None:
    p = published["sifma"]
    assert D(2026, 4, 3) not in days(p)
    assert D(2027, 3, 26) in days(p)
    early = {e.day for e in p.exclusions}
    assert {D(2026, 4, 3), D(2026, 11, 27), D(2027, 12, 31)} <= early
    assert not early & days(p)


def test_target_takes_only_the_marked_days(published: dict[str, Published]) -> None:
    p = published["target"]
    assert {(h.day.month, h.day.day) for h in p.holidays} == {(1, 1), (5, 1), (12, 25), (12, 26)} | {
        (d.month, d.day) for d in (D(2026, 4, 3), D(2026, 4, 6), D(2027, 3, 26), D(2027, 3, 29), D(2028, 4, 14), D(2028, 4, 17))
    }
    assert D(2026, 5, 14) in {e.day for e in p.exclusions}


# Negative twins: damaged snapshots must be rejected, never read as fewer holidays.


def test_gov_uk_missing_year_is_rejected() -> None:
    data = json.loads(raw_snapshot("england_and_wales"))
    events = data["england-and-wales"]["events"]
    data["england-and-wales"]["events"] = [e for e in events if not e["date"].startswith("2023")]
    with pytest.raises(ValueError, match="skips a year"):
        SOURCES["england_and_wales"].parse(json.dumps(data).encode("utf-8"))


def test_weekday_contradicting_its_date_is_rejected() -> None:
    raw = raw_snapshot("new_south_wales").replace(b"Thursday 1 January 2026", b"Friday 1 January 2026")
    with pytest.raises(ValueError, match="names Friday"):
        SOURCES["new_south_wales"].parse(raw)


def test_unused_erratum_is_rejected() -> None:
    raw = raw_snapshot("us_federal").replace(b"<td>Tuesday, December 26 <span", b"<td>Monday, December 26 <span")
    with pytest.raises(ValueError, match="errata no longer in the snapshot"):
        us_federal.parse(raw)


def test_hong_kong_multi_day_event_is_rejected() -> None:
    data = json.loads(raw_snapshot("hong_kong").decode("utf-8-sig"))
    data["vcalendar"][0]["vevent"][0]["dtend"][0] = "20250103"
    with pytest.raises(ValueError, match="multi-day event"):
        SOURCES["hong_kong"].parse(json.dumps(data).encode("utf-8"))


def test_sifma_without_its_section_is_rejected() -> None:
    raw = raw_snapshot("sifma").replace(b"U.S. Holiday Recommendations", b"U.S. Holiday Schedule")
    with pytest.raises(ValueError):
        SOURCES["sifma"].parse(raw)


def test_target_without_marks_has_no_closures() -> None:
    raw = raw_snapshot("target").replace(b"*", b"")
    p = SOURCES["target"].parse(raw)
    assert p.holidays == ()


def test_nyse_cell_in_the_wrong_year_is_rejected() -> None:
    raw = raw_snapshot("nyse").replace(b"Thursday, January 1", b"Thursday, January 2")
    with pytest.raises(ValueError, match="names Thursday"):
        SOURCES["nyse"].parse(raw)

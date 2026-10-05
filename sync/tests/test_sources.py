"""Each parser against its pinned snapshot, and against damaged copies of it."""

from __future__ import annotations

import datetime
import json
import re

import pytest

from conftest import parse_one, raw_parts, raw_snapshot
from shoreleave_sync import rules
from shoreleave_sync.model import Published
from shoreleave_sync.sources import SOURCES, new_south_wales, sifma

D = datetime.date


def days(p: Published) -> set[datetime.date]:
    return {h.day for h in p.holidays}


def unfolded(ics: bytes) -> bytes:
    return ics.replace(b"\r\n ", b"").replace(b"\n ", b"")


HORIZONS = {
    "england_and_wales": (D(2019, 1, 1), D(2028, 12, 31), 83),
    "us_federal": (D(2021, 1, 1), D(2030, 12, 31), 114),
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


def test_us_federal_observed_days_closures_and_exclusions(published: dict[str, Published]) -> None:
    p = published["us_federal"]
    # Year boundary: the observed day of a Saturday 1 January is in the year before.
    assert {D(2021, 12, 31), D(2027, 12, 31), D(2021, 6, 18), D(2027, 6, 18)} <= days(p)
    assert {D(2024, 12, 24), D(2025, 1, 9), D(2025, 12, 24), D(2025, 12, 26)} <= days(p)
    assert {(e.day, e.name) for e in p.exclusions} == {(D(2021, 1, 20), "Inauguration Day"), (D(2025, 1, 20), "Inauguration Day")}
    assert D(2021, 1, 20) not in days(p)


def test_japan_bank_adds_the_statutory_closures(published: dict[str, Published]) -> None:
    p = days(published["japan_bank"])
    assert {D(2026, 1, 2), D(2026, 1, 3), D(2026, 12, 31), D(1990, 12, 31)} <= p
    assert {D(2026, 9, 22), D(2026, 5, 6)} <= p  # citizen's and substitute holidays
    assert {D(2021, 7, 22), D(2021, 7, 23), D(2021, 8, 9)} <= p  # one-year Olympic moves
    assert min(p) == D(1990, 1, 1)


def test_new_south_wales_is_section_4_plus_declared_days(published: dict[str, Published]) -> None:
    p = published["new_south_wales"]
    assert {D(2027, 12, 27), D(2027, 12, 28), D(2026, 12, 28), D(2026, 4, 4), D(2026, 4, 5)} <= days(p)
    assert {D(2026, 4, 27), D(2027, 4, 26)} == set(new_south_wales.DECLARED) & days(p)
    assert not set(new_south_wales.DECLARED) & (rules.new_south_wales_section_4(2026) | rules.new_south_wales_section_4(2027))
    assert D(2026, 8, 3) not in days(p)
    assert {(e.day, e.reason) for e in p.exclusions} == {
        (D(2026, 8, 3), "not a declared public holiday"),
        (D(2027, 8, 2), "not a declared public holiday"),
    }


def test_nsw_rule_handles_every_weekend_collision_year() -> None:
    assert {D(2027, 12, 27), D(2027, 12, 28)} <= rules.new_south_wales_section_4(2027)  # Sat Christmas, Sun Boxing Day
    assert D(2022, 12, 27) in rules.new_south_wales_section_4(2022)  # Sun Christmas
    assert D(2026, 12, 28) in rules.new_south_wales_section_4(2026)  # Sat Boxing Day
    assert D(2028, 1, 3) in rules.new_south_wales_section_4(2028)  # Sat 1 January, additional Monday
    assert D(2027, 4, 26) not in rules.new_south_wales_section_4(2027)  # a declared day is never a rule day


def test_hong_kong_lunar_holidays_and_chains(published: dict[str, Published]) -> None:
    p = {h.day: h.name for h in published["hong_kong"].holidays}
    assert p[D(2027, 2, 9)] == "The fourth day of Lunar New Year"
    assert p[D(2026, 4, 6)] == "The day following Ching Ming Festival"
    assert p[D(2026, 4, 7)] == "The day following Easter Monday"


def test_nyse_closures_and_early_closes(published: dict[str, Published]) -> None:
    p = published["nyse"]
    assert D(2027, 12, 31) not in days(p) and D(2028, 1, 1) not in days(p)
    assert {D(2027, 12, 24), D(2026, 7, 3), D(2027, 7, 5)} <= days(p)
    early = {c.day: c.detail for c in p.early_closes}
    assert sorted(early) == [D(2026, 11, 27), D(2026, 12, 24), D(2027, 11, 26), D(2028, 7, 3), D(2028, 11, 24)]
    assert early[D(2028, 7, 3)] == "closes at 1:00 p.m. (1:15 p.m. for eligible options) Eastern Time"


def test_sifma_early_closes_are_not_closures(published: dict[str, Published]) -> None:
    p = published["sifma"]
    assert D(2026, 4, 3) not in days(p)
    assert D(2027, 3, 26) in days(p)
    early = {c.day: c.detail for c in p.early_closes}
    assert early[D(2026, 4, 3)] == "closes at 12:00 p.m. Eastern Time"
    assert {D(2026, 11, 27), D(2027, 12, 31)} <= set(early)
    assert not set(early) & days(p)


def test_sifma_reads_only_the_us_section(published: dict[str, Published]) -> None:
    # UK Easter Monday, May Day, Summer Bank Holiday and Japan's Coming of Age Day.
    assert not {D(2026, 4, 6), D(2026, 5, 4), D(2026, 8, 31), D(2026, 1, 12)} & days(published["sifma"])


def test_target_is_the_rule_and_only_the_marked_days(published: dict[str, Published]) -> None:
    p = published["target"]
    assert days(p) == {d for year in (2026, 2027, 2028) for d in rules.target(year)}
    excluded = {e.day: e.name for e in p.exclusions}
    assert excluded[D(2026, 6, 4)] == "Corpus Christi"
    assert excluded[D(2026, 10, 3)] == "Day of German Unity"
    assert not set(excluded) & days(p)


def test_easter_against_published_dates() -> None:
    known = {2019: D(2019, 4, 21), 2024: D(2024, 3, 31), 2026: D(2026, 4, 5), 2027: D(2027, 3, 28), 2028: D(2028, 4, 16), 2038: D(2038, 4, 25)}
    assert {year: rules.easter_sunday(year) for year in known} == known


# Negative twins: damaged or changed snapshots must stop regeneration, never be
# read as fewer or other holidays.


def test_gov_uk_missing_year_is_rejected() -> None:
    data = json.loads(raw_snapshot("england_and_wales"))
    events = data["england-and-wales"]["events"]
    data["england-and-wales"]["events"] = [e for e in events if not e["date"].startswith("2023")]
    with pytest.raises(ValueError, match="skips a year"):
        parse_one("england_and_wales", json.dumps(data).encode("utf-8"))


def test_gov_uk_unknown_name_is_rejected() -> None:
    raw = raw_snapshot("england_and_wales").replace(b'"Summer bank holiday"', b'"Late summer holiday"', 1)
    assert raw != raw_snapshot("england_and_wales")
    with pytest.raises(ValueError, match="unknown holiday name"):
        parse_one("england_and_wales", raw)


def test_weekday_contradicting_its_date_is_rejected() -> None:
    raw = raw_snapshot("new_south_wales").replace(b"Thursday 1 January 2026", b"Friday 1 January 2026")
    with pytest.raises(ValueError, match="names Friday"):
        parse_one("new_south_wales", raw)


def test_nsw_bank_holiday_renamed_is_rejected() -> None:
    raw = raw_snapshot("new_south_wales").replace(b"Bank Holiday", b"Bank Holiday Monday")
    with pytest.raises(ValueError, match="unknown holiday name"):
        parse_one("new_south_wales", raw)


def test_nsw_undeclared_extra_day_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(new_south_wales, "DECLARED", {D(2026, 4, 27): "declared"})
    with pytest.raises(ValueError, match=r"table only \[datetime.date\(2027, 4, 26\)\]"):
        parse_one("new_south_wales", raw_snapshot("new_south_wales"))


def test_nsw_declared_day_missing_from_the_table_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(new_south_wales, "DECLARED", {**new_south_wales.DECLARED, D(2026, 9, 1): "declared"})
    with pytest.raises(ValueError, match="rules or declarations only"):
        parse_one("new_south_wales", raw_snapshot("new_south_wales"))


def test_target_marking_an_office_holiday_is_rejected() -> None:
    raw = re.sub(rb"Corpus Christi(\s*<)", rb"Corpus Christi*\1", raw_snapshot("target"), count=1)
    assert raw != raw_snapshot("target")
    with pytest.raises(ValueError, match=r"unknown holiday name\(s\) \['Corpus Christi'\]"):
        parse_one("target", raw)


def test_target_new_office_holiday_is_rejected() -> None:
    raw = raw_snapshot("target").replace(b"Day of German Unity", b"Reformation Day", 1)
    with pytest.raises(ValueError, match="unknown holiday name"):
        parse_one("target", raw)


def test_target_marked_days_disagreeing_with_the_rule_are_rejected() -> None:
    raw = raw_snapshot("target").replace(b"1 May 2027", b"3 May 2027", 1)
    assert raw != raw_snapshot("target")
    with pytest.raises(ValueError, match="TARGET rule disagrees"):
        parse_one("target", raw)


def test_opm_unknown_event_is_rejected() -> None:
    parts = raw_parts("us_federal")
    parts["opm"] = parts["opm"].replace(b"SUMMARY:Columbus Day", b"SUMMARY:Indigenous Peoples' Day", 1)
    with pytest.raises(ValueError, match="unknown holiday name"):
        SOURCES["us_federal"].parse(parts)


def test_opm_event_without_its_year_tab_is_rejected() -> None:
    parts = raw_parts("us_federal")
    parts["opm"] = unfolded(parts["opm"]).replace(b"tabs/2021/", b"tabs/x/", 1)
    with pytest.raises(ValueError, match="names no year tab"):
        SOURCES["us_federal"].parse(parts)


def test_closure_order_naming_other_dates_is_rejected() -> None:
    parts = raw_parts("us_federal")
    key = "fr-2025-23847"
    parts[key] = re.sub(rb"Friday, December 26,(\s+)2025, the day", rb"Monday, December 29,\g<1>2025, the day", parts[key])
    assert parts[key] != raw_parts("us_federal")[key]
    with pytest.raises(ValueError, match="section 1 names"):
        SOURCES["us_federal"].parse(parts)


def test_closure_order_of_another_number_is_rejected() -> None:
    parts = raw_parts("us_federal")
    parts["fr-2024-31766"] = parts["fr-2024-31766"].replace(b"Executive Order 14133", b"Executive Order 14134")
    with pytest.raises(ValueError, match="is not Executive Order 14133"):
        SOURCES["us_federal"].parse(parts)


def test_horizon_stops_before_an_unlisted_friday() -> None:
    # Ending OPM's schedule at 2021, whose next 1 January is a Saturday observed on
    # 31 December 2021 under the 2022 tab, leaves that Friday unvouched for.
    parts = raw_parts("us_federal")
    events = re.split(rb"(?=BEGIN:VEVENT)", unfolded(parts["opm"]))
    kept = [e for e in events if not re.search(rb"tabs/20(2[2-9]|30)/", e)]
    parts["opm"] = b"".join(kept) + b"END:VCALENDAR\r\n"
    p = SOURCES["us_federal"].parse(parts)
    assert (p.valid_from, p.valid_until) == (D(2021, 1, 1), D(2021, 12, 30))
    assert D(2021, 12, 31) not in days(p)


def test_hong_kong_multi_day_event_is_rejected() -> None:
    data = json.loads(raw_snapshot("hong_kong").decode("utf-8-sig"))
    data["vcalendar"][0]["vevent"][0]["dtend"][0] = "20250103"
    with pytest.raises(ValueError, match="multi-day event"):
        parse_one("hong_kong", json.dumps(data).encode("utf-8"))


def test_hong_kong_unknown_name_is_rejected() -> None:
    raw = raw_snapshot("hong_kong").replace(b"Tuen Ng Festival", b"Dragon Boat Festival", 1)
    with pytest.raises(ValueError, match="unknown holiday name"):
        parse_one("hong_kong", raw)


def test_japan_unknown_name_is_rejected() -> None:
    raw = raw_snapshot("japan_bank").decode("shift_jis").replace("海の日", "臨時休日", 1).encode("shift_jis")
    with pytest.raises(ValueError, match="unknown holiday name"):
        parse_one("japan_bank", raw)


def test_sifma_without_its_section_is_rejected() -> None:
    raw = raw_snapshot("sifma").replace(b"U.S. Holiday Recommendations", b"U.S. Holiday Schedule")
    with pytest.raises(ValueError):
        parse_one("sifma", raw)


def test_sifma_uk_name_in_the_us_section_is_rejected() -> None:
    raw = raw_snapshot("sifma").replace(b'\\"children\\":\\"Columbus Day\\"', b'\\"children\\":\\"Spring Bank Holiday\\"')
    assert raw != raw_snapshot("sifma")
    with pytest.raises(ValueError, match="unknown holiday name"):
        parse_one("sifma", raw)


TENTATIVE_NOTE = "Early Close (12:00 p.m. Eastern Time): Friday, April 3, 2026 - Tentative"


def tentative_snapshot() -> bytes:
    raw = raw_snapshot("sifma").replace(b"Early Close (12:00 p.m. Eastern Time): Friday, April 3, 2026", TENTATIVE_NOTE.encode())
    assert raw != raw_snapshot("sifma")
    return raw


def test_sifma_tentative_entry_is_rejected() -> None:
    with pytest.raises(ValueError, match="tentative SIFMA entry"):
        parse_one("sifma", tentative_snapshot())


def test_sifma_tentative_entry_listed_explicitly_is_read(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sifma, "TENTATIVE", {TENTATIVE_NOTE: "read as the early close it names"})
    p = parse_one("sifma", tentative_snapshot())
    assert D(2026, 4, 3) in {c.day for c in p.early_closes}


def test_nyse_cell_in_the_wrong_year_is_rejected() -> None:
    raw = raw_snapshot("nyse").replace(b"Thursday, January 1", b"Thursday, January 2")
    with pytest.raises(ValueError, match="names Thursday"):
        parse_one("nyse", raw)


def test_nyse_unknown_early_close_footnote_is_rejected() -> None:
    raw = raw_snapshot("nyse").replace(b"Each market will close early at", b"Each market will close early, at", 1)
    assert raw != raw_snapshot("nyse")
    with pytest.raises(ValueError, match="unrecognized early-close footnote"):
        parse_one("nyse", raw)

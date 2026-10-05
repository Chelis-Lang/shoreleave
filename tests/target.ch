module Shoreleave.Tests.Target
import Std.Datetime (Date, date)
import Std.Datetime.Business (is_business_day, try_is_business_day, business_calendar_valid_from, business_calendar_valid_until)
import Std.Test (assert_eq)
import Shoreleave.Target (target, target_projected, try_target_projected, target_rule_holidays, target_weekmask, target_source_urls)
import Shoreleave.Published.Target (target_published_holidays)
import Shoreleave.TestSupport.Support (mismatches_by_year, holidays_of, all_closed)
def test_horizon_is_the_published_span() -> unit ! { Test } = {
  cal = target()
  _ = assert_eq(business_calendar_valid_from(cal), date(2026i64, 1i64, 1i64), "valid_from")
  _ = assert_eq(business_calendar_valid_until(cal), date(2028i64, 12i64, 31i64), "valid_until")
  assert_eq(index(target_source_urls(), 0i64), "https://www.ecb.europa.eu/ecb/contacts/working-hours/html/index.en.html", "url")
}
def test_every_closing_day_is_closed() -> unit ! { Test } = {
  cal = target()
  _ = assert_eq(len(holidays_of(cal)), 13i64, "13 weekday closing days in 2026..2028")
  assert_eq(all_closed(cal, target_published_holidays()), true, "no closing day is a business day")
}
def test_rules_match_every_published_year() -> unit ! { Test } = assert_eq(mismatches_by_year(target_weekmask(), target_rule_holidays, target_published_holidays(), range(2026i64, 2029i64)), "", "rules against the ECB, 2026..2028")
-- ECB public holidays that are not TARGET closing days stay open, and a weekend
-- closing day has no substitute.
def test_only_marked_days_close() -> unit ! { Test } = {
  cal = target()
  _ = assert_eq(is_business_day(cal, date(2026i64, 5i64, 14i64)), true, "Ascension Day")
  _ = assert_eq(is_business_day(cal, date(2026i64, 12i64, 24i64)), true, "Christmas Eve")
  _ = assert_eq(is_business_day(cal, date(2027i64, 5i64, 3i64)), true, "Saturday 1 May 2027 has no substitute")
  assert_eq(is_business_day(cal, date(2027i64, 12i64, 27i64)), true, "a weekend Christmas has no substitute")
}
def test_queries_outside_the_horizon_are_none() -> unit ! { Test } = {
  cal = target()
  _ = assert_eq(try_is_business_day(cal, date(2025i64, 12i64, 31i64)), None, "day before the horizon")
  assert_eq(try_is_business_day(cal, date(2029i64, 1i64, 1i64)), None, "day after the horizon")
}
def test_projection() -> unit ! { Test } = {
  cal = target_projected(2030i64)
  _ = assert_eq(is_business_day(cal, date(2029i64, 3i64, 30i64)), false, "Good Friday 2029")
  _ = assert_eq(is_business_day(cal, date(2030i64, 5i64, 1i64)), false, "1 May 2030")
  _ = assert_eq(try_target_projected(2028i64), None, "the published last year")
  assert_eq(try_target_projected(10000i64), None, "after the last projection year")
}

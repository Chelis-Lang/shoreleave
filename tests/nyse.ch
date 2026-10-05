module Shoreleave.Tests.Nyse
import Std.Datetime (Date, date)
import Std.Datetime.Business (is_business_day, try_is_business_day, business_calendar_valid_from, business_calendar_valid_until)
import Std.Test (assert_eq)
import Shoreleave.Nyse (nyse, nyse_projected, try_nyse_projected, nyse_rule_holidays, nyse_weekmask, nyse_source_urls)
import Shoreleave.Published.Nyse (nyse_published_holidays)
import Shoreleave.Rules (contains_day)
import Shoreleave.TestSupport.Support (mismatches_by_year, holidays_of, all_closed)
def test_horizon_is_the_published_span() -> unit ! { Test } = {
  cal = nyse()
  _ = assert_eq(business_calendar_valid_from(cal), date(2026i64, 1i64, 1i64), "valid_from")
  _ = assert_eq(business_calendar_valid_until(cal), date(2028i64, 12i64, 31i64), "valid_until")
  assert_eq(index(nyse_source_urls(), 0i64), "https://www.nyse.com/markets/hours-calendars", "url")
}
def test_every_published_closure_is_closed() -> unit ! { Test } = {
  cal = nyse()
  _ = assert_eq(len(holidays_of(cal)), 29i64, "29 full-day closures in 2026..2028")
  assert_eq(all_closed(cal, nyse_published_holidays()), true, "no published closure is a business day")
}
def test_rules_match_every_published_year() -> unit ! { Test } = assert_eq(mismatches_by_year(nyse_weekmask(), nyse_rule_holidays, nyse_published_holidays(), range(2026i64, 2029i64)), "", "rules against nyse.com, 2026..2028")
-- NYSE closures, not federal holidays: Good Friday closes, Columbus and Veterans Day do not.
def test_market_not_federal_holidays() -> unit ! { Test } = {
  cal = nyse()
  _ = assert_eq(is_business_day(cal, date(2026i64, 4i64, 3i64)), false, "Good Friday 2026")
  _ = assert_eq(is_business_day(cal, date(2026i64, 10i64, 12i64)), true, "Columbus Day trades")
  assert_eq(is_business_day(cal, date(2026i64, 11i64, 11i64)), true, "Veterans Day trades")
}
-- Early closes are trading days: a BusinessCalendar has no half-day kind.
def test_early_closes_are_business_days() -> unit ! { Test } = {
  cal = nyse()
  _ = assert_eq(is_business_day(cal, date(2026i64, 11i64, 27i64)), true, "day after Thanksgiving 2026, 1:00 p.m. close")
  _ = assert_eq(is_business_day(cal, date(2026i64, 12i64, 24i64)), true, "Christmas Eve 2026, 1:00 p.m. close")
  assert_eq(is_business_day(cal, date(2028i64, 7i64, 3i64)), true, "3 July 2028, 1:00 p.m. close")
}
-- Rule 7.2: a Saturday 1 January closes no day, because 31 December ends the year.
def test_saturday_new_year_closes_no_day() -> unit ! { Test } = {
  cal = nyse()
  _ = assert_eq(is_business_day(cal, date(2027i64, 12i64, 31i64)), true, "31 December 2027 trades")
  _ = assert_eq(is_business_day(cal, date(2027i64, 12i64, 24i64)), false, "Saturday Christmas 2027 closes Friday 24th")
  _ = assert_eq(is_business_day(cal, date(2027i64, 6i64, 18i64)), false, "Saturday Juneteenth 2027 closes Friday 18th")
  assert_eq(is_business_day(cal, date(2027i64, 7i64, 5i64)), false, "Sunday Independence Day 2027 closes Monday 5th")
}
def test_queries_outside_the_horizon_are_none() -> unit ! { Test } = {
  cal = nyse()
  _ = assert_eq(try_is_business_day(cal, date(2025i64, 12i64, 31i64)), None, "day before the horizon")
  assert_eq(try_is_business_day(cal, date(2029i64, 1i64, 1i64)), None, "day after the horizon")
}
-- The national day of mourning of 9 January 2025 closed the exchange; it is an
-- announced closure, so the rules for 2025 do not give it.
def test_rules_omit_announced_closures() -> unit ! { Test } = assert_eq(contains_day(nyse_rule_holidays(2025i64), date(2025i64, 1i64, 9i64)), false, "9 January 2025 is not a rule closure")
def test_projection() -> unit ! { Test } = {
  cal = nyse_projected(2033i64)
  _ = assert_eq(is_business_day(cal, date(2032i64, 12i64, 31i64)), true, "Saturday 1 January 2033 closes no day")
  _ = assert_eq(is_business_day(cal, date(2033i64, 6i64, 20i64)), false, "Sunday Juneteenth 2033 closes Monday")
  _ = assert_eq(is_business_day(cal, date(2033i64, 4i64, 15i64)), false, "Good Friday 2033")
  _ = assert_eq(try_nyse_projected(2028i64), None, "the published last year")
  assert_eq(try_nyse_projected(10000i64), None, "after the last projection year")
}

module Shoreleave.Tests.Sifma
import Std.Datetime (Date, date)
import Std.Datetime.Business (is_business_day, try_is_business_day, business_calendar_valid_from, business_calendar_valid_until)
import Std.Test (assert_eq)
import Shoreleave.Sifma (sifma, sifma_projected, try_sifma_projected, sifma_rule_holidays, sifma_weekmask, sifma_source_urls)
import Shoreleave.Published.Sifma (sifma_published_holidays)
import Shoreleave.TestSupport.Support (normalized_year, observed_rule_days, diff_text, holidays_of, all_closed)
def published_year(year: i64) -> List[Date] = normalized_year(sifma_weekmask(), sifma_published_holidays(), year)
def rule_year(year: i64) -> List[Date] = observed_rule_days(sifma_weekmask(), sifma_rule_holidays, year)
def test_horizon_is_the_published_span() -> unit ! { Test } = {
  cal = sifma()
  _ = assert_eq(business_calendar_valid_from(cal), date(2026i64, 1i64, 1i64), "valid_from")
  _ = assert_eq(business_calendar_valid_until(cal), date(2027i64, 12i64, 31i64), "valid_until")
  assert_eq(index(sifma_source_urls(), 0i64), "https://www.sifma.org/resources/general/holiday-schedule/", "url")
}
def test_every_published_close_is_closed() -> unit ! { Test } = {
  cal = sifma()
  _ = assert_eq(len(holidays_of(cal)), 23i64, "23 recommended full closes in 2026..2027")
  assert_eq(all_closed(cal, sifma_published_holidays()), true, "no published close is a business day")
}
-- The rules give every recommended full close except Good Friday, which SIFMA
-- decides each year: an early close only in 2026, a full close in 2027.
def test_rules_match_published_years_but_good_friday() -> unit ! { Test } = {
  _ = assert_eq(diff_text(published_year(2026i64), rule_year(2026i64)), "", "2026")
  assert_eq(diff_text(published_year(2027i64), rule_year(2027i64)), "only in the first: 2027-03-26 ; only in the second: ", "2027: Good Friday is announced")
}
def test_early_closes_are_business_days() -> unit ! { Test } = {
  cal = sifma()
  _ = assert_eq(is_business_day(cal, date(2026i64, 4i64, 3i64)), true, "Good Friday 2026 is an early close")
  _ = assert_eq(is_business_day(cal, date(2026i64, 11i64, 27i64)), true, "the day after Thanksgiving is an early close")
  _ = assert_eq(is_business_day(cal, date(2027i64, 12i64, 31i64)), true, "Saturday 1 January 2028 closes no day")
  _ = assert_eq(is_business_day(cal, date(2027i64, 3i64, 26i64)), false, "Good Friday 2027 is a full close")
  assert_eq(is_business_day(cal, date(2027i64, 12i64, 24i64)), false, "Saturday Christmas 2027 closes Friday 24th")
}
-- The page's UK and Japan sections do not leak into the US calendar.
def test_uk_and_japan_recommendations_are_not_us_closes() -> unit ! { Test } = {
  cal = sifma()
  _ = assert_eq(is_business_day(cal, date(2026i64, 4i64, 6i64)), true, "UK Easter Monday")
  _ = assert_eq(is_business_day(cal, date(2026i64, 5i64, 4i64)), true, "UK May Day")
  _ = assert_eq(is_business_day(cal, date(2026i64, 8i64, 31i64)), true, "UK Summer Bank Holiday")
  _ = assert_eq(is_business_day(cal, date(2026i64, 12i64, 28i64)), true, "UK Boxing Day substitute")
  assert_eq(is_business_day(cal, date(2026i64, 1i64, 12i64)), true, "Japan Coming of Age Day")
}
def test_queries_outside_the_horizon_are_none() -> unit ! { Test } = {
  cal = sifma()
  _ = assert_eq(try_is_business_day(cal, date(2025i64, 12i64, 31i64)), None, "day before the horizon")
  assert_eq(try_is_business_day(cal, date(2028i64, 1i64, 3i64)), None, "day after the horizon")
}
def test_projection_omits_announced_closes() -> unit ! { Test } = {
  cal = sifma_projected(2029i64)
  _ = assert_eq(is_business_day(cal, date(2028i64, 4i64, 14i64)), true, "Good Friday 2028 is not projected")
  _ = assert_eq(is_business_day(cal, date(2028i64, 11i64, 10i64)), true, "Saturday Veterans Day 2028 is not projected")
  _ = assert_eq(is_business_day(cal, date(2028i64, 10i64, 9i64)), false, "Columbus Day 2028")
  _ = assert_eq(try_sifma_projected(2027i64), None, "the published last year")
  assert_eq(try_sifma_projected(10000i64), None, "after the last projection year")
}

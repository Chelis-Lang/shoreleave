module Tides.Tests.NewSouthWales
import Std.Datetime (Date, date)
import Std.Datetime.Business (is_business_day, try_is_business_day, business_calendar_valid_from, business_calendar_valid_until)
import Std.Test (assert_eq)
import Tides.NewSouthWales (new_south_wales, new_south_wales_projected, try_new_south_wales_projected, new_south_wales_rule_holidays, new_south_wales_weekmask, new_south_wales_source_urls)
import Tides.Published.NewSouthWales (new_south_wales_published_holidays)
import Tides.Rules (contains_day)
import Tides.TestSupport.Support (normalized_year, observed_rule_days, diff_text, holidays_of, all_closed)
def test_horizon_is_the_published_span() -> unit ! { Test } = {
  cal = new_south_wales()
  _ = assert_eq(business_calendar_valid_from(cal), date(2026i64, 1i64, 1i64), "valid_from")
  _ = assert_eq(business_calendar_valid_until(cal), date(2027i64, 12i64, 31i64), "valid_until")
  assert_eq(index(new_south_wales_source_urls(), 0i64), "https://www.nsw.gov.au/about-nsw/public-holidays", "url")
}
def test_every_published_holiday_is_closed() -> unit ! { Test } = {
  cal = new_south_wales()
  _ = assert_eq(len(holidays_of(cal)), 18i64, "18 weekday public holidays in 2026..2027")
  assert_eq(all_closed(cal, new_south_wales_published_holidays()), true, "no published holiday is a business day")
}
def published_year(year: i64) -> List[Date] = normalized_year(new_south_wales_weekmask(), new_south_wales_published_holidays(), year)
def rule_year(year: i64) -> List[Date] = observed_rule_days(new_south_wales_weekmask(), new_south_wales_rule_holidays, year)
-- The section 4 rules give every published day but the ones the Minister declared
-- for those years only: the additional days for a weekend Anzac Day.
def test_rules_match_published_years_but_declared_days() -> unit ! { Test } = {
  _ = assert_eq(diff_text(published_year(2026i64), rule_year(2026i64)), "only in the first: 2026-04-27 ; only in the second: ", "2026: declared additional day for Saturday Anzac Day")
  assert_eq(diff_text(published_year(2027i64), rule_year(2027i64)), "only in the first: 2027-04-26 ; only in the second: ", "2027: declared additional day for Sunday Anzac Day")
}
-- Christmas and Boxing Day each keep their own additional day; a Saturday
-- Christmas and Sunday Boxing Day do not share one Monday.
def test_christmas_and_boxing_day_collision() -> unit ! { Test } = {
  cal = new_south_wales()
  _ = assert_eq(is_business_day(cal, date(2027i64, 12i64, 27i64)), false, "2027: additional day for Saturday Christmas")
  _ = assert_eq(is_business_day(cal, date(2027i64, 12i64, 28i64)), false, "2027: additional day for Sunday Boxing Day")
  _ = assert_eq(is_business_day(cal, date(2026i64, 12i64, 28i64)), false, "2026: additional day for Saturday Boxing Day")
  _ = assert_eq(is_business_day(cal, date(2026i64, 4i64, 27i64)), false, "2026: additional day for Saturday Anzac Day")
  assert_eq(is_business_day(cal, date(2026i64, 8i64, 3i64)), true, "the Bank Holiday is not a public holiday")
}
def test_queries_outside_the_horizon_are_none() -> unit ! { Test } = {
  cal = new_south_wales()
  _ = assert_eq(try_is_business_day(cal, date(2025i64, 12i64, 31i64)), None, "day before the horizon")
  assert_eq(try_is_business_day(cal, date(2028i64, 1i64, 3i64)), None, "day after the horizon")
}
def test_projection() -> unit ! { Test } = {
  cal = new_south_wales_projected(2033i64)
  _ = assert_eq(is_business_day(cal, date(2028i64, 1i64, 26i64)), false, "Australia Day 2028")
  _ = assert_eq(is_business_day(cal, date(2032i64, 12i64, 27i64)), false, "2032: Saturday Christmas, additional Monday")
  _ = assert_eq(is_business_day(cal, date(2032i64, 12i64, 28i64)), false, "2032: Sunday Boxing Day, additional Tuesday")
  _ = assert_eq(is_business_day(cal, date(2033i64, 12i64, 27i64)), false, "2033: Sunday Christmas, additional Tuesday")
  _ = assert_eq(is_business_day(cal, date(2033i64, 1i64, 3i64)), false, "2033: Saturday New Year, additional Monday")
  _ = assert_eq(is_business_day(cal, date(2032i64, 4i64, 26i64)), true, "2032: no additional day for Sunday Anzac Day; declared days are never projected")
  _ = assert_eq(contains_day(new_south_wales_rule_holidays(2026i64), date(2026i64, 4i64, 27i64)), false, "no rule gives a declared day")
  _ = assert_eq(try_new_south_wales_projected(2027i64), None, "the published last year")
  assert_eq(try_new_south_wales_projected(10000i64), None, "after the last projection year")
}

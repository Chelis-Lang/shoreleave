module Tides.Tests.EnglandAndWales
import Std.Datetime (Date, date)
import Std.Datetime.Business (is_business_day, try_is_business_day, business_calendar_valid_from, business_calendar_valid_until)
import Std.Test (assert_eq)
import Tides.EnglandAndWales (england_and_wales, england_and_wales_projected, try_england_and_wales_projected, england_and_wales_rule_holidays, england_and_wales_weekmask, england_and_wales_source, england_and_wales_source_urls, england_and_wales_retrieved)
import Tides.Published.EnglandAndWales (england_and_wales_published_holidays)
import Tides.TestSupport.Support (normalized_year, observed_rule_days, diff_text, holidays_of)
def published_year(year: i64) -> List[Date] = normalized_year(england_and_wales_weekmask(), england_and_wales_published_holidays(), year)
def rule_year(year: i64) -> List[Date] = observed_rule_days(england_and_wales_weekmask(), england_and_wales_rule_holidays, year)
def test_horizon_is_the_published_span() -> unit ! { Test } = {
  cal = england_and_wales()
  _ = assert_eq(business_calendar_valid_from(cal), date(2019i64, 1i64, 1i64), "valid_from")
  assert_eq(business_calendar_valid_until(cal), date(2028i64, 12i64, 31i64), "valid_until")
}
def test_every_published_weekday_holiday_is_closed() -> unit ! { Test } = {
  cal = england_and_wales()
  _ = assert_eq(len(holidays_of(cal)), 83i64, "83 published bank holidays, all on weekdays")
  assert_eq(fold(fn (acc: bool, d: Date) -> and(acc, not(is_business_day(cal, d))), true, england_and_wales_published_holidays()), true, "no published holiday is a business day")
}
def test_provenance() -> unit ! { Test } = {
  _ = assert_eq(england_and_wales_source(), "UK Government Digital Service, gov.uk bank holidays", "source")
  _ = assert_eq(index(england_and_wales_source_urls(), 0i64), "https://www.gov.uk/bank-holidays.json", "url")
  assert_eq(england_and_wales_retrieved(), date(2026i64, 10i64, 5i64), "retrieved")
}
def test_rules_match_every_unproclaimed_published_year() -> unit ! { Test } = {
  _ = assert_eq(diff_text(rule_year(2019i64), published_year(2019i64)), "", "2019")
  _ = assert_eq(diff_text(rule_year(2021i64), published_year(2021i64)), "", "2021")
  _ = assert_eq(diff_text(rule_year(2024i64), published_year(2024i64)), "", "2024")
  _ = assert_eq(diff_text(rule_year(2025i64), published_year(2025i64)), "", "2025")
  _ = assert_eq(diff_text(rule_year(2026i64), published_year(2026i64)), "", "2026")
  _ = assert_eq(diff_text(rule_year(2027i64), published_year(2027i64)), "", "2027")
  assert_eq(diff_text(rule_year(2028i64), published_year(2028i64)), "", "2028")
}
-- The proclaimed years differ from the rules by exactly the proclaimed days, which
-- is what a projection omits.
def test_rules_omit_exactly_the_proclaimed_days() -> unit ! { Test } = {
  _ = assert_eq(diff_text(published_year(2020i64), rule_year(2020i64)), "only in the first: 2020-05-08 ; only in the second: 2020-05-04 ", "2020: early May bank holiday moved for VE Day")
  _ = assert_eq(diff_text(published_year(2022i64), rule_year(2022i64)), "only in the first: 2022-06-02 2022-06-03 2022-09-19 ; only in the second: 2022-05-30 ", "2022: spring bank holiday moved, Platinum Jubilee, State Funeral")
  assert_eq(diff_text(published_year(2023i64), rule_year(2023i64)), "only in the first: 2023-05-08 ; only in the second: ", "2023: Coronation")
}
def test_weekend_christmas_substitutes() -> unit ! { Test } = {
  cal = england_and_wales()
  _ = assert_eq(is_business_day(cal, date(2027i64, 12i64, 27i64)), false, "2027: Saturday Christmas Day moves to Monday 27th")
  _ = assert_eq(is_business_day(cal, date(2027i64, 12i64, 28i64)), false, "2027: Sunday Boxing Day moves to Tuesday 28th")
  _ = assert_eq(is_business_day(cal, date(2027i64, 12i64, 29i64)), true, "2027: Wednesday 29th is open")
  _ = assert_eq(is_business_day(cal, date(2022i64, 12i64, 27i64)), false, "2022: Sunday Christmas Day moves to Tuesday 27th")
  _ = assert_eq(is_business_day(cal, date(2026i64, 12i64, 28i64)), false, "2026: Saturday Boxing Day moves to Monday 28th")
  assert_eq(is_business_day(cal, date(2022i64, 1i64, 3i64)), false, "2022: Saturday New Year's Day moves to Monday 3rd")
}
def test_queries_outside_the_horizon_are_none() -> unit ! { Test } = {
  cal = england_and_wales()
  _ = assert_eq(try_is_business_day(cal, date(2018i64, 12i64, 31i64)), None, "day before the horizon")
  _ = assert_eq(try_is_business_day(cal, date(2029i64, 1i64, 1i64)), None, "day after the horizon")
  assert_eq(try_is_business_day(cal, date(2028i64, 12i64, 29i64)), Some(true), "last Friday inside it")
}
def test_projection_extends_by_rule_only() -> unit ! { Test } = {
  cal = england_and_wales_projected(2032i64)
  _ = assert_eq(business_calendar_valid_until(cal), date(2032i64, 12i64, 31i64), "horizon ends with until_year")
  _ = assert_eq(business_calendar_valid_from(cal), date(2019i64, 1i64, 1i64), "horizon starts with the published one")
  _ = assert_eq(is_business_day(cal, date(2022i64, 9i64, 19i64)), false, "published proclaimed days are kept")
  _ = assert_eq(is_business_day(cal, date(2029i64, 5i64, 7i64)), false, "2029 early May bank holiday")
  _ = assert_eq(is_business_day(cal, date(2032i64, 12i64, 27i64)), false, "2032: Saturday Christmas Day moves to Monday 27th")
  assert_eq(is_business_day(cal, date(2032i64, 12i64, 28i64)), false, "2032: Sunday Boxing Day moves to Tuesday 28th")
}
def test_projection_refuses_years_it_cannot_extend() -> unit ! { Test } = {
  _ = assert_eq(is_business_day(england_and_wales_projected(2029i64), date(2029i64, 12i64, 31i64)), true, "a one-year projection")
  _ = assert_eq(try_england_and_wales_projected(2028i64), None, "the published last year")
  _ = assert_eq(try_england_and_wales_projected(2020i64), None, "inside the published horizon")
  assert_eq(try_england_and_wales_projected(9999i64), None, "after the last projection year")
}

module Shoreleave.Tests.UsFederal
import Std.Datetime (Date, date)
import Std.Datetime.Business (is_business_day, try_is_business_day, business_calendar_valid_from, business_calendar_valid_until)
import Std.Test (assert_eq)
import Shoreleave.UsFederal (us_federal, us_federal_projected, try_us_federal_projected, us_federal_rule_holidays, us_federal_weekmask, us_federal_source, us_federal_source_urls)
import Shoreleave.Published.UsFederal (us_federal_published_holidays)
import Shoreleave.Rules (contains_day)
import Shoreleave.TestSupport.Support (normalized_year, observed_rule_days, diff_text, mismatches_by_year, holidays_of, all_closed)
def published_year(year: i64) -> List[Date] = normalized_year(us_federal_weekmask(), us_federal_published_holidays(), year)
def rule_year(year: i64) -> List[Date] = observed_rule_days(us_federal_weekmask(), us_federal_rule_holidays, year)
def test_horizon_is_the_published_span() -> unit ! { Test } = {
  cal = us_federal()
  _ = assert_eq(business_calendar_valid_from(cal), date(2021i64, 1i64, 1i64), "valid_from")
  _ = assert_eq(business_calendar_valid_until(cal), date(2030i64, 12i64, 31i64), "valid_until")
  _ = assert_eq(index(us_federal_source_urls(), 0i64), "https://www.opm.gov/policy-data-oversight/pay-leave/federal-holidays/holidays.ics", "OPM feed")
  _ = assert_eq(index(us_federal_source_urls(), 3i64), "https://www.federalregister.gov/documents/full_text/text/2025/12/23/2025-23847.txt", "Executive Order 14371")
  assert_eq(us_federal_source(), "US Office of Personnel Management, federal holidays; Federal Register, executive orders closing executive departments", "both sources are named")
}
def test_every_published_holiday_is_closed() -> unit ! { Test } = {
  cal = us_federal()
  _ = assert_eq(len(holidays_of(cal)), 114i64, "110 observed legal public holidays and 4 executive-order closures in 2021..2030")
  assert_eq(all_closed(cal, us_federal_published_holidays()), true, "no published holiday is a business day")
}
-- Every year without an executive-order closure: the rules give exactly OPM's
-- observed days, Juneteenth's first year and every weekend shift included.
def test_rules_match_every_published_year_without_closures() -> unit ! { Test } = assert_eq(mismatches_by_year(us_federal_weekmask(), us_federal_rule_holidays, us_federal_published_holidays(), [2021i64, 2022i64, 2023i64, 2026i64, 2027i64, 2028i64, 2029i64, 2030i64]), "", "rules against OPM")
-- The executive-order closures are exactly what the rules lack in 2024 and 2025,
-- and so what a projection omits.
def test_rules_omit_exactly_the_executive_order_closures() -> unit ! { Test } = {
  _ = assert_eq(diff_text(published_year(2024i64), rule_year(2024i64)), "only in the first: 2024-12-24 ; only in the second: ", "2024: Executive Order 14129")
  assert_eq(diff_text(published_year(2025i64), rule_year(2025i64)), "only in the first: 2025-01-09 2025-12-24 2025-12-26 ; only in the second: ", "2025: Executive Orders 14133 and 14371")
}
-- The observed day can fall in the year before: index by observed date.
def test_saturday_new_year_is_observed_the_friday_before() -> unit ! { Test } = {
  cal = us_federal()
  _ = assert_eq(is_business_day(cal, date(2021i64, 12i64, 31i64)), false, "1 January 2022 is a Saturday")
  _ = assert_eq(is_business_day(cal, date(2027i64, 12i64, 31i64)), false, "1 January 2028 is a Saturday")
  _ = assert_eq(is_business_day(cal, date(2023i64, 1i64, 2i64)), false, "1 January 2023 is a Sunday")
  assert_eq(is_business_day(cal, date(2027i64, 6i64, 18i64)), false, "Saturday Juneteenth 2027 is observed on Friday 18th")
}
def test_executive_order_closures_are_closed() -> unit ! { Test } = {
  cal = us_federal()
  _ = assert_eq(is_business_day(cal, date(2025i64, 1i64, 9i64)), false, "Carter day of mourning, Executive Order 14133")
  _ = assert_eq(is_business_day(cal, date(2024i64, 12i64, 24i64)), false, "Executive Order 14129")
  _ = assert_eq(is_business_day(cal, date(2025i64, 12i64, 24i64)), false, "Executive Order 14371")
  assert_eq(is_business_day(cal, date(2025i64, 12i64, 26i64)), false, "Executive Order 14371")
}
-- Inauguration Day is a holiday only in the Washington, DC area.
def test_inauguration_day_is_open() -> unit ! { Test } = {
  cal = us_federal()
  _ = assert_eq(is_business_day(cal, date(2021i64, 1i64, 20i64)), true, "2021 Inauguration Day")
  assert_eq(is_business_day(cal, date(2029i64, 1i64, 22i64)), true, "the Monday after the 2029 inauguration")
}
def test_queries_outside_the_horizon_are_none() -> unit ! { Test } = {
  cal = us_federal()
  _ = assert_eq(try_is_business_day(cal, date(2020i64, 12i64, 31i64)), None, "day before the horizon")
  assert_eq(try_is_business_day(cal, date(2031i64, 1i64, 1i64)), None, "day after the horizon")
}
def test_projection() -> unit ! { Test } = {
  cal = us_federal_projected(2033i64)
  _ = assert_eq(business_calendar_valid_until(cal), date(2033i64, 12i64, 31i64), "horizon ends with until_year")
  _ = assert_eq(is_business_day(cal, date(2032i64, 12i64, 31i64)), false, "1 January 2033 is a Saturday, observed on 31 December 2032")
  _ = assert_eq(is_business_day(cal, date(2033i64, 6i64, 20i64)), false, "Sunday Juneteenth 2033 is observed on Monday")
  _ = assert_eq(is_business_day(cal, date(2033i64, 12i64, 30i64)), true, "1 January 2034 is a Sunday, so Friday 30 December 2033 is open")
  _ = assert_eq(contains_day(us_federal_rule_holidays(2025i64), date(2025i64, 1i64, 9i64)), false, "no rule gives an executive-order closure")
  _ = assert_eq(try_us_federal_projected(2030i64), None, "the published last year")
  _ = assert_eq(try_us_federal_projected(-20000i64), None, "a year outside the date range")
  assert_eq(try_us_federal_projected(9999i64), None, "after the last projection year")
}

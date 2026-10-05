module BedHolidays.Tests.UsFederal
import Std.Datetime (Date, date)
import Std.Datetime.Business (is_business_day, try_is_business_day, business_calendar_valid_from, business_calendar_valid_until)
import Std.Test (assert_eq)
import BedHolidays.UsFederal (us_federal, us_federal_projected, try_us_federal_projected, us_federal_rule_holidays, us_federal_weekmask, us_federal_source_url)
import BedHolidays.Published.UsFederal (us_federal_published_holidays)
import BedHolidays.TestSupport.Support (mismatches_by_year, holidays_of, all_closed)
def test_horizon_is_the_published_span() -> unit ! { Test } = {
  cal = us_federal()
  _ = assert_eq(business_calendar_valid_from(cal), date(2011i64, 1i64, 1i64), "valid_from")
  _ = assert_eq(business_calendar_valid_until(cal), date(2030i64, 12i64, 31i64), "valid_until")
  assert_eq(us_federal_source_url(), "https://www.opm.gov/policy-data-oversight/pay-leave/federal-holidays/", "url")
}
def test_every_published_holiday_is_closed() -> unit ! { Test } = {
  cal = us_federal()
  _ = assert_eq(len(holidays_of(cal)), 209i64, "209 observed holidays in 2011..2030")
  assert_eq(all_closed(cal, us_federal_published_holidays()), true, "no published holiday is a business day")
}
-- Every published year: the rules give exactly OPM's observed days, Juneteenth's
-- first year and every Saturday and Sunday shift included.
def test_rules_match_every_published_year() -> unit ! { Test } = assert_eq(mismatches_by_year(us_federal_weekmask(), us_federal_rule_holidays, us_federal_published_holidays(), range(2011i64, 2031i64)), "", "rules against OPM, 2011..2030")
def test_saturday_new_year_is_observed_the_friday_before() -> unit ! { Test } = {
  cal = us_federal()
  _ = assert_eq(is_business_day(cal, date(2021i64, 12i64, 31i64)), false, "1 January 2022 is a Saturday")
  _ = assert_eq(is_business_day(cal, date(2027i64, 12i64, 31i64)), false, "1 January 2028 is a Saturday")
  _ = assert_eq(is_business_day(cal, date(2023i64, 1i64, 2i64)), false, "1 January 2023 is a Sunday")
  assert_eq(is_business_day(cal, date(2025i64, 1i64, 20i64)), false, "Inauguration Day 2025 is closed only as Martin Luther King Day")
}
-- Inauguration Day and executive-order closures are not legal public holidays.
def test_regional_and_announced_closures_are_open() -> unit ! { Test } = {
  cal = us_federal()
  _ = assert_eq(is_business_day(cal, date(2013i64, 1i64, 21i64)), false, "2013 Inauguration Day coincides with Martin Luther King Day")
  _ = assert_eq(is_business_day(cal, date(2021i64, 1i64, 20i64)), true, "2021 Inauguration Day, a DC-area holiday, is open")
  _ = assert_eq(is_business_day(cal, date(2024i64, 12i64, 24i64)), true, "24 December 2024, closed by executive order, is open")
  assert_eq(is_business_day(cal, date(2025i64, 1i64, 9i64)), true, "9 January 2025, a national day of mourning, is open")
}
def test_queries_outside_the_horizon_are_none() -> unit ! { Test } = {
  cal = us_federal()
  _ = assert_eq(try_is_business_day(cal, date(2010i64, 12i64, 31i64)), None, "day before the horizon")
  assert_eq(try_is_business_day(cal, date(2031i64, 1i64, 1i64)), None, "day after the horizon")
}
def test_projection() -> unit ! { Test } = {
  cal = us_federal_projected(2033i64)
  _ = assert_eq(business_calendar_valid_until(cal), date(2033i64, 12i64, 31i64), "horizon ends with until_year")
  _ = assert_eq(is_business_day(cal, date(2032i64, 12i64, 31i64)), false, "1 January 2033 is a Saturday, observed on 31 December 2032")
  _ = assert_eq(is_business_day(cal, date(2033i64, 6i64, 20i64)), false, "Sunday Juneteenth 2033 is observed on Monday")
  _ = assert_eq(is_business_day(cal, date(2033i64, 12i64, 30i64)), true, "1 January 2034 is a Sunday, so Friday 30 December 2033 is open")
  _ = assert_eq(try_us_federal_projected(2030i64), None, "the published last year")
  _ = assert_eq(try_us_federal_projected(-20000i64), None, "a year outside the date range")
  assert_eq(try_us_federal_projected(9999i64), None, "after the last projection year")
}

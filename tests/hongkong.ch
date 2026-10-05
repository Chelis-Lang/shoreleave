module Tides.Tests.HongKong
import Std.Datetime (Date, date)
import Std.Datetime.Business (is_business_day, try_is_business_day, business_calendar_valid_from, business_calendar_valid_until, business_calendar_weekmask)
import Std.Test (assert_eq)
import Tides.HongKong (hong_kong, hong_kong_projected, try_hong_kong_projected, hong_kong_rule_holidays, hong_kong_weekmask, hong_kong_source_urls)
import Tides.Published.HongKong (hong_kong_published_holidays)
import Tides.TestSupport.Support (normalized_year, observed_rule_days, diff_text, holidays_of, all_closed)
def published_year(year: i64) -> List[Date] = normalized_year(hong_kong_weekmask(), hong_kong_published_holidays(), year)
def rule_year(year: i64) -> List[Date] = observed_rule_days(hong_kong_weekmask(), hong_kong_rule_holidays, year)
def test_horizon_is_the_published_span() -> unit ! { Test } = {
  cal = hong_kong()
  _ = assert_eq(business_calendar_valid_from(cal), date(2025i64, 1i64, 1i64), "valid_from")
  _ = assert_eq(business_calendar_valid_until(cal), date(2027i64, 12i64, 31i64), "valid_until")
  _ = assert_eq(business_calendar_weekmask(cal).saturday, true, "Saturday is not a general holiday")
  assert_eq(index(hong_kong_source_urls(), 0i64), "https://www.1823.gov.hk/common/ical/en.json", "url")
}
def test_every_published_holiday_is_closed() -> unit ! { Test } = {
  cal = hong_kong()
  _ = assert_eq(len(holidays_of(cal)), 51i64, "51 general holidays in 2025..2027, none on a Sunday")
  assert_eq(all_closed(cal, hong_kong_published_holidays()), true, "no published holiday is a business day")
}
-- The published days the rules do not give are exactly the lunar and solar-term
-- holidays and their substitutes, plus 7 April 2026, where Easter Monday moved
-- because the day after Ching Ming took 6 April. Every rule day is published.
def test_rules_omit_exactly_lunar_and_solar_term_holidays() -> unit ! { Test } = {
  _ = assert_eq(diff_text(published_year(2025i64), rule_year(2025i64)), "only in the first: 2025-01-29 2025-01-30 2025-01-31 2025-04-04 2025-05-05 2025-05-31 2025-10-07 2025-10-29 ; only in the second: ", "2025")
  _ = assert_eq(diff_text(published_year(2026i64), rule_year(2026i64)), "only in the first: 2026-02-17 2026-02-18 2026-02-19 2026-04-07 2026-05-25 2026-06-19 2026-09-26 2026-10-19 ; only in the second: ", "2026")
  assert_eq(diff_text(published_year(2027i64), rule_year(2027i64)), "only in the first: 2027-02-06 2027-02-08 2027-02-09 2027-04-05 2027-05-13 2027-06-09 2027-09-16 2027-10-08 ; only in the second: ", "2027")
}
def test_sunday_and_saturday_rules() -> unit ! { Test } = {
  cal = hong_kong()
  _ = assert_eq(is_business_day(cal, date(2026i64, 4i64, 6i64)), false, "2026: the day following Ching Ming, a Sunday")
  _ = assert_eq(is_business_day(cal, date(2026i64, 4i64, 7i64)), false, "2026: the day following Easter Monday, pushed on by the Ching Ming substitute")
  _ = assert_eq(is_business_day(cal, date(2027i64, 2i64, 9i64)), false, "2027: the fourth day of Lunar New Year replaces the Sunday second day")
  _ = assert_eq(is_business_day(cal, date(2027i64, 5i64, 1i64)), false, "a Saturday holiday closes Saturday")
  _ = assert_eq(is_business_day(cal, date(2027i64, 12i64, 27i64)), false, "2027: Saturday Christmas, first weekday after it is Monday 27th")
  _ = assert_eq(is_business_day(cal, date(2026i64, 12i64, 26i64)), false, "2026: first weekday after Christmas is Saturday 26th")
  assert_eq(is_business_day(cal, date(2026i64, 12i64, 28i64)), true, "2026: Monday 28th is open")
}
def test_queries_outside_the_horizon_are_none() -> unit ! { Test } = {
  cal = hong_kong()
  _ = assert_eq(try_is_business_day(cal, date(2024i64, 12i64, 31i64)), None, "day before the horizon")
  assert_eq(try_is_business_day(cal, date(2028i64, 1i64, 1i64)), None, "day after the horizon")
}
-- A projection has no lunar or solar-term holiday: Lunar New Year 2028 (26 to 28
-- January) and Ching Ming 2028 (4 April) are business days in it.
def test_projection_omits_lunar_and_solar_term_holidays() -> unit ! { Test } = {
  cal = hong_kong_projected(2033i64)
  _ = assert_eq(is_business_day(cal, date(2028i64, 1i64, 26i64)), true, "Lunar New Year 2028 is not projected")
  _ = assert_eq(is_business_day(cal, date(2028i64, 4i64, 4i64)), true, "Ching Ming 2028 is not projected")
  _ = assert_eq(is_business_day(cal, date(2028i64, 10i64, 2i64)), false, "2028: Sunday National Day moves to Monday")
  _ = assert_eq(is_business_day(cal, date(2033i64, 12i64, 26i64)), false, "2033: Sunday Christmas moves to Monday 26th")
  _ = assert_eq(is_business_day(cal, date(2033i64, 12i64, 27i64)), false, "2033: first weekday after Christmas is Tuesday 27th")
  _ = assert_eq(try_hong_kong_projected(2027i64), None, "the published last year")
  assert_eq(try_hong_kong_projected(10000i64), None, "after the last projection year")
}

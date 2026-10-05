module BedHolidays.Tests.NewSouthWales
import Std.Datetime (Date, date)
import Std.Datetime.Business (is_business_day, try_is_business_day, business_calendar_valid_from, business_calendar_valid_until)
import Std.Test (assert_eq)
import BedHolidays.NewSouthWales (new_south_wales, new_south_wales_projected, try_new_south_wales_projected, new_south_wales_rule_holidays, new_south_wales_weekmask, new_south_wales_source_url)
import BedHolidays.Published.NewSouthWales (new_south_wales_published_holidays)
import BedHolidays.TestSupport.Support (mismatches_by_year, holidays_of, all_closed)
def test_horizon_is_the_published_span() -> unit ! { Test } = {
  cal = new_south_wales()
  _ = assert_eq(business_calendar_valid_from(cal), date(2026i64, 1i64, 1i64), "valid_from")
  _ = assert_eq(business_calendar_valid_until(cal), date(2027i64, 12i64, 31i64), "valid_until")
  assert_eq(new_south_wales_source_url(), "https://www.nsw.gov.au/about-nsw/public-holidays", "url")
}
def test_every_published_holiday_is_closed() -> unit ! { Test } = {
  cal = new_south_wales()
  _ = assert_eq(len(holidays_of(cal)), 18i64, "18 weekday public holidays in 2026..2027")
  assert_eq(all_closed(cal, new_south_wales_published_holidays()), true, "no published holiday is a business day")
}
def test_rules_match_every_published_year() -> unit ! { Test } = assert_eq(mismatches_by_year(new_south_wales_weekmask(), new_south_wales_rule_holidays, new_south_wales_published_holidays(), range(2026i64, 2028i64)), "", "rules against the NSW Government, 2026..2027")
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
  _ = assert_eq(try_new_south_wales_projected(2027i64), None, "the published last year")
  assert_eq(try_new_south_wales_projected(10000i64), None, "after the last projection year")
}

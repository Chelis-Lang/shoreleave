module Shoreleave.Tests.JapanBank
import Std.Datetime (Date, date)
import Std.Datetime.Business (is_business_day, try_is_business_day, business_calendar_valid_from, business_calendar_valid_until)
import Std.Test (assert_eq)
import Shoreleave.JapanBank (japan_bank, japan_bank_projected, try_japan_bank_projected, japan_bank_rule_holidays, japan_bank_weekmask, japan_bank_source_urls, japan_vernal_equinox_day, japan_autumnal_equinox_day)
import Shoreleave.Published.JapanBank (japan_bank_published_holidays)
import Shoreleave.Rules (contains_day, joined)
import Shoreleave.TestSupport.Support (normalized_year, observed_rule_days, diff_text, mismatches_by_year, holidays_of, all_closed)
def test_horizon_starts_with_the_saturday_closure() -> unit ! { Test } = {
  cal = japan_bank()
  _ = assert_eq(business_calendar_valid_from(cal), date(1990i64, 1i64, 1i64), "valid_from")
  _ = assert_eq(business_calendar_valid_until(cal), date(2027i64, 12i64, 31i64), "valid_until")
  assert_eq(index(japan_bank_source_urls(), 0i64), "https://www8.cao.go.jp/chosei/shukujitsu/syukujitsu.csv", "url")
}
def test_every_published_holiday_is_closed() -> unit ! { Test } = assert_eq(all_closed(japan_bank(), japan_bank_published_holidays()), true, "no published holiday is a business day")
-- The equinox formula gives the published equinox day in every year of the horizon.
def test_equinox_formula_matches_every_published_year() -> unit ! { Test } = {
  published = japan_bank_published_holidays()
  misses = joined(map(fn (year: i64) -> if and(contains_day(published, date(year, 3i64, japan_vernal_equinox_day(year))), contains_day(published, date(year, 9i64, japan_autumnal_equinox_day(year)))) then "" else string_concat(to_string(year), " "), range(1990i64, 2028i64)))
  assert_eq(misses, "", "equinox formula against the Cabinet Office, 1990..2027")
}
-- The rules state the Act from 2020; 2020 and 2021 carry the one-year Olympic moves.
def test_rules_match_every_published_year_under_the_current_act() -> unit ! { Test } = assert_eq(mismatches_by_year(japan_bank_weekmask(), japan_bank_rule_holidays, japan_bank_published_holidays(), range(2022i64, 2028i64)), "", "rules against the Cabinet Office, 2022..2027")
def test_rules_omit_one_year_statutory_moves() -> unit ! { Test } = assert_eq(diff_text(normalized_year(japan_bank_weekmask(), japan_bank_published_holidays(), 2021i64), observed_rule_days(japan_bank_weekmask(), japan_bank_rule_holidays, 2021i64)), "only in the first: 2021-07-22 2021-07-23 2021-08-09 ; only in the second: 2021-07-19 2021-08-11 2021-10-11 ", "2021: Olympic moves of Marine Day, Sports Day and Mountain Day")
def test_bank_substitute_and_citizens_holidays() -> unit ! { Test } = {
  cal = japan_bank()
  _ = assert_eq(is_business_day(cal, date(2026i64, 1i64, 2i64)), false, "2 January bank closure")
  _ = assert_eq(is_business_day(cal, date(2026i64, 12i64, 31i64)), false, "31 December bank closure")
  _ = assert_eq(is_business_day(cal, date(2026i64, 5i64, 6i64)), false, "2026: Sunday 3 May, substitute on Wednesday 6 May")
  _ = assert_eq(is_business_day(cal, date(2026i64, 9i64, 22i64)), false, "2026: citizen's holiday between Respect for the Aged Day and the equinox")
  assert_eq(is_business_day(cal, date(2026i64, 12i64, 30i64)), true, "30 December is open")
}
def test_queries_outside_the_horizon_are_none() -> unit ! { Test } = {
  cal = japan_bank()
  _ = assert_eq(try_is_business_day(cal, date(1989i64, 12i64, 29i64)), None, "before 1990")
  assert_eq(try_is_business_day(cal, date(2028i64, 1i64, 4i64)), None, "after the horizon")
}
def test_projection() -> unit ! { Test } = {
  cal = japan_bank_projected(2032i64)
  _ = assert_eq(is_business_day(cal, date(2028i64, 3i64, 20i64)), false, "vernal equinox 2028")
  _ = assert_eq(is_business_day(cal, date(2032i64, 9i64, 21i64)), false, "2032: citizen's holiday")
  _ = assert_eq(is_business_day(cal, date(2028i64, 1i64, 3i64)), false, "3 January 2028 bank closure")
  _ = assert_eq(try_japan_bank_projected(2027i64), None, "the published last year")
  assert_eq(try_japan_bank_projected(2100i64), None, "after the equinox formula's last year")
}

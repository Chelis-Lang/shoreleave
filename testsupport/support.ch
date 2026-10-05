module Shoreleave.TestSupport.Support
import Std.Datetime (Date, date, date_epoch_day, date_to_string)
import Std.Datetime.Business (Weekmask, BusinessCalendar, business_calendar, business_calendar_holidays, is_business_day)
import Shoreleave.Rules (contains_day, days_in_year, joined)
export (normalized_year, observed_rule_days, difference, days_text, diff_text, holidays_of, mismatches_by_year, all_closed)
-- Shared helpers for the calendar tests.
-- The days of `days` in `year` that are business weekdays under `weekmask`,
-- sorted and unique, as a calendar over that year normalizes them.
def normalized_year(weekmask: Weekmask, days: List[Date], year: i64) -> List[Date] = business_calendar_holidays(business_calendar(weekmask, days_in_year(days, year), date(year, 1i64, 1i64), date(year, 12i64, 31i64)))
-- The rule holidays observed in `year`, including those the next year's rules
-- observe in it (a Saturday 1 January observed on 31 December).
def observed_rule_days(weekmask: Weekmask, rule: i64 -> List[Date], year: i64) -> List[Date] = normalized_year(weekmask, flatten([rule(year), rule(add(year, 1i64))]), year)
def difference(a: List[Date], b: List[Date]) -> List[Date] = filter(fn (d: Date) -> not(contains_day(b, d)), a)
def days_text(days: List[Date]) -> string = joined(map(fn (d: Date) -> string_concat(date_to_string(d), " "), days))
-- "" when the two lists hold the same days; otherwise the days only one of them holds.
def diff_text(a: List[Date], b: List[Date]) -> string = {
  only_a = difference(a, b)
  only_b = difference(b, a)
  if and(eq(len(only_a), 0i64), eq(len(only_b), 0i64)) then "" else joined(["only in the first: ", days_text(only_a), "; only in the second: ", days_text(only_b)])
}
def holidays_of(cal: BusinessCalendar) -> List[Date] = business_calendar_holidays(cal)
-- "" when the rules give exactly the published holidays in every year of `years`;
-- otherwise each differing year with its difference.
def mismatches_by_year(weekmask: Weekmask, rule: i64 -> List[Date], published: List[Date], years: List[i64]) -> string =
  joined(map(fn (year: i64) -> {
    d = diff_text(observed_rule_days(weekmask, rule, year), normalized_year(weekmask, published, year))
    if eq(d, "") then "" else joined([to_string(year), ": ", d, "| "])
  }, years))
-- True when no day of `days` is a business day of `cal`.
def all_closed(cal: BusinessCalendar, days: List[Date]) -> bool = fold(fn (acc: bool, d: Date) -> and(acc, not(is_business_day(cal, d))), true, days)

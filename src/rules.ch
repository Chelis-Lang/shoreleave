module Tides.Rules
import Std.Datetime (Date, Weekday, Monday, Saturday, Sunday, date, date_year, date_weekday, date_add_days, date_epoch_day, weekday_iso_number, nth_weekday_in_month, last_weekday_in_month, weekday_on_or_after, easter_sunday_gregorian)
import Std.Datetime.Business (Weekmask, BusinessCalendar, business_calendar, try_business_calendar)
export (monday_to_friday, monday_to_saturday, nth_weekday, last_weekday, is_saturday, is_sunday, is_weekend, good_friday, easter_saturday, easter_monday, saturday_back_sunday_forward, weekend_forward_to_monday, sunday_forward_to_monday, new_year_with_additional_day, christmas_and_boxing_with_additional_days, contains_day, days_in_year, joined, projection_problem, projected_calendar, try_projected_calendar)
-- Holiday-rule building blocks shared by the calendars, and the one projection
-- constructor every `<calendar>_projected` uses. Observance rules belong to each
-- calendar's own module; nothing here consults data.
def monday_to_friday() -> Weekmask = Weekmask { monday: true, tuesday: true, wednesday: true, thursday: true, friday: true, saturday: false, sunday: false }
def monday_to_saturday() -> Weekmask = Weekmask { monday: true, tuesday: true, wednesday: true, thursday: true, friday: true, saturday: true, sunday: false }
def nth_weekday(year: i64, month: i64, w: Weekday, n: i64) -> Date =
  match nth_weekday_in_month(year, month, w, n) with {
    | Some(d) => d
    | None => fail(joined(["nth_weekday: domain: month ", to_string(month), " of ", to_string(year), " has fewer than ", to_string(n), " of that weekday"]))
  }
def last_weekday(year: i64, month: i64, w: Weekday) -> Date = last_weekday_in_month(year, month, w)
def iso_weekday(d: Date) -> i64 = weekday_iso_number(date_weekday(d))
def is_saturday(d: Date) -> bool = eq(iso_weekday(d), 6i64)
def is_sunday(d: Date) -> bool = eq(iso_weekday(d), 7i64)
def is_weekend(d: Date) -> bool = gte(iso_weekday(d), 6i64)
def good_friday(year: i64) -> Date = date_add_days(easter_sunday_gregorian(year), -2i64)
def easter_saturday(year: i64) -> Date = date_add_days(easter_sunday_gregorian(year), -1i64)
def easter_monday(year: i64) -> Date = date_add_days(easter_sunday_gregorian(year), 1i64)
-- A Saturday holiday is observed on the Friday before it and a Sunday holiday on
-- the Monday after it (the US federal rule, 5 U.S.C. 6103(b) and Executive Order
-- 11582, which the US markets also follow for most holidays).
def saturday_back_sunday_forward(d: Date) -> Date = if is_saturday(d) then date_add_days(d, -1i64) else if is_sunday(d) then date_add_days(d, 1i64) else d
def weekend_forward_to_monday(d: Date) -> Date = if is_weekend(d) then weekday_on_or_after(d, Monday) else d
def sunday_forward_to_monday(d: Date) -> Date = if is_sunday(d) then date_add_days(d, 1i64) else d
-- 1 January, and the Monday after it when it falls on a weekend.
def new_year_with_additional_day(year: i64) -> List[Date] = {
  first = date(year, 1i64, 1i64)
  [first, weekend_forward_to_monday(first)]
}
-- 25 and 26 December, with the weekday substitutes England and Wales and New South
-- Wales both use: a weekend Christmas Day or Boxing Day moves to the next weekday
-- that is not already one of the two holidays.
def christmas_and_boxing_with_additional_days(year: i64) -> List[Date] = {
  christmas = date(year, 12i64, 25i64)
  boxing = date(year, 12i64, 26i64)
  if is_saturday(christmas) then [christmas, boxing, date(year, 12i64, 27i64), date(year, 12i64, 28i64)] else if is_sunday(christmas) then [christmas, boxing, date(year, 12i64, 27i64)] else if is_saturday(boxing) then [christmas, boxing, date(year, 12i64, 28i64)] else [christmas, boxing]
}
def contains_day(days: List[Date], d: Date) -> bool = fold(fn (acc: bool, x: Date) -> or(acc, eq(date_epoch_day(x), date_epoch_day(d))), false, days)
def days_in_year(days: List[Date], year: i64) -> List[Date] = filter(fn (d: Date) -> eq(date_year(d), year), days)
def joined(parts: List[string]) -> string = fold(fn (acc: string, part: string) -> string_concat(acc, part), "", parts)
-- `or` evaluates both arguments, so the year comparison guards the `date` call
-- by nesting instead: `date` fails for a year outside its range.
def not_extending(published_until: Date, until_year: i64) -> string = joined(["until_year ", to_string(until_year), " does not extend the published horizon, which ends in ", to_string(date_year(published_until)), "; use the published calendar"])
-- Why `until_year` cannot extend a calendar, or "" when it can: the projection
-- must end after the published horizon and within the years the rules hold for.
def projection_problem(published_until: Date, until_year: i64, max_year: i64) -> string = if gt(until_year, max_year) then joined(["until_year ", to_string(until_year), " is after ", to_string(max_year), ", the last year its rules are stated for"]) else if lt(until_year, date_year(published_until)) then not_extending(published_until, until_year) else if lte(date_epoch_day(date(until_year, 12i64, 31i64)), date_epoch_day(published_until)) then not_extending(published_until, until_year) else ""
-- The rule-generated holidays after the published horizon and up to the end of
-- `until_year`. Each year's rules may observe a holiday in the year before (a
-- Saturday 1 January observed on 31 December), so the year after `until_year` is
-- generated too when the rules hold for it.
def projected_days(published_until: Date, rule: i64 -> List[Date], until_year: i64, max_year: i64) -> List[Date] = {
  first_year = date_year(published_until)
  last_rule_year = if lt(until_year, max_year) then add(until_year, 1i64) else until_year
  generated = flat_map(rule, range(first_year, add(last_rule_year, 1i64)))
  start = date_epoch_day(published_until)
  stop = date_epoch_day(date(until_year, 12i64, 31i64))
  filter(fn (d: Date) -> and(gt(date_epoch_day(d), start), lte(date_epoch_day(d), stop)), generated)
}
def projected_calendar(name: string, weekmask: Weekmask, published: List[Date], published_from: Date, published_until: Date, rule: i64 -> List[Date], until_year: i64, max_year: i64) -> BusinessCalendar = {
  problem = projection_problem(published_until, until_year, max_year)
  if eq(problem, "") then business_calendar(weekmask, flatten([published, projected_days(published_until, rule, until_year, max_year)]), published_from, date(until_year, 12i64, 31i64)) else fail(joined([name, ": domain: ", problem]))
}
def try_projected_calendar(weekmask: Weekmask, published: List[Date], published_from: Date, published_until: Date, rule: i64 -> List[Date], until_year: i64, max_year: i64) -> Option[BusinessCalendar] = if eq(projection_problem(published_until, until_year, max_year), "") then try_business_calendar(weekmask, flatten([published, projected_days(published_until, rule, until_year, max_year)]), published_from, date(until_year, 12i64, 31i64)) else None

module Tides.JapanBank
import Std.Datetime (Date, Monday, date, date_add_days)
import Std.Datetime.Business (Weekmask, BusinessCalendar, business_calendar)
import Tides.Rules (projected_calendar, try_projected_calendar, monday_to_friday, nth_weekday, is_sunday, contains_day)
import Tides.Published.JapanBank (japan_bank_published_holidays, japan_bank_published_from, japan_bank_published_until, japan_bank_published_source, japan_bank_published_source_urls, japan_bank_published_retrieved, japan_bank_published_sha256s)
export (japan_bank, japan_bank_projected, try_japan_bank_projected, japan_bank_rule_holidays, japan_bank_weekmask, japan_bank_projection_last_year, japan_bank_source, japan_bank_source_urls, japan_bank_retrieved, japan_bank_snapshot_sha256s, japan_vernal_equinox_day, japan_autumnal_equinox_day, japan_national_holidays)
-- Japanese bank holidays on a Monday to Friday week: the national holidays the
-- Cabinet Office publishes, with their substitute and citizen's holidays, plus the
-- bank closures of 31 December and 2 and 3 January (Banking Act Enforcement Order,
-- article 5). Banks have closed every Saturday since February 1989, so the
-- calendar starts on 1 January 1990.
--
-- The projection states the Act on National Holidays as it stands from 2020: the
-- sixteen national holidays; a substitute holiday on the first following day that
-- is not a national holiday when one falls on a Sunday; and a citizen's holiday on
-- a day between two national holidays. The Cabinet Office fixes each equinox day
-- every February for the next year from the National Astronomical Observatory's
-- ephemeris; the projection predicts it with the standard formula, which matches
-- every published equinox day from 1990 and is stated for 1980 to 2099, so a
-- projection ends by 2099. A projection omits holidays made for one year (the 2019
-- enthronement days), one-year moves by statute (the 2020 and 2021 Olympic moves),
-- and any later change to the Act.
def japan_bank_weekmask() -> Weekmask = monday_to_friday()
-- The published calendar: horizon japan_bank_published_from() to japan_bank_published_until().
def japan_bank() -> BusinessCalendar = business_calendar(japan_bank_weekmask(), japan_bank_published_holidays(), japan_bank_published_from(), japan_bank_published_until())
-- The March day of the vernal equinox holiday, for 1980 to 2099.
def japan_vernal_equinox_day(year: i64) -> i64 = sub(floor_div(add(20843100i64, mul(242194i64, sub(year, 1980i64))), 1000000i64), floor_div(sub(year, 1980i64), 4i64))
-- The September day of the autumnal equinox holiday, for 1980 to 2099.
def japan_autumnal_equinox_day(year: i64) -> i64 = sub(floor_div(add(23248800i64, mul(242194i64, sub(year, 1980i64))), 1000000i64), floor_div(sub(year, 1980i64), 4i64))
-- The sixteen national holidays of the Act as it stands from 2020.
def japan_national_holidays(year: i64) -> List[Date] = [date(year, 1i64, 1i64), nth_weekday(year, 1i64, Monday, 2i64), date(year, 2i64, 11i64), date(year, 2i64, 23i64), date(year, 3i64, japan_vernal_equinox_day(year)), date(year, 4i64, 29i64), date(year, 5i64, 3i64), date(year, 5i64, 4i64), date(year, 5i64, 5i64), nth_weekday(year, 7i64, Monday, 3i64), date(year, 8i64, 11i64), nth_weekday(year, 9i64, Monday, 3i64), date(year, 9i64, japan_autumnal_equinox_day(year)), nth_weekday(year, 10i64, Monday, 2i64), date(year, 11i64, 3i64), date(year, 11i64, 23i64)]
-- The substitute for a Sunday national holiday: the first following day that is
-- not itself a national holiday. Three national holidays in a row (3 to 5 May) is
-- the longest run, so the third following day always qualifies.
def substitute_holiday(national: List[Date], h: Date) -> List[Date] = if is_sunday(h) then if not(contains_day(national, date_add_days(h, 1i64))) then [date_add_days(h, 1i64)] else if not(contains_day(national, date_add_days(h, 2i64))) then [date_add_days(h, 2i64)] else [date_add_days(h, 3i64)] else []
-- A citizen's holiday: a day that is not a national holiday between two that are.
def citizens_holiday(national: List[Date], h: Date) -> List[Date] = if and(contains_day(national, date_add_days(h, 2i64)), not(contains_day(national, date_add_days(h, 1i64)))) then [date_add_days(h, 1i64)] else []
-- The holidays the rules give for one year.
def japan_bank_rule_holidays(year: i64) -> List[Date] = {
  national = japan_national_holidays(year)
  flatten([national, flat_map(fn (h: Date) -> substitute_holiday(national, h), national), flat_map(fn (h: Date) -> citizens_holiday(national, h), national), [date(year, 1i64, 2i64), date(year, 1i64, 3i64), date(year, 12i64, 31i64)]])
}
-- The last year a projection may reach: the last year of the equinox formula.
def japan_bank_projection_last_year() -> i64 = 2099i64
-- The published calendar extended by the rules through the end of `until_year`.
-- Fails `domain` when `until_year` does not pass the published horizon or is after
-- japan_bank_projection_last_year().
def japan_bank_projected(until_year: i64) -> BusinessCalendar = projected_calendar("japan_bank_projected", japan_bank_weekmask(), japan_bank_published_holidays(), japan_bank_published_from(), japan_bank_published_until(), japan_bank_rule_holidays, until_year, japan_bank_projection_last_year())
def try_japan_bank_projected(until_year: i64) -> Option[BusinessCalendar] = try_projected_calendar(japan_bank_weekmask(), japan_bank_published_holidays(), japan_bank_published_from(), japan_bank_published_until(), japan_bank_rule_holidays, until_year, japan_bank_projection_last_year())
def japan_bank_source() -> string = japan_bank_published_source()
def japan_bank_source_urls() -> List[string] = japan_bank_published_source_urls()
def japan_bank_retrieved() -> Date = japan_bank_published_retrieved()
def japan_bank_snapshot_sha256s() -> List[string] = japan_bank_published_sha256s()

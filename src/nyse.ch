module BedHolidays.Nyse
import Std.Datetime (Date, Monday, Thursday, date)
import Std.Datetime.Business (Weekmask, BusinessCalendar, business_calendar)
import BedHolidays.Rules (projected_calendar, try_projected_calendar, monday_to_friday, saturday_back_sunday_forward, sunday_forward_to_monday, is_saturday, nth_weekday, last_weekday, good_friday)
import BedHolidays.Published.Nyse (nyse_published_holidays, nyse_published_from, nyse_published_until, nyse_published_source, nyse_published_source_url, nyse_published_retrieved, nyse_published_sha256)
export (nyse, nyse_projected, try_nyse_projected, nyse_rule_holidays, nyse_weekmask, nyse_projection_last_year, nyse_source, nyse_source_url, nyse_retrieved, nyse_snapshot_sha256)
-- New York Stock Exchange full-day closures, as nyse.com publishes them, on a
-- Monday to Friday week. Early closes are trading days. Under NYSE Rule 7.2 a
-- Saturday holiday closes the Friday before it unless that Friday ends a monthly or
-- yearly accounting period, so a Saturday 1 January closes no day; a Sunday holiday
-- closes the Monday after it. Juneteenth closes the market from 2022. A projection
-- omits every closure the exchange announces for one day, such as a national day of
-- mourning (9 January 2025) or an emergency closure.
def nyse_weekmask() -> Weekmask = monday_to_friday()
-- The published calendar: horizon nyse_published_from() to nyse_published_until().
def nyse() -> BusinessCalendar = business_calendar(nyse_weekmask(), nyse_published_holidays(), nyse_published_from(), nyse_published_until())
-- The holidays the rules give for one year, including any observed in the year before.
def nyse_rule_holidays(year: i64) -> List[Date] = flatten([if is_saturday(date(year, 1i64, 1i64)) then [] else [sunday_forward_to_monday(date(year, 1i64, 1i64))], [nth_weekday(year, 1i64, Monday, 3i64), nth_weekday(year, 2i64, Monday, 3i64), good_friday(year), last_weekday(year, 5i64, Monday), saturday_back_sunday_forward(date(year, 7i64, 4i64)), nth_weekday(year, 9i64, Monday, 1i64), nth_weekday(year, 11i64, Thursday, 4i64), saturday_back_sunday_forward(date(year, 12i64, 25i64))], if gte(year, 2022i64) then [saturday_back_sunday_forward(date(year, 6i64, 19i64))] else []])
-- The last year a projection may reach.
def nyse_projection_last_year() -> i64 = 9998i64
-- The published calendar extended by the rules through the end of `until_year`.
-- Fails `domain` when `until_year` does not pass the published horizon or is after
-- nyse_projection_last_year().
def nyse_projected(until_year: i64) -> BusinessCalendar = projected_calendar("nyse_projected", nyse_weekmask(), nyse_published_holidays(), nyse_published_from(), nyse_published_until(), nyse_rule_holidays, until_year, nyse_projection_last_year())
def try_nyse_projected(until_year: i64) -> Option[BusinessCalendar] = try_projected_calendar(nyse_weekmask(), nyse_published_holidays(), nyse_published_from(), nyse_published_until(), nyse_rule_holidays, until_year, nyse_projection_last_year())
def nyse_source() -> string = nyse_published_source()
def nyse_source_url() -> string = nyse_published_source_url()
def nyse_retrieved() -> Date = nyse_published_retrieved()
def nyse_snapshot_sha256() -> string = nyse_published_sha256()

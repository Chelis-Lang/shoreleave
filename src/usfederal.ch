module BedHolidays.UsFederal
import Std.Datetime (Date, Monday, Thursday, date)
import Std.Datetime.Business (Weekmask, BusinessCalendar, business_calendar)
import BedHolidays.Rules (projected_calendar, try_projected_calendar, monday_to_friday, saturday_back_sunday_forward, nth_weekday, last_weekday)
import BedHolidays.Published.UsFederal (us_federal_published_holidays, us_federal_published_from, us_federal_published_until, us_federal_published_source, us_federal_published_source_url, us_federal_published_retrieved, us_federal_published_sha256)
export (us_federal, us_federal_projected, try_us_federal_projected, us_federal_rule_holidays, us_federal_weekmask, us_federal_projection_last_year, us_federal_source, us_federal_source_url, us_federal_retrieved, us_federal_snapshot_sha256)
-- US federal legal public holidays (5 U.S.C. 6103(a)) on the days OPM lists them
-- as observed for most federal employees, on a Monday to Friday week. A Saturday
-- holiday is observed on the Friday before it and a Sunday holiday on the Monday
-- after it, so a Saturday 1 January is observed on 31 December of the year before.
-- Juneteenth is a legal public holiday from 2021. Inauguration Day, a holiday only
-- in the Washington, DC area, is left out. Neither the published calendar nor a
-- projection has closures ordered by executive order, which OPM announces
-- separately (for example 24 December 2024 and the national day of mourning of
-- 9 January 2025).
def us_federal_weekmask() -> Weekmask = monday_to_friday()
-- The published calendar: horizon us_federal_published_from() to us_federal_published_until().
def us_federal() -> BusinessCalendar = business_calendar(us_federal_weekmask(), us_federal_published_holidays(), us_federal_published_from(), us_federal_published_until())
-- The holidays the rules give for one year, including any observed in the year before.
def us_federal_rule_holidays(year: i64) -> List[Date] = flatten([[saturday_back_sunday_forward(date(year, 1i64, 1i64)), nth_weekday(year, 1i64, Monday, 3i64), nth_weekday(year, 2i64, Monday, 3i64), last_weekday(year, 5i64, Monday), saturday_back_sunday_forward(date(year, 7i64, 4i64)), nth_weekday(year, 9i64, Monday, 1i64), nth_weekday(year, 10i64, Monday, 2i64), saturday_back_sunday_forward(date(year, 11i64, 11i64)), nth_weekday(year, 11i64, Thursday, 4i64), saturday_back_sunday_forward(date(year, 12i64, 25i64))], if gte(year, 2021i64) then [saturday_back_sunday_forward(date(year, 6i64, 19i64))] else []])
-- The last year a projection may reach.
def us_federal_projection_last_year() -> i64 = 9998i64
-- The published calendar extended by the rules through the end of `until_year`.
-- Fails `domain` when `until_year` does not pass the published horizon or is after
-- us_federal_projection_last_year().
def us_federal_projected(until_year: i64) -> BusinessCalendar = projected_calendar("us_federal_projected", us_federal_weekmask(), us_federal_published_holidays(), us_federal_published_from(), us_federal_published_until(), us_federal_rule_holidays, until_year, us_federal_projection_last_year())
def try_us_federal_projected(until_year: i64) -> Option[BusinessCalendar] = try_projected_calendar(us_federal_weekmask(), us_federal_published_holidays(), us_federal_published_from(), us_federal_published_until(), us_federal_rule_holidays, until_year, us_federal_projection_last_year())
def us_federal_source() -> string = us_federal_published_source()
def us_federal_source_url() -> string = us_federal_published_source_url()
def us_federal_retrieved() -> Date = us_federal_published_retrieved()
def us_federal_snapshot_sha256() -> string = us_federal_published_sha256()

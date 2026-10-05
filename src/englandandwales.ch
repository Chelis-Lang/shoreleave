module BedHolidays.EnglandAndWales
import Std.Datetime (Date, Monday)
import Std.Datetime.Business (Weekmask, BusinessCalendar, business_calendar)
import BedHolidays.Rules (projected_calendar, try_projected_calendar, monday_to_friday, new_year_with_additional_day, good_friday, easter_monday, nth_weekday, last_weekday, christmas_and_boxing_with_additional_days)
import BedHolidays.Published.EnglandAndWales (england_and_wales_published_holidays, england_and_wales_published_from, england_and_wales_published_until, england_and_wales_published_source, england_and_wales_published_source_url, england_and_wales_published_retrieved, england_and_wales_published_sha256)
export (england_and_wales, england_and_wales_projected, try_england_and_wales_projected, england_and_wales_rule_holidays, england_and_wales_weekmask, england_and_wales_projection_last_year, england_and_wales_source, england_and_wales_source_url, england_and_wales_retrieved, england_and_wales_snapshot_sha256)
-- England and Wales bank holidays, as gov.uk publishes them, on a Monday to Friday
-- week. The projection's rules are those of the Banking and Financial Dealings Act
-- 1971 and the annual royal proclamations: 1 January, Good Friday, Easter Monday,
-- the first and last Mondays of May, the last Monday of August, and 25 and 26
-- December, each weekend one with its substitute weekday. A projection omits every
-- holiday proclaimed for one year (the 2022 State Funeral and Platinum Jubilee, the
-- 2023 Coronation) and every proclaimed move of a rule holiday (the early May bank
-- holiday of 2020, the spring bank holiday of 2022).
def england_and_wales_weekmask() -> Weekmask = monday_to_friday()
-- The published calendar: horizon england_and_wales_published_from() to england_and_wales_published_until().
def england_and_wales() -> BusinessCalendar = business_calendar(england_and_wales_weekmask(), england_and_wales_published_holidays(), england_and_wales_published_from(), england_and_wales_published_until())
-- The holidays the rules give for one year, including any observed in the year before.
def england_and_wales_rule_holidays(year: i64) -> List[Date] = flatten([new_year_with_additional_day(year), [good_friday(year), easter_monday(year), nth_weekday(year, 5i64, Monday, 1i64), last_weekday(year, 5i64, Monday), last_weekday(year, 8i64, Monday)], christmas_and_boxing_with_additional_days(year)])
-- The last year a projection may reach.
def england_and_wales_projection_last_year() -> i64 = 9998i64
-- The published calendar extended by the rules through the end of `until_year`.
-- Fails `domain` when `until_year` does not pass the published horizon or is after
-- england_and_wales_projection_last_year().
def england_and_wales_projected(until_year: i64) -> BusinessCalendar = projected_calendar("england_and_wales_projected", england_and_wales_weekmask(), england_and_wales_published_holidays(), england_and_wales_published_from(), england_and_wales_published_until(), england_and_wales_rule_holidays, until_year, england_and_wales_projection_last_year())
def try_england_and_wales_projected(until_year: i64) -> Option[BusinessCalendar] = try_projected_calendar(england_and_wales_weekmask(), england_and_wales_published_holidays(), england_and_wales_published_from(), england_and_wales_published_until(), england_and_wales_rule_holidays, until_year, england_and_wales_projection_last_year())
def england_and_wales_source() -> string = england_and_wales_published_source()
def england_and_wales_source_url() -> string = england_and_wales_published_source_url()
def england_and_wales_retrieved() -> Date = england_and_wales_published_retrieved()
def england_and_wales_snapshot_sha256() -> string = england_and_wales_published_sha256()

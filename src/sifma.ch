module Tides.Sifma
import Std.Datetime (Date, Monday, Thursday, date)
import Std.Datetime.Business (Weekmask, BusinessCalendar, business_calendar)
import Tides.Rules (projected_calendar, try_projected_calendar, monday_to_friday, saturday_back_sunday_forward, sunday_forward_to_monday, is_saturday, is_weekend, nth_weekday, last_weekday)
import Tides.Published.Sifma (sifma_published_holidays, sifma_published_from, sifma_published_until, sifma_published_source, sifma_published_source_urls, sifma_published_retrieved, sifma_published_sha256s)
export (sifma, sifma_projected, try_sifma_projected, sifma_rule_holidays, sifma_weekmask, sifma_projection_last_year, sifma_source, sifma_source_urls, sifma_retrieved, sifma_snapshot_sha256s)
-- The full-day closes SIFMA recommends for the US bond market, on a Monday to
-- Friday week. Early closes are trading days. SIFMA decides each year whether Good
-- Friday is a full close or only an early close, so a projection omits Good Friday.
-- A projection also omits Veterans Day when it falls on a weekend, whose
-- observance SIFMA likewise decides each year, and every one-day closure SIFMA
-- recommends after an announcement. A Saturday 1 January closes no day.
def sifma_weekmask() -> Weekmask = monday_to_friday()
-- The published calendar: horizon sifma_published_from() to sifma_published_until().
def sifma() -> BusinessCalendar = business_calendar(sifma_weekmask(), sifma_published_holidays(), sifma_published_from(), sifma_published_until())
-- The holidays the rules give for one year, including any observed in the year before.
def sifma_rule_holidays(year: i64) -> List[Date] = flatten([if is_saturday(date(year, 1i64, 1i64)) then [] else [sunday_forward_to_monday(date(year, 1i64, 1i64))], [nth_weekday(year, 1i64, Monday, 3i64), nth_weekday(year, 2i64, Monday, 3i64), last_weekday(year, 5i64, Monday), saturday_back_sunday_forward(date(year, 7i64, 4i64)), nth_weekday(year, 9i64, Monday, 1i64), nth_weekday(year, 10i64, Monday, 2i64), nth_weekday(year, 11i64, Thursday, 4i64), saturday_back_sunday_forward(date(year, 12i64, 25i64))], if gte(year, 2022i64) then [saturday_back_sunday_forward(date(year, 6i64, 19i64))] else [], if is_weekend(date(year, 11i64, 11i64)) then [] else [date(year, 11i64, 11i64)]])
-- The last year a projection may reach.
def sifma_projection_last_year() -> i64 = 9998i64
-- The published calendar extended by the rules through the end of `until_year`.
-- Fails `domain` when `until_year` does not pass the published horizon or is after
-- sifma_projection_last_year().
def sifma_projected(until_year: i64) -> BusinessCalendar = projected_calendar("sifma_projected", sifma_weekmask(), sifma_published_holidays(), sifma_published_from(), sifma_published_until(), sifma_rule_holidays, until_year, sifma_projection_last_year())
def try_sifma_projected(until_year: i64) -> Option[BusinessCalendar] = try_projected_calendar(sifma_weekmask(), sifma_published_holidays(), sifma_published_from(), sifma_published_until(), sifma_rule_holidays, until_year, sifma_projection_last_year())
def sifma_source() -> string = sifma_published_source()
def sifma_source_urls() -> List[string] = sifma_published_source_urls()
def sifma_retrieved() -> Date = sifma_published_retrieved()
def sifma_snapshot_sha256s() -> List[string] = sifma_published_sha256s()

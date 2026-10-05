module Tides.HongKong
import Std.Datetime (Date, date)
import Std.Datetime.Business (Weekmask, BusinessCalendar, business_calendar)
import Tides.Rules (projected_calendar, try_projected_calendar, monday_to_saturday, sunday_forward_to_monday, is_saturday, is_sunday, good_friday, easter_saturday, easter_monday)
import Tides.Published.HongKong (hong_kong_published_holidays, hong_kong_published_from, hong_kong_published_until, hong_kong_published_source, hong_kong_published_source_urls, hong_kong_published_retrieved, hong_kong_published_sha256s)
export (hong_kong, hong_kong_projected, try_hong_kong_projected, hong_kong_rule_holidays, hong_kong_weekmask, hong_kong_projection_last_year, hong_kong_source, hong_kong_source_urls, hong_kong_retrieved, hong_kong_snapshot_sha256s)
-- Hong Kong general holidays, as the 1823 government feed publishes them, on a
-- Monday to Saturday week: every Sunday is a general holiday, and Saturday is not
-- (General Holidays Ordinance, Cap. 149). Combine with a Monday to Friday calendar
-- through `business_in_all` for a five-day banking week. The projection's rules
-- cover the holidays fixed in the Gregorian calendar: 1 January, Good Friday and
-- the day after it, Easter Monday, 1 May, 1 July, 1 October, 25 December and the
-- first weekday after it, a Sunday one moving to the Monday after it. A projection
-- omits every lunar or solar-term holiday, which has no Gregorian rule: Lunar New
-- Year's three days and the fourth day that replaces one falling on a Sunday, Ching
-- Ming, the Buddha's Birthday, Tuen Ng, the day after Mid-Autumn and Chung Yeung. It
-- also omits the moves those holidays force on a rule holiday (in 2026 Easter
-- Monday moved to 7 April because the day after Ching Ming took 6 April) and every
-- additional general holiday announced for one year.
def hong_kong_weekmask() -> Weekmask = monday_to_saturday()
-- The published calendar: horizon hong_kong_published_from() to hong_kong_published_until().
def hong_kong() -> BusinessCalendar = business_calendar(hong_kong_weekmask(), hong_kong_published_holidays(), hong_kong_published_from(), hong_kong_published_until())
-- The holidays the rules give for one year, including any observed in the year before.
def hong_kong_rule_holidays(year: i64) -> List[Date] = flatten([[sunday_forward_to_monday(date(year, 1i64, 1i64)), good_friday(year), easter_saturday(year), easter_monday(year), sunday_forward_to_monday(date(year, 5i64, 1i64)), sunday_forward_to_monday(date(year, 7i64, 1i64)), sunday_forward_to_monday(date(year, 10i64, 1i64)), date(year, 12i64, 25i64)], if is_sunday(date(year, 12i64, 25i64)) then [date(year, 12i64, 26i64), date(year, 12i64, 27i64)] else if is_saturday(date(year, 12i64, 25i64)) then [date(year, 12i64, 27i64)] else [date(year, 12i64, 26i64)]])
-- The last year a projection may reach.
def hong_kong_projection_last_year() -> i64 = 9998i64
-- The published calendar extended by the rules through the end of `until_year`.
-- Fails `domain` when `until_year` does not pass the published horizon or is after
-- hong_kong_projection_last_year().
def hong_kong_projected(until_year: i64) -> BusinessCalendar = projected_calendar("hong_kong_projected", hong_kong_weekmask(), hong_kong_published_holidays(), hong_kong_published_from(), hong_kong_published_until(), hong_kong_rule_holidays, until_year, hong_kong_projection_last_year())
def try_hong_kong_projected(until_year: i64) -> Option[BusinessCalendar] = try_projected_calendar(hong_kong_weekmask(), hong_kong_published_holidays(), hong_kong_published_from(), hong_kong_published_until(), hong_kong_rule_holidays, until_year, hong_kong_projection_last_year())
def hong_kong_source() -> string = hong_kong_published_source()
def hong_kong_source_urls() -> List[string] = hong_kong_published_source_urls()
def hong_kong_retrieved() -> Date = hong_kong_published_retrieved()
def hong_kong_snapshot_sha256s() -> List[string] = hong_kong_published_sha256s()

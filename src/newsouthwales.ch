module Tides.NewSouthWales
import Std.Datetime (Date, Monday, date, easter_sunday_gregorian)
import Std.Datetime.Business (Weekmask, BusinessCalendar, business_calendar)
import Tides.Rules (projected_calendar, try_projected_calendar, monday_to_friday, new_year_with_additional_day, weekend_forward_to_monday, good_friday, easter_saturday, easter_monday, nth_weekday, christmas_and_boxing_with_additional_days)
import Tides.Published.NewSouthWales (new_south_wales_published_holidays, new_south_wales_published_from, new_south_wales_published_until, new_south_wales_published_source, new_south_wales_published_source_urls, new_south_wales_published_retrieved, new_south_wales_published_sha256s)
export (new_south_wales, new_south_wales_projected, try_new_south_wales_projected, new_south_wales_rule_holidays, new_south_wales_weekmask, new_south_wales_projection_last_year, new_south_wales_source, new_south_wales_source_urls, new_south_wales_retrieved, new_south_wales_snapshot_sha256s)
-- New South Wales public holidays on a Monday to Friday week. The standard holidays
-- are those of the Public Holidays Act 2010, section 4: 1 January, Australia Day,
-- Good Friday, Easter Saturday, Easter Sunday, Easter Monday, Anzac Day, the King's
-- Birthday (the second Monday of June), Labour Day (the first Monday of October),
-- and 25 and 26 December. A weekend 1 January gains an additional Monday; a weekend
-- Australia Day moves to the Monday; a weekend 25 or 26 December gains an
-- additional weekday, so a Saturday Christmas and Sunday Boxing Day give Monday 27
-- and Tuesday 28 December. Days the Minister declares by order (section 5), such
-- as the additional days for a weekend Anzac Day in 2026 and 2027, come only from
-- the published table, never from a rule. The August Bank Holiday is not a public
-- holiday and is left out. A projection omits every declared day.
def new_south_wales_weekmask() -> Weekmask = monday_to_friday()
-- The published calendar: horizon new_south_wales_published_from() to new_south_wales_published_until().
def new_south_wales() -> BusinessCalendar = business_calendar(new_south_wales_weekmask(), new_south_wales_published_holidays(), new_south_wales_published_from(), new_south_wales_published_until())
-- The holidays the rules give for one year, including any observed in the year before.
def new_south_wales_rule_holidays(year: i64) -> List[Date] = flatten([new_year_with_additional_day(year), [weekend_forward_to_monday(date(year, 1i64, 26i64)), good_friday(year), easter_saturday(year), easter_sunday_gregorian(year), easter_monday(year), date(year, 4i64, 25i64), nth_weekday(year, 6i64, Monday, 2i64), nth_weekday(year, 10i64, Monday, 1i64)], christmas_and_boxing_with_additional_days(year)])
-- The last year a projection may reach.
def new_south_wales_projection_last_year() -> i64 = 9998i64
-- The published calendar extended by the rules through the end of `until_year`.
-- Fails `domain` when `until_year` does not pass the published horizon or is after
-- new_south_wales_projection_last_year().
def new_south_wales_projected(until_year: i64) -> BusinessCalendar = projected_calendar("new_south_wales_projected", new_south_wales_weekmask(), new_south_wales_published_holidays(), new_south_wales_published_from(), new_south_wales_published_until(), new_south_wales_rule_holidays, until_year, new_south_wales_projection_last_year())
def try_new_south_wales_projected(until_year: i64) -> Option[BusinessCalendar] = try_projected_calendar(new_south_wales_weekmask(), new_south_wales_published_holidays(), new_south_wales_published_from(), new_south_wales_published_until(), new_south_wales_rule_holidays, until_year, new_south_wales_projection_last_year())
def new_south_wales_source() -> string = new_south_wales_published_source()
def new_south_wales_source_urls() -> List[string] = new_south_wales_published_source_urls()
def new_south_wales_retrieved() -> Date = new_south_wales_published_retrieved()
def new_south_wales_snapshot_sha256s() -> List[string] = new_south_wales_published_sha256s()

module Shoreleave.Target
import Std.Datetime (Date, date)
import Std.Datetime.Business (Weekmask, BusinessCalendar, business_calendar)
import Shoreleave.Rules (projected_calendar, try_projected_calendar, monday_to_friday, good_friday, easter_monday)
import Shoreleave.Published.Target (target_published_holidays, target_published_from, target_published_until, target_published_source, target_published_source_urls, target_published_retrieved, target_published_sha256s)
export (target, target_projected, try_target_projected, target_rule_holidays, target_weekmask, target_projection_last_year, target_source, target_source_urls, target_retrieved, target_snapshot_sha256s)
-- TARGET closing days on a Monday to Friday week: 1 January, Good Friday, Easter
-- Monday, 1 May, 25 December and 26 December (Governing Council decision of
-- 14 December 2000, Guideline (EU) 2022/912). The published calendar is this rule
-- over the years the ECB's public-holidays page covers; generation fails unless the
-- days the page marks as TARGET closing days are exactly the rule's. The page's
-- other rows are ECB office holidays, which TARGET does not observe. No closing day
-- is announced, so a projection omits nothing the rules can state.
def target_weekmask() -> Weekmask = monday_to_friday()
-- The published calendar: horizon target_published_from() to target_published_until().
def target() -> BusinessCalendar = business_calendar(target_weekmask(), target_published_holidays(), target_published_from(), target_published_until())
-- The holidays the rules give for one year, including any observed in the year before.
def target_rule_holidays(year: i64) -> List[Date] = [date(year, 1i64, 1i64), good_friday(year), easter_monday(year), date(year, 5i64, 1i64), date(year, 12i64, 25i64), date(year, 12i64, 26i64)]
-- The last year a projection may reach.
def target_projection_last_year() -> i64 = 9998i64
-- The published calendar extended by the rules through the end of `until_year`.
-- Fails `domain` when `until_year` does not pass the published horizon or is after
-- target_projection_last_year().
def target_projected(until_year: i64) -> BusinessCalendar = projected_calendar("target_projected", target_weekmask(), target_published_holidays(), target_published_from(), target_published_until(), target_rule_holidays, until_year, target_projection_last_year())
def try_target_projected(until_year: i64) -> Option[BusinessCalendar] = try_projected_calendar(target_weekmask(), target_published_holidays(), target_published_from(), target_published_until(), target_rule_holidays, until_year, target_projection_last_year())
def target_source() -> string = target_published_source()
def target_source_urls() -> List[string] = target_published_source_urls()
def target_retrieved() -> Date = target_published_retrieved()
def target_snapshot_sha256s() -> List[string] = target_published_sha256s()

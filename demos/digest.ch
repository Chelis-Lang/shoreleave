module Tides.Demos.Digest
import Std.Datetime (Date, date, date_add_days, date_to_string)
import Std.Datetime.Business (BusinessCalendar, ModifiedFollowing, RollStartForward, try_is_business_day, business_calendar_holidays, business_calendar_valid_from, business_calendar_valid_until, business_day_count, business_day_offset, business_day_roll)
import Tides.Rules (joined)
import Tides.EnglandAndWales (england_and_wales, england_and_wales_projected, try_england_and_wales_projected)
import Tides.UsFederal (us_federal, us_federal_projected)
import Tides.JapanBank (japan_bank, japan_bank_projected, try_japan_bank_projected)
import Tides.NewSouthWales (new_south_wales, new_south_wales_projected)
import Tides.HongKong (hong_kong, hong_kong_projected)
import Tides.Nyse (nyse, nyse_projected)
import Tides.Sifma (sifma, sifma_projected)
import Tides.Target (target, target_projected)
import Tides.Provenance (tides_version)
-- One line per calendar: its horizon, holiday count, business days over the whole
-- horizon, the 100th business day after its first day, and a modified-following
-- roll of the last 25 December it covers. `chelis eval --file` and the executable
-- `chelis build` makes print the same lines.
def digest(name: string, cal: BusinessCalendar) -> string = {
  first = business_calendar_valid_from(cal)
  last = business_calendar_valid_until(cal)
  joined([name, " ", date_to_string(first), "..", date_to_string(last), " holidays=", to_string(len(business_calendar_holidays(cal))), " business_days=", to_string(business_day_count(cal, first, date_add_days(last, 1i64))), " day100=", date_to_string(business_day_offset(cal, first, 100i64, RollStartForward)), " christmas_roll=", date_to_string(business_day_roll(cal, date_add_days(last, -6i64), ModifiedFollowing))])
}
version = tides_version()
england_and_wales_digest = digest("england_and_wales", england_and_wales())
england_and_wales_projected_digest = digest("england_and_wales_projected", england_and_wales_projected(2040i64))
us_federal_digest = digest("us_federal", us_federal())
us_federal_projected_digest = digest("us_federal_projected", us_federal_projected(2040i64))
japan_bank_digest = digest("japan_bank", japan_bank())
japan_bank_projected_digest = digest("japan_bank_projected", japan_bank_projected(2040i64))
new_south_wales_digest = digest("new_south_wales", new_south_wales())
new_south_wales_projected_digest = digest("new_south_wales_projected", new_south_wales_projected(2040i64))
hong_kong_digest = digest("hong_kong", hong_kong())
hong_kong_projected_digest = digest("hong_kong_projected", hong_kong_projected(2040i64))
nyse_digest = digest("nyse", nyse())
nyse_projected_digest = digest("nyse_projected", nyse_projected(2040i64))
sifma_digest = digest("sifma", sifma())
sifma_projected_digest = digest("sifma_projected", sifma_projected(2040i64))
target_digest = digest("target", target())
target_projected_digest = digest("target_projected", target_projected(2040i64))
-- Outside the horizon there is no answer, in either lane.
outside_horizon = match try_is_business_day(england_and_wales(), date(2029i64, 1i64, 2i64)) with {
  | Some(open) => if open then "open" else "closed"
  | None => "none"
}
inside_horizon = match try_is_business_day(england_and_wales(), date(2028i64, 12i64, 26i64)) with {
  | Some(open) => if open then "open" else "closed"
  | None => "none"
}
projection_inside_published = match try_england_and_wales_projected(2028i64) with {
  | Some(cal) => "some"
  | None => "none"
}
projection_after_formula = match try_japan_bank_projected(2100i64) with {
  | Some(cal) => "some"
  | None => "none"
}

module Shoreleave.TestsNeg.Horizon.OffsetPastNyse
import Std.Datetime (date, date_to_string)
import Std.Datetime.Business (business_day_offset, RejectNonBusinessStart)
import Shoreleave.Nyse (nyse)
def test_neg_offset_past_the_horizon() -> unit = test_assert(eq(date_to_string(business_day_offset(nyse(), date(2028i64, 12i64, 29i64), 1i64, RejectNonBusinessStart)), ""), "unreachable")

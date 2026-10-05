module BedHolidays.TestsNeg.Horizon.AfterHongKong
import Std.Datetime (date)
import Std.Datetime.Business (is_business_day)
import BedHolidays.HongKong (hong_kong)
def test_neg_query_after_the_horizon() -> unit = test_assert(is_business_day(hong_kong(), date(2028i64, 1i64, 1i64)), "unreachable")

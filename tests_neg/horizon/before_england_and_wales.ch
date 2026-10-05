module BedHolidays.TestsNeg.Horizon.BeforeEnglandAndWales
import Std.Datetime (date)
import Std.Datetime.Business (is_business_day)
import BedHolidays.EnglandAndWales (england_and_wales)
def test_neg_query_before_the_horizon() -> unit = test_assert(is_business_day(england_and_wales(), date(2018i64, 12i64, 31i64)), "unreachable")

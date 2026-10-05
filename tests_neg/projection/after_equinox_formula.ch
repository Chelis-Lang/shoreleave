module BedHolidays.TestsNeg.Projection.AfterEquinoxFormula
import Std.Datetime.Business (business_calendar_valid_until)
import BedHolidays.JapanBank (japan_bank_projected)
def test_neg_projection_after_the_equinox_formula() -> unit = test_assert(eq(business_calendar_valid_until(japan_bank_projected(2100i64)), business_calendar_valid_until(japan_bank_projected(2030i64))), "unreachable")

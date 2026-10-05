module BedHolidays.TestsNeg.Projection.BeforePublished
import Std.Datetime.Business (business_calendar_valid_until)
import BedHolidays.UsFederal (us_federal_projected)
def test_neg_projection_before_the_published_horizon() -> unit = test_assert(eq(business_calendar_valid_until(us_federal_projected(-20000i64)), business_calendar_valid_until(us_federal_projected(2031i64))), "unreachable")

module Tides.TestsNeg.Projection.InsidePublished
import Std.Datetime.Business (business_calendar_valid_until)
import Tides.EnglandAndWales (england_and_wales_projected)
def test_neg_projection_inside_the_published_horizon() -> unit = test_assert(eq(business_calendar_valid_until(england_and_wales_projected(2028i64)), business_calendar_valid_until(england_and_wales_projected(2029i64))), "unreachable")

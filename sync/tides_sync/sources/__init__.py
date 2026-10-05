"""One module per upstream source. Each exports `SOURCE`, a `model.Source`."""

from __future__ import annotations

from tides_sync.model import Source
from tides_sync.sources import (
    england_and_wales,
    hong_kong,
    japan_bank,
    new_south_wales,
    nyse,
    sifma,
    target,
    us_federal,
)

SOURCES: dict[str, Source] = {
    module.SOURCE.key: module.SOURCE
    for module in (
        england_and_wales,
        us_federal,
        japan_bank,
        new_south_wales,
        hong_kong,
        nyse,
        sifma,
        target,
    )
}

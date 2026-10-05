"""Japanese bank holidays: the Cabinet Office national-holiday list plus the
statutory bank closures of 31 December and 2 and 3 January.

The Cabinet Office CSV lists national holidays, substitute holidays and citizen's
holidays. Article 5 of the Banking Act Enforcement Order also closes banks on
Saturdays and from 31 December to 3 January. Banks have closed on every Saturday
since February 1989, so the calendar, whose weekmask is Monday to Friday, starts at
the first full year under that rule, 1990, even though the list reaches back to 1955.
"""

from __future__ import annotations

import csv
import datetime
import io

from tides_sync.model import Holiday, Published, published_years, require_names, single_part

FIRST_YEAR = 1990
# The Cabinet Office's names: the national holidays, 休日 for a substitute or
# citizen's holiday, and the days made holidays for one year by statute.
NAMES = frozenset(
    {
        "元日", "成人の日", "建国記念の日", "天皇誕生日", "春分の日", "昭和の日", "みどりの日",
        "憲法記念日", "こどもの日", "海の日", "山の日", "敬老の日", "秋分の日", "体育の日",
        "スポーツの日", "体育の日（スポーツの日）", "文化の日", "勤労感謝の日", "休日",
        "休日（祝日扱い）", "即位礼正殿の儀", "結婚の儀",
    }
)
YEAR_END_CLOSURE = "Bank closure (Banking Act Enforcement Order, art. 5)"


def year_end_closures(year: int) -> list[Holiday]:
    return [
        Holiday(datetime.date(year, 1, 2), YEAR_END_CLOSURE),
        Holiday(datetime.date(year, 1, 3), YEAR_END_CLOSURE),
        Holiday(datetime.date(year, 12, 31), YEAR_END_CLOSURE),
    ]


def national_holidays(raw: bytes) -> list[Holiday]:
    rows = list(csv.reader(io.StringIO(raw.decode("shift_jis"))))
    holidays = []
    for row in rows[1:]:
        if not row:
            continue
        year, month, day = (int(part) for part in row[0].split("/"))
        holidays.append(Holiday(datetime.date(year, month, day), row[1].strip()))
    return holidays


def parse(raw: bytes) -> Published:
    national = national_holidays(raw)
    last_year = max(h.day.year for h in national)
    years = range(FIRST_YEAR, last_year + 1)
    closures = [closure for year in years for closure in year_end_closures(year)]
    # The national list before 1990 is published but outside this calendar's horizon.
    in_horizon = [h for h in national if h.day.year >= FIRST_YEAR]
    require_names([h.name for h in in_horizon], NAMES, "Cabinet Office syukujitsu.csv")
    return published_years(in_horizon + closures, FIRST_YEAR, last_year)


SOURCE = single_part(
    "japan_bank",
    "Cabinet Office, Government of Japan, national holidays (syukujitsu.csv)",
    "https://www8.cao.go.jp/chosei/shukujitsu/syukujitsu.csv",
    "csv",
    parse,
)

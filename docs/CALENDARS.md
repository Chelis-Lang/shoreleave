# Calendars

Each calendar is a `Std.Datetime.Business` `BusinessCalendar` produced by a nullary
function, and each has a named projection. Import them from `BedHolidays.<Module>`.

| Producer | Module | Source | Weekmask | Published horizon |
|---|---|---|---|---|
| `england_and_wales()` | `EnglandAndWales` | gov.uk bank holidays (JSON) | Mon–Fri | 2019-01-01 to 2028-12-31 |
| `us_federal()` | `UsFederal` | US Office of Personnel Management, federal holidays (HTML tables) | Mon–Fri | 2011-01-01 to 2030-12-31 |
| `japan_bank()` | `JapanBank` | Cabinet Office national holidays (`syukujitsu.csv`) plus the statutory bank closures | Mon–Fri | 1990-01-01 to 2027-12-31 |
| `new_south_wales()` | `NewSouthWales` | NSW Government public holidays (HTML table) | Mon–Fri | 2026-01-01 to 2027-12-31 |
| `hong_kong()` | `HongKong` | Hong Kong 1823 general holidays (JSON) | Mon–Sat | 2025-01-01 to 2027-12-31 |
| `nyse()` | `Nyse` | nyse.com holidays and trading hours (HTML table) | Mon–Fri | 2026-01-01 to 2028-12-31 |
| `sifma()` | `Sifma` | SIFMA US holiday recommendations (page data) | Mon–Fri | 2026-01-01 to 2027-12-31 |
| `target()` | `Target` | ECB public holidays, TARGET closing days marked (HTML) | Mon–Fri | 2026-01-01 to 2028-12-31 |

## Horizons

A calendar's horizon is the span its source publishes, whole years from the first
to the last year listed. A query outside it fails `domain`, and the `try_` forms
return `None`; a calendar is never extended silently. Three horizons are narrower
than the list behind them:

- `japan_bank()` starts in 1990, the first full year after Japanese banks closed on
  every Saturday (February 1989), because its weekmask is Monday to Friday.
- `us_federal()` ends on 30 December instead of 31 December when the next 1 January
  is a Saturday: that Friday is observed under the next year's schedule, which the
  source does not yet list.
- A day a source lists outside its own years (OPM's 2011 schedule names Friday
  31 December 2010) is left out.

## What each calendar leaves out

- `us_federal()`: Inauguration Day, a holiday only in the Washington, DC area, and
  closures ordered by executive order, which OPM does not list in its schedules.
- `new_south_wales()`: the August Bank Holiday, which closes bank branches but is not
  a declared public holiday.
- `nyse()` and `sifma()`: early closes, which are trading days.
- `target()`: ECB public holidays that are not TARGET closing days.

## Projections

`<calendar>_projected(until_year)` is the published calendar extended through
31 December of `until_year` by the calendar's rules, which `<calendar>_rule_holidays(year)`
exposes. It fails `domain` (and `try_<calendar>_projected` returns `None`) when
`until_year` does not pass the published horizon or is after
`<calendar>_projection_last_year()`. A rule cannot state a holiday that is announced
or follows a lunar or solar calendar, so a projection omits:

| Calendar | Omitted from a projection |
|---|---|
| England and Wales | holidays proclaimed for one year, and proclaimed moves of a rule holiday |
| US federal | Inauguration Day and executive-order closures (also absent from the published calendar) |
| Japan (banks) | holidays made for one year, one-year statutory moves, later amendments of the Act; equinox days are predicted by formula, so projections end by 2099 |
| New South Wales | holidays declared for one year, such as a national day of mourning |
| Hong Kong | Lunar New Year (with its fourth-day substitute), Ching Ming, the Buddha's Birthday, Tuen Ng, the day after Mid-Autumn, Chung Yeung, the moves they force on rule holidays, and additional general holidays |
| NYSE | one-day closures the exchange announces |
| SIFMA | Good Friday, Veterans Day on a weekend, and announced one-day closes |
| TARGET | nothing: every closing day is fixed by the TARGET Guideline |

The tests check each rule set against the published dates for every year both
cover, and name the exact days by which an announced or lunar year differs.

## Provenance

Each calendar module exposes `<calendar>_source()` (the publishing authority),
`<calendar>_source_url()`, `<calendar>_retrieved()` (the retrieval date, a `Date`)
and `<calendar>_snapshot_sha256()` (the SHA-256 of the stored upstream response).
`BedHolidays.Provenance.holidays_version()` returns the package version.

The raw response of every source is stored under `upstream/`, and
`upstream/manifest.json` records each one's URL, retrieval date, file and SHA-256.
That stored snapshot is the pinned upstream release of its calendar: generation
reads only these files, so it is reproducible offline.

The package version is `YYYY.MMDD.N`: the newest retrieval date, then a counter for
releases of the same data, such as one for a new compiler pin. The generator refuses
a version whose date part is not the newest retrieval date.

## Regenerating

The generator under `sync/` is a uv project:

```sh
cd sync
uv run python -m bed_holidays_sync fetch            # refresh every snapshot (network)
uv run python -m bed_holidays_sync fetch nyse       # or only some
uv run python -m bed_holidays_sync generate         # rewrite src/published/ and src/provenance.ch
uv run python -m bed_holidays_sync check            # fail when a generated module is stale
uv run pytest
```

`fetch` parses each response before storing it, so a source whose page changes shape
fails loudly instead of yielding fewer holidays. After a fetch, set the package
version to the new retrieval date, regenerate, and run the Chelis tests: a changed
published year that no longer matches the rules shows up there by name.

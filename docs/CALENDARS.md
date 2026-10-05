# Calendars

Each calendar is a `Std.Datetime.Business` `BusinessCalendar` produced by a nullary
function, and each has a named projection. Import them from `Shoreleave.<Module>`.

| Producer | Module | Source | Weekmask | Published horizon |
|---|---|---|---|---|
| `england_and_wales()` | `EnglandAndWales` | gov.uk bank holidays (JSON) | Mon–Fri | 2019-01-01 to 2028-12-31 |
| `us_federal()` | `UsFederal` | OPM federal holidays (iCal), plus Federal Register executive orders closing agencies | Mon–Fri | 2021-01-01 to 2030-12-31 |
| `japan_bank()` | `JapanBank` | Cabinet Office national holidays (`syukujitsu.csv`), plus the statutory bank closures | Mon–Fri | 1990-01-01 to 2027-12-31 |
| `new_south_wales()` | `NewSouthWales` | Public Holidays Act 2010 s4 rules, checked against the NSW Government's table (HTML), which also records s5 declared days | Mon–Fri | 2026-01-01 to 2027-12-31 |
| `hong_kong()` | `HongKong` | Hong Kong 1823 general holidays (JSON) | Mon–Sat | 2025-01-01 to 2027-12-31 |
| `nyse()` | `Nyse` | nyse.com holidays and trading hours (HTML) | Mon–Fri | 2026-01-01 to 2028-12-31 |
| `sifma()` | `Sifma` | SIFMA US holiday recommendations (page data) | Mon–Fri | 2026-01-01 to 2027-12-31 |
| `target()` | `Target` | TARGET Guideline rule, checked against the days the ECB's public-holidays page marks (HTML) | Mon–Fri | 2026-01-01 to 2028-12-31 |

## Horizons

A calendar's horizon is the span its source publishes, whole years from the first
to the last year listed. A query outside it fails `domain`, and the `try_` forms
return `None`; a calendar is never extended silently. Two horizons are narrower
than the list behind them:

- `japan_bank()` starts in 1990, the first full year after Japanese banks closed on
  every Saturday (February 1989), because its weekmask is Monday to Friday.
- `us_federal()` would end on 30 December instead of 31 December if the next
  1 January were a Saturday: that Friday is observed under the next year's schedule,
  which the source would not yet list.

## What each published calendar holds

- `us_federal()`: the legal public holidays on their observed days, indexed by the
  observed date, so a Saturday 1 January is the previous 31 December (2021-12-31,
  2027-12-31). It also holds the days executive orders closed executive departments
  and agencies: 2024-12-24 (EO 14129), 2025-01-09 (EO 14133) and 2025-12-24 and
  2025-12-26 (EO 14371). Each order's Federal Register text is snapshotted, and
  generation fails unless its first section still names exactly those days. A new
  closure order is added to the generator's list when it is published. Inauguration
  Day, a holiday only in the Washington, DC area, is left out.
- `japan_bank()`: the national, substitute and citizen's holidays the Cabinet Office
  lists, plus 31 December and 2 and 3 January (Banking Act Enforcement Order, art. 5).
- `new_south_wales()`: the s4 standard holidays, generated from the rules, plus the
  days the Minister declared under s5 (2026-04-27 and 2027-04-26, the additional days
  for a weekend Anzac Day). Generation fails unless the published table holds exactly
  these. The August Bank Holiday is not a public holiday and is left out.
- `target()`: the rule's closing days. Generation fails unless the days the ECB marks
  as TARGET closing days are exactly the rule's; the page's other rows are ECB office
  holidays (Corpus Christi, Day of German Unity and so on).
- `nyse()` and `sifma()`: full-day closures only. A `BusinessCalendar` has no
  half-day kind, so an early close is a business day. The early closes and their
  closing times are kept in each calendar's parse listing and in the generated
  module's comments. SIFMA entries marked "Tentative" stop generation unless the
  generator lists them explicitly.

## Announced closures are current only as of retrieval

Some closures are announced for one occasion: the executive orders closing federal
agencies that `us_federal()` reads from the Federal Register, and the one-day
closures NYSE and SIFMA announce. A calendar holds the ones published by its
`<calendar>_retrieved()` date and no later. A closure announced after that date,
even for a day inside the horizon, is absent until the calendar is fetched and
regenerated, and for `us_federal()` until its order is added to the generator's
list of closure orders.

## Projections

`<calendar>_projected(until_year)` is the published calendar extended through
31 December of `until_year` by the calendar's rules, which `<calendar>_rule_holidays(year)`
exposes. It fails `domain` (and `try_<calendar>_projected` returns `None`) when
`until_year` does not pass the published horizon or is after
`<calendar>_projection_last_year()`. One-off days come only from published data,
never from a rule, so a projection omits:

| Calendar | Omitted from a projection |
|---|---|
| England and Wales | holidays proclaimed for one year, and proclaimed moves of a rule holiday |
| US federal | executive-order closures |
| Japan (banks) | holidays made for one year, one-year statutory moves, later amendments of the Act; equinox days are predicted by formula, so projections end by 2099 |
| New South Wales | days the Minister declares, such as an additional day for a weekend Anzac Day or a national day of mourning |
| Hong Kong | Lunar New Year (with its fourth-day substitute), Ching Ming, the Buddha's Birthday, Tuen Ng, the day after Mid-Autumn, Chung Yeung, the moves they force on rule holidays, and additional general holidays |
| NYSE | one-day closures the exchange announces; a Saturday 1 January closes no day (Rule 7.2's accounting-period exception) |
| SIFMA | Good Friday, which SIFMA makes a full or early close each year, Veterans Day on a weekend, and announced one-day closes |
| TARGET | nothing: every closing day is fixed by the TARGET Guideline |

The Chelis tests check each rule set against the published dates for every year both
cover, and name the exact days by which an announced, declared or lunar year differs.

## Provenance

Each calendar module exposes `<calendar>_source()` (the publishing authorities),
`<calendar>_source_urls()`, `<calendar>_retrieved()` (the retrieval date of its
oldest document, a `Date`) and `<calendar>_snapshot_sha256s()` (the SHA-256 of each
stored upstream document, in the order of the URLs). `Shoreleave.Provenance.shoreleave_version()`
returns the package version.

Every fetched document is stored under `upstream/<calendar>/`, and
`upstream/manifest.json` records each one's URL, retrieval date, file and SHA-256.
That stored snapshot is the pinned upstream release of its calendar: generation reads
only these files, so it is reproducible offline. `upstream/<calendar>/parsed.txt`
lists every dated entry the parse produced (holiday, excluded with its reason, or
early close with its time), so a regeneration that adds, removes or reclassifies a
date shows as a changed line in review.

Every parser checks each holiday's name against the calendar's allowlist, so an entry
of another calendar sharing the page, or a new kind of entry, stops regeneration
instead of entering the calendar. It also checks every weekday the source names
against its date.

The package version is `YYYY.MMDD.N`: the newest retrieval date, then a counter for
releases of the same data, such as one for a new compiler pin. The generator refuses
a version whose date part is not the newest retrieval date.

## Regenerating

The generator under `sync/` is a uv project:

```sh
cd sync
uv run python -m shoreleave_sync fetch            # refresh every snapshot (network)
uv run python -m shoreleave_sync fetch nyse       # or only some
uv run python -m shoreleave_sync generate         # rewrite src/published/, src/provenance.ch and the parse listings
uv run python -m shoreleave_sync check            # fail when a generated file is stale
uv run pytest
```

`fetch` parses each document before storing it, so a source whose page changes shape
fails loudly instead of yielding fewer holidays. After a fetch, set the package
version to the new retrieval date, regenerate, review the listing diff, and run the
Chelis tests: a changed published year that no longer matches the rules shows up
there by name.

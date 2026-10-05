# shoreleave

Business-day calendars for Chelis, built from each jurisdiction's or market's own
published holiday list. Every calendar is a `Std.Datetime.Business`
`BusinessCalendar` whose horizon is the span its source publishes: a query outside
that span fails `domain` (or returns `None` from a `try_` form) instead of guessing.

`shoreleave` is one of the `bed` packages, the seabed family of external-data packages:
data whose truth is set outside any program, synced from its upstream on the upstream's schedule. Each
`bed` package lives in its own repository and has its own semantic version; each
calendar reports when its data was retrieved.

[`docs/CALENDARS.md`](docs/CALENDARS.md) lists the calendars, their sources and
horizons, what each projection omits, the provenance values, and how to regenerate
the data.

## Toolchain

The package pins its compiler in `reef.toml`. Install that toolchain with
`chelisup`, as described in the Chelis install guide, and run
`chelis reef conform audit` to check the shell contract.

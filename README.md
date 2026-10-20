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

## Use a calendar

Install the compiler selected by [`reef.toml`](reef.toml) with
[`chelisup`](https://github.com/Chelis-Lang/chelis#installation), then install
the package:

```sh
chelis reef install --from-github Chelis-Lang/shoreleave@v0.1.5
```

Add it to your project's manifest:

```toml
[dependencies]
shoreleave = { version = "=0.1.5" }
```

Import a calendar from `Shoreleave.<Module>` and use the business-day operations
in `Std.Datetime.Business`. For example, `Shoreleave.Nyse.nyse()` provides the
published NYSE calendar. The [calendar reference](docs/CALENDARS.md) lists each
module, published horizon, and projection function.

## Run the example

From this checkout:

```sh
chelis eval --file demos/digest.ch
chelis build --target c --output target/digest demos/digest.ch
target/digest/digest
```

The evaluator and native executable print the same calendar digest: horizons,
holiday counts, business-day counts, offsets, and modified-following rolls.
The final values demonstrate rejected out-of-horizon queries and invalid
projections. The full program is [`demos/digest.ch`](demos/digest.ch).

## License

Shoreleave's code is licensed under the [MIT License](LICENSE). Calendar
snapshots under `upstream/` come from the sources listed in
[`docs/CALENDARS.md`](docs/CALENDARS.md) and retain their source terms.

## Toolchain

The package pins its compiler in `reef.toml`. Install that toolchain with
`chelisup`, as described in the Chelis install guide, and run
`chelis reef conform audit` to check the shell contract.

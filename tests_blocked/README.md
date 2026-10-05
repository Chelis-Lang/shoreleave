# Blocked-probe suite

One expected-to-fail reproducer per open upstream blocker
(`<area>/<name>.ch` + `<name>.expect`; line 1 = pinned diagnostic substring,
lines 2+ = the `chelis#NNN` citation + on-pass de-narrowing instructions).
Run with `chelis test tests_blocked/ --expect blocked`. Blockers the harness
cannot express (check-context-only, cross-module) are listed here for manual
re-probe.

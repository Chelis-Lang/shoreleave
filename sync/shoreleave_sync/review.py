"""The pull-request body a scheduled sync opens: what changed in each calendar's
parse listing, so a reviewer reads dates, not snapshot bytes."""

from __future__ import annotations

import re

MAX_LINES_PER_CALENDAR = 200

HEADER = """Scheduled sync: re-fetched every source and regenerated the package.

Each calendar below lists the entries its parse listing (`upstream/<calendar>/parsed.txt`)
gained (+) or lost (-). Re-pinned snapshots whose entries did not change are not part
of this pull request. Review each change against its source, bump the package version
in `reef.toml` and regenerate before release.
"""


def changes_by_calendar(diff: str) -> dict[str, list[str]]:
    """The added and removed listing lines of a `git diff`, keyed by calendar."""
    changes: dict[str, list[str]] = {}
    calendar = None
    for line in diff.splitlines():
        match = re.match(r"^\+\+\+ b/upstream/([a-z_]+)/parsed\.txt$", line)
        if match:
            calendar = match.group(1)
            changes.setdefault(calendar, [])
            continue
        if line.startswith(("+++", "---")) or calendar is None:
            continue
        if line.startswith(("+", "-")) and not re.match(r"^[+-]# (?!horizon )", line):
            changes[calendar].append(line)
    return {key: lines for key, lines in changes.items() if lines}


def pr_body(diff: str) -> str:
    changes = changes_by_calendar(diff)
    parts = [HEADER]
    if not changes:
        parts.append("No calendar's entries changed; only snapshot provenance did.\n")
    for calendar, lines in sorted(changes.items()):
        shown = lines[:MAX_LINES_PER_CALENDAR]
        parts.append(f"### {calendar}\n\n```diff\n" + "\n".join(shown) + "\n```\n")
        if len(lines) > len(shown):
            parts.append(f"... and {len(lines) - len(shown)} more lines; see `upstream/{calendar}/parsed.txt`.\n")
    return "\n".join(parts)

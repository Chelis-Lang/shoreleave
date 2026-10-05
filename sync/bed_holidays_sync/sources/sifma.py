"""SIFMA's recommended full-day closes of the US bond market, from sifma.org.

The page is rendered from a React Server Components payload embedded in the HTML.
The parser decodes that payload, follows its row references from the "U.S. Holiday
Recommendations" section, and reads each holiday card: a heading, the full-close
day (empty when there is none) and a note naming any early close. Early closes,
Good Friday's included when SIFMA recommends only an early close, are not closures.
"""

from __future__ import annotations

import json
import re
from typing import Any

from bed_holidays_sync.model import Exclusion, Holiday, Published, Source, parse_month_day, published_years

SECTION = "U.S. Holiday Recommendations"
_PUSH = re.compile(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)')
_REFERENCE = re.compile(r"\$L?([0-9a-f]+)")
_PANEL = re.compile(r"(\d{4})-\d+")


def payload_rows(document: str) -> dict[str, Any]:
    payload = "".join(json.loads(f'"{chunk}"') for chunk in _PUSH.findall(document))
    rows: dict[str, Any] = {}
    for part in re.split(r"\n(?=[0-9a-f]+:)", "\n" + payload):
        match = re.match(r"([0-9a-f]+):(.*)\Z", part, re.S)
        if match and match.group(2)[:1] in "[{":
            rows[match.group(1)] = json.loads(match.group(2))
    return rows


def deref(rows: dict[str, Any], node: Any) -> Any:
    """The row a reference string names, or node itself."""
    if isinstance(node, str):
        match = _REFERENCE.fullmatch(node)
        if match and match.group(1) in rows:
            return rows[match.group(1)]
    return node


def _text(node: Any) -> str:
    props = node[3] if isinstance(node, list) and len(node) == 4 and node[0] == "$" else {}
    children = props.get("children") if isinstance(props, dict) else None
    return children.strip() if isinstance(children, str) else ""


def cards(rows: dict[str, Any], node: Any, panel: str | None, seen: frozenset[str] = frozenset()):
    """Yield (panel, heading, full-close text, note) for every card below node."""
    if isinstance(node, str):
        match = _REFERENCE.fullmatch(node)
        if match and match.group(1) in rows and match.group(1) not in seen:
            yield from cards(rows, rows[match.group(1)], panel, seen | {match.group(1)})
        return
    if isinstance(node, dict):
        yield from cards(rows, node.get("children"), panel, seen)
        return
    if not isinstance(node, list):
        return
    if len(node) == 4 and node[0] == "$" and isinstance(node[3], dict):
        props = node[3]
        value = props.get("value")
        if isinstance(value, str) and _PANEL.fullmatch(value):
            panel = value
        children = props.get("children")
        parts = [deref(rows, c) for c in children] if isinstance(children, list) else []
        if (
            node[1] == "div"
            and len(parts) == 3
            and all(isinstance(c, list) and len(c) == 4 and c[0] == "$" for c in parts)
            and [c[1] for c in parts] == ["h3", "span", "p"]
        ):
            yield panel, _text(parts[0]), _text(parts[1]), _text(parts[2])
            return
        yield from cards(rows, children, panel, seen)
        return
    for child in node:
        yield from cards(rows, child, panel, seen)


def parse(raw: bytes) -> Published:
    rows = payload_rows(raw.decode("utf-8"))
    (section,) = [key for key, row in rows.items() if SECTION in json.dumps(row, ensure_ascii=False)]
    holidays: list[Holiday] = []
    exclusions: list[Exclusion] = []
    years: set[int] = set()
    for panel, heading, close, note in cards(rows, rows[section], None):
        if panel is None:
            raise ValueError(f"card {heading!r} lies outside a year panel")
        years.add(int(_PANEL.fullmatch(panel).group(1)))
        if close:
            holidays.append(Holiday(parse_month_day(close), heading))
        if note and note.startswith("Early Close"):
            day = parse_month_day(note.split(":", 2)[-1] if note.count(":") >= 2 else note)
            exclusions.append(Exclusion(day, heading, note))
    ordered = sorted(years)
    if not ordered or ordered != list(range(ordered[0], ordered[-1] + 1)):
        raise ValueError(f"SIFMA panels skip a year: {ordered}")
    return published_years(holidays, ordered[0], ordered[-1], exclusions)


SOURCE = Source(
    key="sifma",
    authority="SIFMA, US holiday recommendations (fixed income)",
    url="https://www.sifma.org/resources/general/holiday-schedule/",
    suffix="html",
    parse=parse,
)

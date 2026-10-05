"""Command line: `fetch` refreshes snapshots over the network; `generate` and
`check` work offline from the pinned snapshots."""

from __future__ import annotations

import argparse
import datetime
import pathlib
import re
import sys

from tides_sync import emit, snapshot
from tides_sync.sources import SOURCES

ROOT = pathlib.Path(__file__).resolve().parents[2]


def package_version(root: pathlib.Path) -> str:
    match = re.search(r'(?m)^version\s*=\s*"([^"]+)"', (root / "reef.toml").read_text(encoding="utf-8"))
    if match is None:
        raise ValueError("reef.toml has no package version")
    return match.group(1)


def expected_version_prefix(snapshots: list[snapshot.Snapshot]) -> str:
    newest = max(s.retrieved for s in snapshots)
    return f"{newest.year}.{newest.month * 100 + newest.day}."


def generated_files(root: pathlib.Path) -> dict[pathlib.Path, str]:
    """Every generated file and its content, computed from the pinned snapshots."""
    upstream = root / "upstream"
    files: dict[pathlib.Path, str] = {}
    snapshots = []
    for key, source in SOURCES.items():
        snaps, raws = snapshot.load(upstream, source)
        snapshots.extend(snaps.values())
        published = source.parse(raws)
        files[root / "src" / "published" / f"{emit.pascal(key).lower()}.ch"] = emit.published_module(source, snaps, published)
        files[upstream / key / "parsed.txt"] = emit.parsed_listing(source, snaps, published)
    version = package_version(root)
    prefix = expected_version_prefix(snapshots)
    if not version.startswith(prefix) or not re.fullmatch(r"\d+", version[len(prefix):]):
        raise ValueError(f"package version {version} must be {prefix}N for the newest retrieval date")
    files[root / "src" / "provenance.ch"] = emit.provenance_module(version)
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tides_sync")
    parser.add_argument("--root", type=pathlib.Path, default=ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    fetch = commands.add_parser("fetch", help="download and pin fresh snapshots")
    fetch.add_argument("keys", nargs="*", metavar="KEY", help=f"any of {sorted(SOURCES)}; all by default")
    commands.add_parser("generate", help="write the generated Chelis modules")
    commands.add_parser("check", help="fail when a generated module is stale")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.command == "fetch":
        today = datetime.date.today()
        unknown = sorted(set(args.keys) - set(SOURCES))
        if unknown:
            parser.error(f"unknown source(s) {unknown}; choose from {sorted(SOURCES)}")
        for key in args.keys or list(SOURCES):
            source = SOURCES[key]
            raws = {part.name: snapshot.fetch_bytes(part.url) for part in source.parts}
            for name, snap in snapshot.store(root / "upstream", source, raws, today).items():
                print(f"{key}/{name}: {snap.file} {snap.sha256[:12]} retrieved {snap.retrieved}")
        return 0
    files = generated_files(root)
    stale = [path for path, text in files.items() if not path.exists() or path.read_text(encoding="utf-8") != text]
    if args.command == "check":
        for path in stale:
            print(f"stale: {path.relative_to(root)}", file=sys.stderr)
        return 1 if stale else 0
    for path in stale:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(files[path], encoding="utf-8")
        print(f"wrote {path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

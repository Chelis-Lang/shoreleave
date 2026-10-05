"""Command line: `fetch` refreshes snapshots over the network; `generate` and
`check` work offline from the pinned snapshots."""

from __future__ import annotations

import argparse
import datetime
import pathlib
import re
import subprocess
import sys

from shoreleave_sync import emit, review, snapshot
from shoreleave_sync.sources import SOURCES

ROOT = pathlib.Path(__file__).resolve().parents[2]


def package_version(root: pathlib.Path) -> str:
    match = re.search(r'(?m)^version\s*=\s*"([^"]+)"', (root / "reef.toml").read_text(encoding="utf-8"))
    if match is None:
        raise ValueError("reef.toml has no package version")
    return match.group(1)


def unchanged(upstream: pathlib.Path, source, fresh) -> bool:
    """Whether the pinned snapshot parses to exactly the entries a fresh fetch does.

    A page can change bytes without changing a date (a timestamp, a layout tweak),
    so a fetch keeps the pinned snapshot and its retrieval date unless the entries
    differ; `--force` re-pins regardless.
    """
    try:
        _, raws = snapshot.load(upstream, source)
    except FileNotFoundError:
        return False
    return emit.listing_entries(source.parse(raws)) == emit.listing_entries(fresh)


def retrieved_text(upstream: pathlib.Path, source) -> str:
    snaps, _ = snapshot.load(upstream, source)
    return emit.retrieved(snaps).isoformat()


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
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError(f"package version {version} is not a plain MAJOR.MINOR.PATCH semantic version")
    files[root / "src" / "provenance.ch"] = emit.provenance_module(version)
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="shoreleave_sync")
    parser.add_argument("--root", type=pathlib.Path, default=ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    fetch = commands.add_parser("fetch", help="download and pin fresh snapshots")
    fetch.add_argument("keys", nargs="*", metavar="KEY", help=f"any of {sorted(SOURCES)}; all by default")
    fetch.add_argument("--force", action="store_true", help="store new snapshots even when they parse to the same entries")
    commands.add_parser("generate", help="write the generated Chelis modules")
    commands.add_parser("check", help="fail when a generated module is stale")
    body = commands.add_parser("pr-body", help="describe the uncommitted listing changes as a pull-request body")
    body.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.command == "fetch":
        today = datetime.date.today()
        unknown = sorted(set(args.keys) - set(SOURCES))
        if unknown:
            parser.error(f"unknown source(s) {unknown}; choose from {sorted(SOURCES)}")
        failures = []
        for key in args.keys or list(SOURCES):
            source = SOURCES[key]
            try:
                raws = {part.name: snapshot.fetch_bytes(part.url) for part in source.parts}
                fresh = source.parse(raws)
            except Exception as error:  # every source is tried; each failure is reported
                failures.append(f"{key}: {type(error).__name__}: {error}")
                continue
            if not args.force and unchanged(root / "upstream", source, fresh):
                print(f"{key}: unchanged; keeping the snapshot retrieved {retrieved_text(root / 'upstream', source)}")
                continue
            for name, snap in snapshot.store(root / "upstream", source, raws, today).items():
                print(f"{key}/{name}: {snap.file} {snap.sha256[:12]} retrieved {snap.retrieved}")
        for failure in failures:
            print(f"FAILED {failure}", file=sys.stderr)
        if failures:
            return 1
        return 0
    if args.command == "pr-body":
        diff = subprocess.run(
            ["git", "-C", str(root), "diff", "HEAD", "--", "upstream/*/parsed.txt"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        args.output.write_text(review.pr_body(diff), encoding="utf-8")
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

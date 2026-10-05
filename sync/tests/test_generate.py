"""The generated Chelis modules against the snapshots they are generated from."""

from __future__ import annotations

import datetime
import hashlib
import json
import re
import shutil
import subprocess

import pytest

from tides_sync import __main__ as cli
from tides_sync import emit, snapshot
from tides_sync.model import Published
from tides_sync.sources import SOURCES
from conftest import ROOT, UPSTREAM

DATE = re.compile(r"date\((-?\d+)i64, (\d+)i64, (\d+)i64\)")


def test_generated_modules_are_current() -> None:
    assert cli.main(["--root", str(ROOT), "check"]) == 0


@pytest.mark.parametrize("key", sorted(SOURCES))
def test_each_module_holds_exactly_its_source(published: dict[str, Published], key: str) -> None:
    text = (ROOT / "src" / "published" / f"{emit.pascal(key).lower()}.ch").read_text(encoding="utf-8")
    holiday_defs = [line for line in text.splitlines() if re.match(rf"def {key}_\d{{4}}\(\)", line)]
    emitted = [datetime.date(int(y), int(m), int(d)) for line in holiday_defs for y, m, d in DATE.findall(line)]
    assert emitted == [h.day for h in published[key].holidays]
    p = published[key]
    assert f"def {key}_published_from() -> Date = {emit.date_literal(p.valid_from)}" in text
    assert f"def {key}_published_until() -> Date = {emit.date_literal(p.valid_until)}" in text


def test_manifest_records_every_part_of_every_source() -> None:
    manifest = json.loads((UPSTREAM / "manifest.json").read_text(encoding="utf-8"))
    assert sorted(manifest) == sorted(SOURCES)
    for key, parts in manifest.items():
        assert sorted(parts) == sorted(p.name for p in SOURCES[key].parts)
        for part in SOURCES[key].parts:
            entry = parts[part.name]
            raw = (UPSTREAM / entry["file"]).read_bytes()
            assert hashlib.sha256(raw).hexdigest() == entry["sha256"]
            assert entry["url"] == part.url


def test_package_version_follows_the_newest_retrieval() -> None:
    snaps = [snap for s in SOURCES.values() for snap in snapshot.load(UPSTREAM, s)[0].values()]
    assert cli.package_version(ROOT).startswith(cli.expected_version_prefix(snaps))


# Negative twins.


def test_tampered_snapshot_is_rejected(tmp_path) -> None:
    shutil.copytree(UPSTREAM, tmp_path / "upstream")
    path = tmp_path / "upstream" / "target" / "main.html"
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="SHA-256"):
        snapshot.load(tmp_path / "upstream", SOURCES["target"])


def test_stale_module_is_reported(tmp_path) -> None:
    for name in ("upstream", "src"):
        shutil.copytree(ROOT / name, tmp_path / name)
    shutil.copy(ROOT / "reef.toml", tmp_path / "reef.toml")
    assert cli.main(["--root", str(tmp_path), "check"]) == 0
    stale = tmp_path / "src" / "published" / "target.ch"
    assert stale.exists()
    stale.write_text(stale.read_text(encoding="utf-8").replace("2026i64, 5i64, 1i64", "2026i64, 5i64, 4i64"), encoding="utf-8")
    assert cli.main(["--root", str(tmp_path), "check"]) == 1


def test_version_not_from_the_newest_retrieval_is_rejected(tmp_path) -> None:
    for name in ("upstream", "src"):
        shutil.copytree(ROOT / name, tmp_path / name)
    reef = (ROOT / "reef.toml").read_text(encoding="utf-8")
    (tmp_path / "reef.toml").write_text(re.sub(r'(?m)^version = ".*"', 'version = "2025.101.0"', reef), encoding="utf-8")
    with pytest.raises(ValueError, match="newest retrieval date"):
        cli.generated_files(tmp_path)


def test_non_ascii_string_literal_is_rejected() -> None:
    assert emit.string_literal('a "b" \\c') == '"a \\"b\\" \\\\c"'
    with pytest.raises(ValueError):
        emit.string_literal("Bank holiday’s")


def test_parsed_listing_records_every_entry(published: dict[str, Published]) -> None:
    # The listing is the review surface: an added, removed or reclassified date
    # changes one of its lines.
    for key, p in published.items():
        lines = (UPSTREAM / key / "parsed.txt").read_text(encoding="utf-8").splitlines()
        entries = [line for line in lines if not line.startswith("#")]
        assert len(entries) == len(p.holidays) + len(p.exclusions) + len(p.early_closes)
        assert f"# horizon {p.valid_from.isoformat()}..{p.valid_until.isoformat()}" in lines


def test_a_changed_date_shows_in_the_listing(tmp_path) -> None:
    for name in ("upstream", "src"):
        shutil.copytree(ROOT / name, tmp_path / name)
    shutil.copy(ROOT / "reef.toml", tmp_path / "reef.toml")
    gov_uk = tmp_path / "upstream" / "england_and_wales" / "main.json"
    raw = gov_uk.read_bytes().replace(b'"2028-08-28"', b'"2028-08-29"')
    gov_uk.write_bytes(raw)
    manifest = json.loads((tmp_path / "upstream" / "manifest.json").read_text(encoding="utf-8"))
    manifest["england_and_wales"]["main"]["sha256"] = hashlib.sha256(raw).hexdigest()
    (tmp_path / "upstream" / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    files = cli.generated_files(tmp_path)
    listing = files[tmp_path / "upstream" / "england_and_wales" / "parsed.txt"]
    assert "2028-08-29\tholiday\tSummer bank holiday" in listing
    assert "2028-08-28" not in listing
    assert cli.main(["--root", str(tmp_path), "check"]) == 1


def test_every_snapshot_and_listing_is_tracked() -> None:
    # An ignore rule can shadow a required artifact (an unanchored `target/`
    # once hid upstream/target/); a fresh clone would then lack it.
    manifest = json.loads((UPSTREAM / "manifest.json").read_text(encoding="utf-8"))
    required = ["upstream/manifest.json"]
    required += [f"upstream/{entry['file']}" for parts in manifest.values() for entry in parts.values()]
    required += [f"upstream/{key}/parsed.txt" for key in SOURCES]
    untracked = [
        path
        for path in required
        if subprocess.run(["git", "-C", str(ROOT), "ls-files", "--error-unmatch", path], capture_output=True).returncode != 0
    ]
    assert untracked == []

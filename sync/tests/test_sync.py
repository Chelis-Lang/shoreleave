"""The scheduled sync's pieces: fetch re-pins only changed entries, reports every
failing source, and the pull-request body shows listing changes."""

from __future__ import annotations

import datetime
import json
import shutil
import subprocess

import pytest

from conftest import ROOT
from shoreleave_sync import __main__ as cli
from shoreleave_sync import review, snapshot
from shoreleave_sync.sources import SOURCES


@pytest.fixture
def root(tmp_path):
    for name in ("upstream", "src"):
        shutil.copytree(ROOT / name, tmp_path / name)
    shutil.copy(ROOT / "reef.toml", tmp_path / "reef.toml")
    return tmp_path


def serve(root, edits=None, failing=()):
    """A fetch_bytes stand-in serving each part's pinned bytes, optionally edited."""
    by_url = {}
    for key, source in SOURCES.items():
        _, raws = snapshot.load(root / "upstream", source)
        for part in source.parts:
            raw = raws[part.name] + b"\n"  # new bytes, same entries
            if edits and key in edits:
                raw = edits[key](raw)
            by_url[part.url] = (key, raw)

    def fetch(url):
        key, raw = by_url[url]
        if key in failing:
            raise OSError(f"{url} unreachable")
        return raw

    return fetch


def manifest(root):
    return json.loads((root / "upstream" / "manifest.json").read_text(encoding="utf-8"))


def test_unchanged_entries_keep_the_pinned_snapshot(root, monkeypatch) -> None:
    before = manifest(root)
    monkeypatch.setattr(snapshot, "fetch_bytes", serve(root))
    assert cli.main(["--root", str(root), "fetch"]) == 0
    assert manifest(root) == before
    assert cli.main(["--root", str(root), "check"]) == 0


def test_changed_entries_repin_with_todays_date(root, monkeypatch) -> None:
    before = manifest(root)
    edit = {"england_and_wales": lambda raw: raw.replace(b'"2028-08-28"', b'"2028-08-29"')}
    monkeypatch.setattr(snapshot, "fetch_bytes", serve(root, edit))
    assert cli.main(["--root", str(root), "fetch"]) == 0
    after = manifest(root)
    assert after["england_and_wales"]["main"]["sha256"] != before["england_and_wales"]["main"]["sha256"]
    assert after["england_and_wales"]["main"]["retrieved"] == datetime.date.today().isoformat()
    assert {k: v for k, v in after.items() if k != "england_and_wales"} == {k: v for k, v in before.items() if k != "england_and_wales"}
    assert cli.main(["--root", str(root), "check"]) == 1  # the generated files now lag


def test_force_repins_unchanged_entries(root, monkeypatch) -> None:
    monkeypatch.setattr(snapshot, "fetch_bytes", serve(root))
    assert cli.main(["--root", str(root), "fetch", "--force", "target"]) == 0
    assert manifest(root)["target"]["main"]["retrieved"] == datetime.date.today().isoformat()


def test_every_failing_source_is_reported_and_the_rest_still_sync(root, monkeypatch, capsys) -> None:
    edit = {
        "target": lambda raw: raw.replace(b"Day of German Unity", b"Reformation Day"),
        "england_and_wales": lambda raw: raw.replace(b'"2028-08-28"', b'"2028-08-29"'),
    }
    monkeypatch.setattr(snapshot, "fetch_bytes", serve(root, edit, failing=("nyse",)))
    assert cli.main(["--root", str(root), "fetch"]) == 1
    err = capsys.readouterr().err
    assert "FAILED nyse: OSError" in err
    assert "FAILED target: ValueError" in err and "unknown holiday name" in err
    assert manifest(root)["england_and_wales"]["main"]["retrieved"] == datetime.date.today().isoformat()


DIFF = """\
diff --git a/upstream/nyse/parsed.txt b/upstream/nyse/parsed.txt
--- a/upstream/nyse/parsed.txt
+++ b/upstream/nyse/parsed.txt
@@ -1,4 +1,4 @@
 # nyse: New York Stock Exchange, holidays and trading hours
-# horizon 2026-01-01..2028-12-31
+# horizon 2026-01-01..2029-12-31
-# main: https://www.nyse.com/markets/hours-calendars retrieved 2026-10-05 sha256 aa
+# main: https://www.nyse.com/markets/hours-calendars retrieved 2026-12-21 sha256 bb
+2029-01-01\tholiday\tNew Year's Day
"""


def test_pr_body_lists_entry_changes_not_provenance() -> None:
    body = review.pr_body(DIFF)
    assert "### nyse" in body
    assert "+2029-01-01\tholiday\tNew Year's Day" in body
    assert "+# horizon 2026-01-01..2029-12-31" in body
    assert "sha256" not in body


def test_pr_body_with_only_provenance_changes_says_so() -> None:
    provenance_only = "\n".join(line for line in DIFF.splitlines() if "horizon" not in line and "2029-01-01" not in line)
    assert "No calendar's entries changed" in review.pr_body(provenance_only)


def test_pr_body_command_reads_the_working_tree(root, tmp_path_factory) -> None:
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-qm", "base"], check=True)
    listing = root / "upstream" / "target" / "parsed.txt"
    listing.write_text(listing.read_text(encoding="utf-8") + "2029-01-01\tholiday\tNew Year's Day\n", encoding="utf-8")
    output = tmp_path_factory.mktemp("body") / "body.md"
    assert cli.main(["--root", str(root), "pr-body", "--output", str(output)]) == 0
    assert "+2029-01-01\tholiday\tNew Year's Day" in output.read_text(encoding="utf-8")

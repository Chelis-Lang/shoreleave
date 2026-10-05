"""Pinned upstream snapshots: fetching them, and reading them back offline.

Each source's raw response is stored as `upstream/<key>.<suffix>`, and
`upstream/manifest.json` records its URL, retrieval date and SHA-256. Generation
reads only these files, so regenerating the package is reproducible offline and a
snapshot is the pinned upstream release of its calendar.
"""

from __future__ import annotations

import dataclasses
import datetime
import hashlib
import json
import pathlib
import ssl
import urllib.request

import truststore

from bed_holidays_sync.model import Source

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120 Safari/537.36 bed-holidays-sync"
)
MANIFEST = "manifest.json"


@dataclasses.dataclass(frozen=True)
class Snapshot:
    key: str
    url: str
    retrieved: datetime.date
    file: str
    sha256: str


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    # The operating system's verifier completes chains that a server sends
    # without its intermediate certificate, as browsers do.
    context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    with urllib.request.urlopen(request, timeout=60, context=context) as response:
        return response.read()


def read_manifest(upstream: pathlib.Path) -> dict[str, Snapshot]:
    path = upstream / MANIFEST
    if not path.exists():
        return {}
    entries = json.loads(path.read_text(encoding="utf-8"))
    return {
        key: Snapshot(key, e["url"], datetime.date.fromisoformat(e["retrieved"]), e["file"], e["sha256"])
        for key, e in entries.items()
    }


def write_manifest(upstream: pathlib.Path, snapshots: dict[str, Snapshot]) -> None:
    entries = {
        key: {"url": s.url, "retrieved": s.retrieved.isoformat(), "file": s.file, "sha256": s.sha256}
        for key, s in sorted(snapshots.items())
    }
    (upstream / MANIFEST).write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")


def store(upstream: pathlib.Path, source: Source, raw: bytes, retrieved: datetime.date) -> Snapshot:
    """Validate raw by parsing it, then record it as the source's pinned snapshot."""
    source.parse(raw)
    upstream.mkdir(parents=True, exist_ok=True)
    name = f"{source.key}.{source.suffix}"
    (upstream / name).write_bytes(raw)
    snapshot = Snapshot(source.key, source.url, retrieved, name, hashlib.sha256(raw).hexdigest())
    snapshots = read_manifest(upstream)
    snapshots[source.key] = snapshot
    write_manifest(upstream, snapshots)
    return snapshot


def load(upstream: pathlib.Path, source: Source) -> tuple[Snapshot, bytes]:
    """The pinned snapshot of source, checked against its recorded digest and URL."""
    snapshot = read_manifest(upstream).get(source.key)
    if snapshot is None:
        raise FileNotFoundError(f"no snapshot of {source.key}; run the fetch command")
    if snapshot.url != source.url:
        raise ValueError(f"{source.key}: snapshot is of {snapshot.url}, source is {source.url}")
    raw = (upstream / snapshot.file).read_bytes()
    if hashlib.sha256(raw).hexdigest() != snapshot.sha256:
        raise ValueError(f"{source.key}: {snapshot.file} does not match its recorded SHA-256")
    return snapshot, raw

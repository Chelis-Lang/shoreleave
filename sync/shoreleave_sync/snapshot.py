"""Pinned upstream snapshots: fetching them, and reading them back offline.

Each document of a source is stored as `upstream/<key>/<part>.<suffix>`, and
`upstream/manifest.json` records each one's URL, retrieval date and SHA-256.
Generation reads only these files, so regenerating the package is reproducible
offline and the stored snapshot is the pinned upstream release of its calendar.
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

from shoreleave_sync.model import Source

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120 Safari/537.36 shoreleave-sync"
)
MANIFEST = "manifest.json"


@dataclasses.dataclass(frozen=True)
class Snapshot:
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


def read_manifest(upstream: pathlib.Path) -> dict[str, dict[str, Snapshot]]:
    path = upstream / MANIFEST
    if not path.exists():
        return {}
    entries = json.loads(path.read_text(encoding="utf-8"))
    return {
        key: {
            name: Snapshot(e["url"], datetime.date.fromisoformat(e["retrieved"]), e["file"], e["sha256"])
            for name, e in parts.items()
        }
        for key, parts in entries.items()
    }


def write_manifest(upstream: pathlib.Path, manifest: dict[str, dict[str, Snapshot]]) -> None:
    entries = {
        key: {
            name: {"url": s.url, "retrieved": s.retrieved.isoformat(), "file": s.file, "sha256": s.sha256}
            for name, s in sorted(parts.items())
        }
        for key, parts in sorted(manifest.items())
    }
    (upstream / MANIFEST).write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")


def store(upstream: pathlib.Path, source: Source, raws: dict[str, bytes], retrieved: datetime.date) -> dict[str, Snapshot]:
    """Validate the documents by parsing them, then record them as the source's pinned snapshot."""
    source.parse(raws)
    directory = upstream / source.key
    directory.mkdir(parents=True, exist_ok=True)
    snapshots = {}
    for part in source.parts:
        name = f"{source.key}/{part.name}.{part.suffix}"
        (upstream / name).write_bytes(raws[part.name])
        snapshots[part.name] = Snapshot(part.url, retrieved, name, hashlib.sha256(raws[part.name]).hexdigest())
    manifest = read_manifest(upstream)
    manifest[source.key] = snapshots
    write_manifest(upstream, manifest)
    return snapshots


def load(upstream: pathlib.Path, source: Source) -> tuple[dict[str, Snapshot], dict[str, bytes]]:
    """The pinned snapshot of every part of source, checked against its digest and URL."""
    recorded = read_manifest(upstream).get(source.key)
    if recorded is None:
        raise FileNotFoundError(f"no snapshot of {source.key}; run the fetch command")
    if sorted(recorded) != sorted(p.name for p in source.parts):
        raise ValueError(f"{source.key}: snapshot parts {sorted(recorded)} are not the source's parts")
    raws = {}
    for part in source.parts:
        snap = recorded[part.name]
        if snap.url != part.url:
            raise ValueError(f"{source.key}/{part.name}: snapshot is of {snap.url}, source is {part.url}")
        raw = (upstream / snap.file).read_bytes()
        if hashlib.sha256(raw).hexdigest() != snap.sha256:
            raise ValueError(f"{source.key}/{part.name}: {snap.file} does not match its recorded SHA-256")
        raws[part.name] = raw
    return recorded, raws

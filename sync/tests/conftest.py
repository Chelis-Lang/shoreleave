from __future__ import annotations

import pathlib

import pytest

from shoreleave_sync import snapshot
from shoreleave_sync.model import Published
from shoreleave_sync.sources import SOURCES

ROOT = pathlib.Path(__file__).resolve().parents[2]
UPSTREAM = ROOT / "upstream"


def raw_parts(key: str) -> dict[str, bytes]:
    return snapshot.load(UPSTREAM, SOURCES[key])[1]


def raw_snapshot(key: str) -> bytes:
    """The single document of a one-part source."""
    return raw_parts(key)["main"]


def parse_one(key: str, raw: bytes) -> Published:
    return SOURCES[key].parse({"main": raw})


@pytest.fixture(scope="session")
def published() -> dict[str, Published]:
    return {key: source.parse(raw_parts(key)) for key, source in SOURCES.items()}

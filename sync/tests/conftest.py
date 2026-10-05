from __future__ import annotations

import pathlib

import pytest

from bed_holidays_sync import snapshot
from bed_holidays_sync.model import Published
from bed_holidays_sync.sources import SOURCES

ROOT = pathlib.Path(__file__).resolve().parents[2]
UPSTREAM = ROOT / "upstream"


def raw_snapshot(key: str) -> bytes:
    return snapshot.load(UPSTREAM, SOURCES[key])[1]


@pytest.fixture(scope="session")
def published() -> dict[str, Published]:
    return {key: source.parse(raw_snapshot(key)) for key, source in SOURCES.items()}

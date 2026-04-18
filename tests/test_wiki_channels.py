"""Spec-facing tests for the external corpus channel registry."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

from wiki.channels import CHANNELS_PATH, TRACK_CHANNEL_AFFINITY, get_track_affinity, load_channels


def test_registry_schema_covers_all_live_source_files():
    channels = load_channels(reload=True)
    source_files = {path.stem for path in CHANNELS_PATH.parent.glob("*.jsonl")}
    assert set(channels) == source_files


def test_track_affinity_lookup_and_missing_channel_fallback():
    load_channels(reload=True)

    assert get_track_affinity("realna_istoria", "hist") == 1.0
    assert get_track_affinity("ulp_youtube", "a1") == 1.0
    assert get_track_affinity("missing-source", "hist") == 0.0
    assert TRACK_CHANNEL_AFFINITY["imtgsh"]["hist"] == 1.0


def test_invalid_registry_entry_is_rejected(tmp_path: Path):
    payload = {
        "channels": [{
            "id": "demo",
            "name": "Demo",
            "host": "Demo Host",
            "url": "https://example.test",
            "source_file": "demo",
            "register_tag": "spoken",
            "decolonization_tag": "neutral",
            "quality_tier": 2,
            "language_purity": "vetted",
            "track_affinity": {"hist": 1.2},
            "description": "Demo channel.",
        }],
    }
    path = tmp_path / "channels.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")

    with pytest.raises(ValueError, match=r"track_affinity\['hist'\] must be between 0.0 and 1.0"):
        load_channels(path, reload=True)

"""Spec-facing tests for the external corpus channel registry."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

from wiki.channels import load_channels


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

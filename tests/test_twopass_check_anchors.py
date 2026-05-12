from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK_ANCHORS_PATH = ROOT / "audit" / "twopass-pass2-only-2026-05-13" / "check_anchors.py"


def _load_check_anchors():
    spec = importlib.util.spec_from_file_location("twopass_check_anchors", CHECK_ANCHORS_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_manifest(path: Path, content: str) -> None:
    import hashlib

    path.write_text(
        json.dumps(
            {
                "anchors": [
                    {
                        "id": "uk-ex-1",
                        "kind": "uk-ex",
                        "content": content,
                        "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_compare_anchors_accepts_byte_identical_anchor(tmp_path: Path) -> None:
    check_anchors = _load_check_anchors()
    anchors_json = tmp_path / "anchors.json"
    module = tmp_path / "module.md"
    content = "Спочатку я прокидаюся."
    _write_manifest(anchors_json, content)
    module.write_text(f"<!-- ANCHOR uk-ex-1 -->\n{content}\n", encoding="utf-8")

    result = check_anchors.compare_anchors(anchors_json, module)

    assert result["passed"] is True
    assert result["mismatches"] == []


def test_compare_anchors_rejects_hash_mismatch(tmp_path: Path) -> None:
    check_anchors = _load_check_anchors()
    anchors_json = tmp_path / "anchors.json"
    module = tmp_path / "module.md"
    _write_manifest(anchors_json, "Спочатку я прокидаюся.")
    module.write_text("<!-- ANCHOR uk-ex-1 -->\nСпочатку я прокидаюсь.\n", encoding="utf-8")

    result = check_anchors.compare_anchors(anchors_json, module)

    assert result["passed"] is False
    assert result["mismatches"][0]["id"] == "uk-ex-1"
    assert "-Спочатку я прокидаюся." in result["mismatches"][0]["diff"]

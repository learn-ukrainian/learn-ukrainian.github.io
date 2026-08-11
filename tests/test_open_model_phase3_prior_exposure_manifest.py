import json
import os
import subprocess
from pathlib import Path

import pytest

from scripts.projects.open_model_data import phase3_prior_exposure_manifest as exposure


def _private_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    path.write_text(json.dumps(value), encoding="utf-8")
    os.chmod(path, 0o600)


def _identity(number: int) -> dict[str, str]:
    return {"unit_id": f"unit.{number}", "unit_sha256": f"{number:064x}"}


def test_builds_sorted_deduplicated_text_free_manifest(tmp_path: Path) -> None:
    identity_list = tmp_path / "retired.json"
    packet_dir = tmp_path / "packets"
    output = tmp_path / "private" / "exposed.jsonl"
    _private_json(identity_list, [_identity(1), _identity(2)])
    _private_json(
        packet_dir / "packet-0001.json",
        {"row_count": 2, "rows": [{**_identity(2), "source_text": "secret"}, _identity(3)]},
    )

    receipt = exposure.build(
        identity_lists=[identity_list], packet_dirs=[packet_dir], output=output
    )

    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert rows == [_identity(1), _identity(2), _identity(3)]
    assert receipt["unique_identity_count"] == 3
    assert receipt["text_free"] is True
    assert "secret" not in output.read_text(encoding="utf-8")
    assert output.stat().st_mode & 0o777 == 0o600
    assert output.parent.stat().st_mode & 0o777 == 0o700


def test_rejects_non_private_input(tmp_path: Path) -> None:
    source = tmp_path / "retired.json"
    _private_json(source, [_identity(1)])
    # Intentional world-readable input for the private-mode gate (avoid Python chmod for CodeQL #353).
    subprocess.run(["chmod", "644", str(source)], check=True, timeout=30)

    with pytest.raises(exposure.PriorExposureError, match="0600"):
        exposure.build(identity_lists=[source], packet_dirs=[], output=tmp_path / "out.jsonl")


def test_rejects_duplicate_inside_packet_directory(tmp_path: Path) -> None:
    packet_dir = tmp_path / "packets"
    _private_json(packet_dir / "packet-0001.json", {"row_count": 1, "rows": [_identity(1)]})
    _private_json(packet_dir / "packet-0002.json", {"row_count": 1, "rows": [_identity(1)]})

    with pytest.raises(exposure.PriorExposureError, match="across retired packets"):
        exposure.build(identity_lists=[], packet_dirs=[packet_dir], output=tmp_path / "out.jsonl")


def test_rejects_output_inside_an_input(tmp_path: Path) -> None:
    packet_dir = tmp_path / "packets"
    _private_json(packet_dir / "packet-0001.json", {"row_count": 1, "rows": [_identity(1)]})

    with pytest.raises(exposure.PriorExposureError, match="inside an exposure source"):
        exposure.build(
            identity_lists=[], packet_dirs=[packet_dir], output=packet_dir / "exposed.jsonl"
        )

from __future__ import annotations

import subprocess
from pathlib import Path

from scripts.storage.consumers import KNOWN_BASES, scan_inventory, write_inventory


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, timeout=30)


def test_scan_includes_literal_artifacts_and_known_dynamic_bases(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    table = tmp_path / "registry/artifacts/classification-v1.tsv"
    table.parent.mkdir(parents=True)
    table.write_text(
        "path\tmode\tblob\tsize\tclass\tgroup\treason\tjudgment\n"
        "data/registry.yaml\t100644\tx\t1\tA\troot\tr\trule\n"
        "data/translations/example.json\t100644\tx\t1\tK\ttranslations\tr\trule\n"
        "data/lexicon/candidates.json\t100644\tx\t1\tA\tlexicon_candidates\tr\trule\n",
        encoding="utf-8",
    )
    source = tmp_path / "scripts/reader.py"
    source.parent.mkdir()
    source.write_text(
        'from pathlib import Path\nPATH = Path("data/registry.yaml")\nTRANSLATIONS = "data/translations/example.json"\nBASE = DATA_ROOT\n',
        encoding="utf-8",
    )
    _git(tmp_path, "add", "registry/artifacts/classification-v1.tsv", "scripts/reader.py")

    rows = scan_inventory(tmp_path, phase="P1", table=table)
    assert rows == [
        {"artifact": "base:DATA_ROOT", "consumer": "scripts/reader.py", "check": ""},
        {"artifact": "data/registry.yaml", "consumer": "scripts/reader.py", "check": ""},
        {"artifact": "data/translations/example.json", "consumer": "scripts/reader.py", "check": ""},
    ]
    output = tmp_path / "inventory.tsv"
    write_inventory(output, rows)
    assert output.read_text(encoding="utf-8").splitlines() == [
        '"artifact"\t"consumer"\t"check"',
        '"base:DATA_ROOT"\t"scripts/reader.py"\t""',
        '"data/registry.yaml"\t"scripts/reader.py"\t""',
        '"data/translations/example.json"\t"scripts/reader.py"\t""',
    ]
    assert "DATA_ROOT" in KNOWN_BASES

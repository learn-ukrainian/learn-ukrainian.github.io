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
        {"artifact": "base:phase-directory-prefix", "consumer": "scripts/reader.py", "check": ""},
        {"artifact": "data/registry.yaml", "consumer": "scripts/reader.py", "check": ""},
        {"artifact": "data/translations/example.json", "consumer": "scripts/reader.py", "check": ""},
    ]
    output = tmp_path / "inventory.tsv"
    write_inventory(output, rows)
    assert output.read_text(encoding="utf-8").splitlines() == [
        '"artifact"\t"consumer"\t"check"',
        '"base:DATA_ROOT"\t"scripts/reader.py"\t""',
        '"base:phase-directory-prefix"\t"scripts/reader.py"\t""',
        '"data/registry.yaml"\t"scripts/reader.py"\t""',
        '"data/translations/example.json"\t"scripts/reader.py"\t""',
    ]
    assert "DATA_ROOT" in KNOWN_BASES


def test_p3_scan_finds_reviewed_dynamic_consumers() -> None:
    root = Path(__file__).resolve().parents[2]
    names = {row["consumer"] for row in scan_inventory(root, phase="P3")}
    for filename in (
        "judge_eval_seat.py",
        "package_unified_dataset.py",
        "model_view_exporter.py",
        "v4_mine_stem_controls.py",
        "phase3_textbook_nonhit.py",
        "v6_mine_general_assistant_textbooks.py",
        "v5_mine_dialect_corpus.py",
    ):
        assert f"scripts/projects/open_model_data/{filename}" in names


def test_p3_scan_finds_segment_joins_and_paths_import(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    table = tmp_path / "registry/artifacts/classification-v1.tsv"
    table.parent.mkdir(parents=True)
    table.write_text(
        "path\tclass\tgroup\ndata/projects/open_model_data/contracts/schema.json\tA\tcontracts\n",
        encoding="utf-8",
    )
    source = tmp_path / "scripts/reader.py"
    source.parent.mkdir()
    source.write_text(
        "from scripts.projects.open_model_data.paths import CONTRACTS_DIR\n"
        'A = Path("data") / "projects" / "open_model_data" / "contracts"\n'
        'B = os.path.join("data", "projects", "open_model_data", "release")\n',
        encoding="utf-8",
    )
    _git(tmp_path, "add", "registry/artifacts/classification-v1.tsv", "scripts/reader.py")
    labels = {row["artifact"] for row in scan_inventory(tmp_path, phase="P3", table=table)}
    assert {"base:data-segment-join", "base:open_model_data.paths"} <= labels


def test_scan_finds_moved_registry_twin_of_kept_paths(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    table = tmp_path / "registry/artifacts/classification-v1.tsv"
    table.parent.mkdir(parents=True)
    table.write_text(
        "path\tmode\tblob\tsize\tclass\tgroup\treason\tjudgment\n"
        "data/translations/example.json\t100644\tx\t1\tK\ttranslations\tr\trule\n"
        "data/raw/source.html\t100644\tx\t1\tA\traw_source\tr\trule\n",
        encoding="utf-8",
    )
    source = tmp_path / "scripts/reader.py"
    source.parent.mkdir()
    source.write_text(
        'TRANSLATIONS = ROOT / "registry" / "translations" / "example.json"\nRAW = "registry/raw/source.html"\n',
        encoding="utf-8",
    )
    _git(tmp_path, "add", "registry/artifacts/classification-v1.tsv", "scripts/reader.py")
    rows = scan_inventory(tmp_path, phase="P1", table=table)
    assert {"artifact": "base:data-segment-join", "consumer": "scripts/reader.py", "check": ""} in rows
    source.write_text(
        'TRANSLATIONS = "registry/translations/example.json"\nRAW = "registry/raw/source.html"\n', encoding="utf-8"
    )
    labels = {row["artifact"] for row in scan_inventory(tmp_path, phase="P1", table=table)}
    # The K path is reported under its table path; an A path never moved, so its registry twin is not a hit.
    assert "data/translations/example.json" in labels
    assert "data/raw/source.html" not in labels


def test_scan_finds_quoted_data_prefix_classifiers(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    table = tmp_path / "registry/artifacts/classification-v1.tsv"
    table.parent.mkdir(parents=True)
    table.write_text("path\tclass\tgroup\ndata/registry.yaml\tK\troot\n", encoding="utf-8")
    source = tmp_path / "scripts/classify.py"
    source.parent.mkdir()
    source.write_text('CONTENT_PATH_PREFIXES = ("curriculum/", "data/")\n', encoding="utf-8")
    _git(tmp_path, "add", "registry/artifacts/classification-v1.tsv", "scripts/classify.py")
    rows = scan_inventory(tmp_path, phase="P1", table=table)
    assert {"artifact": "base:data-prefix", "consumer": "scripts/classify.py", "check": ""} in rows


def test_scan_finds_artifact_directory_joins_and_imported_path_constants(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    table = tmp_path / "registry/artifacts/classification-v1.tsv"
    table.parent.mkdir(parents=True)
    table.write_text(
        "path\tmode\tblob\tsize\tclass\tgroup\treason\tjudgment\n"
        "data/audit/map.json\t100644\tx\t1\tA\tsnapshots\tr\trule\n",
        encoding="utf-8",
    )
    files = {
        # Joins the artifact's directory, so the full path never appears as a literal.
        "scripts/pkg/writer.py": 'from pathlib import Path\nROOT = Path(".")\nOUT = ROOT / "data" / "audit" / "report.md"\n',
        # Defines a path constant through another constant, then a reader imports it.
        "scripts/pkg/config.py": 'from pathlib import Path\nBASE = Path(".") / "data" / "audit"\nMAP_PATH = BASE / "map.json"\nOTHER = 3\n',
        "scripts/pkg/reader.py": "from pkg.config import MAP_PATH, OTHER\n\nprint(MAP_PATH, OTHER)\n",
        "scripts/pkg/unrelated.py": "from pkg.config import OTHER\n",
    }
    for name, content in files.items():
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text(content, encoding="utf-8")
    _git(tmp_path, "add", ".")

    rows = {(row["artifact"], row["consumer"]) for row in scan_inventory(tmp_path, phase="P1", table=table)}
    assert ("base:data-segment-join", "scripts/pkg/writer.py") in rows
    assert ("base:import:scripts.pkg.config:MAP_PATH", "scripts/pkg/reader.py") in rows
    assert not any(consumer == "scripts/pkg/unrelated.py" for _, consumer in rows)

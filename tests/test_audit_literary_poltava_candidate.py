import importlib.util
import json
import sqlite3
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts/dataset/audit_literary_poltava_candidate.py"
SPEC = importlib.util.spec_from_file_location("literary_audit", SCRIPT)
AUDIT = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(AUDIT)


def make_database(path: Path) -> None:
    connection = sqlite3.connect(path)
    connection.execute(
        "CREATE TABLE literary_texts (id INTEGER PRIMARY KEY, chunk_id TEXT, source_file TEXT, work_id TEXT, genre TEXT, source_url TEXT, author TEXT, work TEXT, year INTEGER)"
    )
    connection.executemany(
        "INSERT INTO literary_texts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (1, "c1", "scan-a.pdf", "w1", "poetry", None, "Автор", "Твір", 1900),
            (2, "c2", "scan-a.pdf", "w1", "poetry", None, "Автор", "Твір", 1900),
            (3, "c3", "scan-b.pdf", "w2", "prose", "https://example.invalid/catalog", "Інший", "Інший твір", 1950),
            (4, "c4", "scan-c.pdf", "w3", "prose", None, "Третій", "Весна", 1960),
            (5, "c5", "scan-c.pdf", "w3", "prose", None, "Третій", "Весна", 1960),
        ],
    )
    connection.commit()
    connection.close()


def write_jsonl(path: Path) -> None:
    rows = [
        {
            "id": "lit-1",
            "author": "Автор",
            "work": "Твір",
            "year": 1900,
            "language_period": "modern",
            "dialect_standard": "candidate",
            "text": "Один два три чотири п'ять шість.",
        },
        {
            "id": "lit-2",
            "author": "Автор",
            "work": "Твір",
            "year": 1900,
            "language_period": "modern",
            "dialect_standard": "candidate",
            "text": "Один, два три чотири п'ять шість!",
        },
        {
            "id": "lit-3",
            "author": "Інший",
            "work": "Інший твір",
            "year": 1950,
            "language_period": "modern",
            "dialect_standard": "candidate",
            "text": "ы явний сигнал.",
        },
        {
            "id": "lit-4",
            "author": "Третій",
            "work": "Весна",
            "year": 1960,
            "language_period": "modern",
            "dialect_standard": "candidate",
            "text": "Весна несе тепло до тихого саду де птахи співають над річкою і зелені дерева шумлять увечері щодня.",
        },
        {
            "id": "lit-5",
            "author": "Третій",
            "work": "Весна",
            "year": 1960,
            "language_period": "modern",
            "dialect_standard": "candidate",
            "text": "Весна несе тепло до тихого саду де птахи співають над річкою і зелені дерева шумлять увечері щодня разом.",
        },
    ]
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def test_audit_is_deterministic_fail_closed_and_covers_all_rows(tmp_path: Path) -> None:
    dataset, database = tmp_path / "candidate.jsonl", tmp_path / "sources.db"
    write_jsonl(dataset)
    make_database(database)
    evaluation = tmp_path / "evaluation.jsonl"
    evaluation.write_text(
        json.dumps(
            {
                "record_layouts": {
                    "item": ["id", "source", "references"],
                    "reference": ["annotator_index", "target"],
                },
                "items": [
                    [
                        "eval-1",
                        "Один два три чотири п'ять шість",
                        [["0", "Інший нормативний варіант"]],
                    ]
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    output, report = tmp_path / "evidence", tmp_path / "report.md"

    first = AUDIT.audit(dataset, database, output, report, [evaluation])
    receipts_before = {path.name: path.read_bytes() for path in output.iterdir()}
    second = AUDIT.audit(dataset, database, output, report, [evaluation])

    assert first == second
    assert first["collection_verdict"] == "rebuild_required"
    assert first["all_records_have_unknown_rights"] is True
    assert first["duplicate_counts"]["exact_clusters"] == 1
    assert first["duplicate_counts"]["near_clusters"] == 1
    assert first["duplicate_counts"]["near_records"] == 2
    assert first["evaluation_overlap_counts"] == {"exact": 2}
    assert first["evaluation_inventories"][0]["text_count"] == 2
    assert receipts_before == {path.name: path.read_bytes() for path in output.iterdir()}
    input_contract = json.loads((output / "input_contract.json").read_text(encoding="utf-8"))
    assert input_contract["sources_db"]["acquisition_provenance"] == "unknown_fail_closed"
    assert input_contract["sources_db"]["selected_row_count"] == 5
    dispositions = [
        json.loads(line) for line in (output / "record_dispositions.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [row["id"] for row in dispositions] == ["lit-1", "lit-2", "lit-3", "lit-4", "lit-5"]
    assert dispositions[0]["disposition"] == "excluded_evaluation_overlap"
    assert "russian_only_letter_signal" in dispositions[2]["anomaly_signals"]


def test_empty_similarity_and_ukrainian_cyrillic_signal_are_fail_safe() -> None:
    assert AUDIT.jaccard(set(), set()) == 0.0
    flags = AUDIT.anomaly_flags({"text": "Її Єва ґречно їде."}, None)
    assert "low_cyrillic_ratio_signal" not in flags

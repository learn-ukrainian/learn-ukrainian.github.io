"""Unit and contract tests for ULDR Phase 3.3 STEM negative controls (#8007)."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.projects.open_model_data.v4_mine_stem_controls import (
    DEFAULT_OUTPUT_DIR,
    DPO_QUOTA,
    SFT_QUOTA,
    SSH_OR_HOST_RE,
    assert_no_corpus_text,
    assert_no_private_host_paths,
    classify_nomenclature,
    classify_obyem,
    classify_rahuvaty,
    classify_semantic_context,
    classify_vidnoshennia,
    is_train_textbook,
    load_heldout_chunk_ids,
    main,
    mine_controls,
    ocr_sanity_check,
    public_relpath,
    style_guide_collision_check,
    verify_artifacts,
)

CONTRACTS_DIR = REPO_ROOT / "data" / "projects" / "open_model_data" / "contracts"
RECEIPT_SCHEMA_PATH = CONTRACTS_DIR / "v1_stem_controls_receipt.schema.json"


def _train_title(prefix: str, start: int = 0) -> str:
    for offset in range(start, start + 80):
        title = f"{prefix} {offset}"
        if is_train_textbook("Істер", title):
            return title
    raise AssertionError(f"could not find a train title for {prefix}")


def _heldout_title(prefix: str) -> str:
    for offset in range(200, 280):
        title = f"{prefix} {offset}"
        if not is_train_textbook("Істер", title):
            return title
    raise AssertionError(f"could not find a held-out title for {prefix}")


def _seed_vesum(conn: sqlite3.Connection, texts: list[str]) -> None:
    conn.execute("CREATE TABLE forms (lemma TEXT, word_form TEXT, tags TEXT)")
    conn.execute("CREATE TABLE forms_all (lemma TEXT, word_form TEXT, tags TEXT)")
    extra = [
        "об'єм",
        "обсяг",
        "рахувати",
        "порахувати",
        "порахуй",
        "обчислити",
        "обчислювати",
        "вважати",
        "відношення",
        "ставлення",
        "стосунки",
        "сірчана",
        "кислота",
        "вуглекислий",
        "газ",
        "науковий",
        "термін",
        "піраміди",
        "куба",
        "конуса",
        "розчину",
        "яблука",
        "дні",
        "заряду",
        "маси",
    ]
    tokens: set[str] = set(extra)
    for text in texts:
        for tok in text.replace(".", " ").replace(",", " ").split():
            clean = tok.strip("«»\"'’ʼ-").casefold()
            if clean:
                tokens.add(clean)
    for tok in sorted(tokens):
        conn.execute("INSERT INTO forms (lemma, word_form, tags) VALUES (?, ?, ?)", (tok, tok, "n:inanim"))
        conn.execute("INSERT INTO forms_all (lemma, word_form, tags) VALUES (?, ?, ?)", (tok, tok, "n:inanim"))
    conn.commit()


def _build_fixture_dbs(
    tmp_path: Path,
    *,
    sft_quota: int,
    include_rejects: bool = True,
) -> tuple[Path, Path, Path]:
    sources = tmp_path / "sources.db"
    vesum = tmp_path / "vesum.db"
    heldout = tmp_path / "heldout.jsonl"

    sentences: list[tuple[str, str, str]] = []
    if include_rejects:
        sentences.extend(
            [
                (
                    "informatyka",
                    "stem-abstract-data",
                    "Об'єм даних у файлі становить чотири гігабайти на диску сервера.",
                ),
                (
                    "algebra",
                    "stem-ocr-junk",
                    "Об'¡м ï cubà ÐÐÐ піраміди становить значення у таблиці.",
                ),
                (
                    "algebra",
                    "stem-collision",
                    "Я рахую, що цей інтеграл розв'язано правильно у класі.",
                ),
                (
                    "khimiya",
                    "stem-calque-gas",
                    "Вуглекислий газ виділяється під час реакції в колбі.",
                ),
            ]
        )
    sentences.extend(
        [
            (
                "khimiya",
                "stem-chem-acid",
                "Сірчана кислота реагує з металом у колбі під час лабораторної роботи.",
            ),
            (
                "algebra",
                "stem-count",
                "Порахуй яблука на тарілці та запиши число елементів у зошиті.",
            ),
            (
                "fizyka",
                "stem-ratio",
                "Відношення заряду до маси частинки є сталою фізичною величиною у досліді.",
            ),
            (
                "matematyka",
                "stem-colloquial",
                "Та ну, порахуй-но яблука на парті, гаразд, і запиши дні спостереження.",
            ),
        ]
    )
    solids = ("піраміди", "куба", "конуса", "циліндра", "кулі", "призми")
    for idx in range(sft_quota + 40):
        solid = solids[idx % len(solids)]
        sentences.append(
            (
                "algebra" if idx % 2 == 0 else "heometriya",
                f"stem-alg-{idx:04d}",
                f"Об'єм {solid} становить {idx + 3} кубічних сантиметрів у геометричній задачі {idx}.",
            )
        )

    heldout_chunk = "heldout-reserved-chunk"
    heldout.write_text(
        json.dumps(
            {
                "eval_id": "eval_decolon_9999",
                "source_metadata": {"source": f"textbook:{heldout_chunk}"},
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    sentences.append(
        (
            "algebra",
            heldout_chunk,
            "Об'єм піраміди становить 99 кубічних сантиметрів у геометричній задачі heldout.",
        )
    )

    src = sqlite3.connect(sources)
    src.execute(
        "CREATE TABLE textbooks (id INTEGER PRIMARY KEY, chunk_id TEXT, title TEXT, text TEXT, author_uk TEXT, subject TEXT)"
    )
    src.execute("CREATE TABLE style_guide (id INTEGER PRIMARY KEY, word TEXT, section TEXT, text TEXT, source TEXT)")
    title = _train_title("Алгебра Істера")
    heldout_title = _heldout_title("Геометрія Мерзляка")
    for idx, (subject, chunk_id, text) in enumerate(sentences, 1):
        book_title = heldout_title if chunk_id == heldout_chunk else title
        src.execute(
            "INSERT INTO textbooks (id, chunk_id, title, text, author_uk, subject) VALUES (?, ?, ?, ?, ?, ?)",
            (idx, chunk_id, book_title, text, "Істер", subject),
        )
    src.execute(
        "INSERT INTO style_guide (word, section, text, source) VALUES (?, ?, ?, ?)",
        (
            "об'єм даних",
            "лексика",
            "Неправильно казати «об'єм даних», треба казати «обсяг даних».",
            "style_guide",
        ),
    )
    src.commit()
    src.close()

    texts = [item[2] for item in sentences]
    ves = sqlite3.connect(vesum)
    _seed_vesum(ves, texts)
    ves.close()
    return sources, vesum, heldout


def test_obyem_physical_preserve_and_abstract_correct() -> None:
    physical = classify_obyem("Об'єм піраміди дорівнює об'єму розчину в колбі.")
    assert physical is not None
    assert physical.action == "PRESERVE"
    assert physical.entity_type == "physical_3d_volume"

    abstract = classify_obyem("Об'єм даних і об'єм робіт зросли разом з обсягом інвестицій.")
    assert abstract is not None
    assert abstract.action == "CORRECT"
    assert abstract.replacement == "обсяг"
    assert abstract.entity_type == "abstract_quantity_data_scope"

    mixed = classify_semantic_context("Об'єм куба і об'єм даних записані в таблиці.")
    assert mixed is not None
    assert mixed.action == "CORRECT"


def test_rahuvaty_and_vidnoshennia_sense_split() -> None:
    counting = classify_rahuvaty("Порахуй яблука та дні спостереження в журналі.")
    assert counting is not None and counting.action == "PRESERVE"
    calc = classify_rahuvaty("Порахуй інтеграл і значення виразу за формулою.")
    assert calc is not None and calc.action == "REGISTER" and calc.replacement == "обчислити"
    opinion = classify_rahuvaty("Я рахую, що відповідь правильна.")
    assert opinion is not None and opinion.action == "CORRECT" and opinion.replacement == "вважати"

    ratio = classify_vidnoshennia("Відношення заряду до маси дорівнює a : b.")
    assert ratio is not None and ratio.action == "PRESERVE"
    social = classify_vidnoshennia("Наші відношення до колег стали напруженими.")
    assert social is not None and social.action == "CORRECT"


def test_nomenclature_separates_calque_from_trivial_acid() -> None:
    calque = classify_nomenclature("Вуглекислий газ збирають у колбі.")
    assert calque is not None and calque.action == "CORRECT"
    trivial = classify_nomenclature("Сірчана кислота є традиційною назвою сульфатної.")
    assert trivial is not None and trivial.action == "PRESERVE"
    assert trivial.entity_type == "nomenclature_modernization"


def test_ocr_and_style_guide_filters() -> None:
    assert not ocr_sanity_check("Об'¡м ï cubà ÐÐÐ піраміди").ok
    assert not ocr_sanity_check("коротко").ok
    assert ocr_sanity_check("Об'єм піраміди становить дванадцять кубічних сантиметрів у задачі.").ok
    collision = style_guide_collision_check("Тут об'єм даних перевищує ліміт.", {"об'єм даних"})
    assert not collision.ok


def test_zero_false_preservation_of_abstract_calques() -> None:
    abstracts = [
        "Об'єм даних у сховищі зріс після архівації логів.",
        "Об'єм робіт перевищує кошторис підряду.",
        "Об'єм інвестицій на ринку кредитів збільшився.",
        "Об'єм пам'яті комп'ютера вимірюють у гігабайтах.",
        "Об'єм інформації в тексті не є геометричною величиною.",
    ]
    for sentence in abstracts:
        decision = classify_semantic_context(sentence)
        assert decision is not None, sentence
        assert decision.action != "PRESERVE", sentence


def test_public_relpath_never_returns_metal_root() -> None:
    rendered = public_relpath(DEFAULT_OUTPUT_DIR)
    assert not rendered.startswith("/")
    assert "/home/ops" not in rendered
    assert "ops@" not in rendered


def test_receipt_safety_rejects_host_and_corpus_leaks() -> None:
    with pytest.raises(ValueError):
        assert_no_private_host_paths({"notes": "ran on /home/ops/cluster"})
    with pytest.raises(ValueError):
        assert_no_private_host_paths({"ssh": "Host ops"})
    with pytest.raises(ValueError):
        assert_no_corpus_text({"text": "Об'єм піраміди"})
    clean = {"filename": "stem_controls_receipt.json", "note": "hash-only"}
    assert_no_private_host_paths(clean)
    assert_no_corpus_text(clean)
    assert SSH_OR_HOST_RE.search("user@bastion:repo.git")


def test_mine_exact_production_quotas(tmp_path: Path) -> None:
    sources, vesum, heldout = _build_fixture_dbs(tmp_path, sft_quota=SFT_QUOTA)
    out = tmp_path / "out"
    receipt = mine_controls(
        sources_db=sources,
        vesum_db=vesum,
        output_dir=out,
        sft_quota=SFT_QUOTA,
        dpo_quota=DPO_QUOTA,
        heldout_suite_path=heldout,
    )
    schema = json.loads(RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(receipt)
    assert receipt["yield"]["sft_preserve_controls"] == 1800
    assert receipt["yield"]["dpo_preserve_pairs"] == 900
    assert receipt["cleanliness"]["vesum_verification_rate"] == 1.0
    assert receipt["semantic_typing"]["false_preservation_of_abstract_calques"] == 0
    assert receipt["semantic_typing"]["obyem_preserve"] >= 1
    assert receipt["semantic_typing"]["obyem_correct_excluded"] >= 1
    assert receipt["semantic_typing"]["nomenclature_calque_excluded"] >= 1
    assert receipt["safety_assertions"]["no_corpus_text_emitted"] is True
    assert_no_private_host_paths(receipt)
    assert_no_corpus_text(receipt)

    index_rows = [
        json.loads(line)
        for line in (out / "stem_controls_index.jsonl").read_text(encoding="utf-8").splitlines()
        if line
    ]
    assert len(index_rows) == 1800
    assert all(row["action"] == "PRESERVE" and row["vesum_attested"] for row in index_rows)
    assert all("heldout-reserved-chunk" != row["chunk_id"] for row in index_rows)
    assert all(row["entity_type"] != "abstract_quantity_data_scope" for row in index_rows)
    for row in index_rows:
        assert_no_corpus_text(row)

    sft = [
        json.loads(line)
        for line in (out / "stem_preserve_sft_controls.jsonl").read_text(encoding="utf-8").splitlines()
        if line
    ]
    dpo = [
        json.loads(line)
        for line in (out / "stem_preserve_dpo_pairs.jsonl").read_text(encoding="utf-8").splitlines()
        if line
    ]
    assert len(sft) == 1800
    assert len(dpo) == 900
    assert all(row["is_calque_or_russianism"] is False for row in sft)
    assert all(item["is_standard_attested"] for row in sft for item in row["vesum_attestation"] if item["lemma"] == row["target_term"] or row["target_term"] == "науковий термін")
    assert all(row["metadata"]["vesum_verified"] for row in dpo)
    dumped = json.dumps(receipt, ensure_ascii=False)
    assert "Об'єм піраміди становить" not in dumped
    assert "/home/ops" not in dumped


def test_heldout_chunk_is_excluded(tmp_path: Path) -> None:
    sources, vesum, heldout = _build_fixture_dbs(tmp_path, sft_quota=12)
    out = tmp_path / "small"
    receipt = mine_controls(
        sources_db=sources,
        vesum_db=vesum,
        output_dir=out,
        sft_quota=10,
        dpo_quota=5,
        heldout_suite_path=heldout,
    )
    index_rows = [
        json.loads(line)
        for line in (out / "stem_controls_index.jsonl").read_text(encoding="utf-8").splitlines()
        if line
    ]
    assert {row["chunk_id"] for row in index_rows}.isdisjoint({"heldout-reserved-chunk"})
    assert receipt["source_pool"]["heldout_excluded"] is True


def test_verify_only_and_cli_help(tmp_path: Path) -> None:
    sources, vesum, heldout = _build_fixture_dbs(tmp_path, sft_quota=12)
    out = tmp_path / "cli"
    code = main(
        [
            "--sources-db",
            str(sources),
            "--vesum-db",
            str(vesum),
            "--output-dir",
            str(out),
            "--sft-quota",
            "8",
            "--dpo-quota",
            "4",
        ]
    )
    assert code == 0
    # heldout path is default repo suite here; still enough train sentences
    verify_code = main(["--verify-only", "--output-dir", str(out), "--sft-quota", "8", "--dpo-quota", "4"])
    assert verify_code == 0
    verify_artifacts(out, sft_quota=8, dpo_quota=4)

    help_text = subprocess.check_output(
        [sys.executable, "-m", "scripts.projects.open_model_data.v4_mine_stem_controls", "--help"],
        cwd=REPO_ROOT,
        text=True,
    )
    assert "python -m scripts.projects.open_model_data.v4_mine_stem_controls" in help_text
    assert "$SOURCES_DB" in help_text
    assert "$VESUM_DB" in help_text
    assert "/home/ops" not in help_text
    assert "Host ops" not in help_text
    assert "Exit codes" in help_text
    assert "Outputs" in help_text


def test_module_and_docs_have_no_private_host_paths() -> None:
    paths = [
        REPO_ROOT / "scripts/projects/open_model_data/v4_mine_stem_controls.py",
        REPO_ROOT / "docs/projects/open-model-data/PHASE_3_3_STEM_NEGATIVE_CONTROLS.md",
        REPO_ROOT / "docs/SCRIPTS.md",
    ]
    needle = "/home/" + "ops"
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert needle not in text
        assert "Host ops" not in text
        assert "ops@" not in text


def test_load_heldout_chunk_ids_from_phase3() -> None:
    ids = load_heldout_chunk_ids()
    if not ids:
        pytest.skip("Phase 3.0 held-out suite missing")
    assert any(item.startswith("1-klas") or "klas" in item for item in ids)

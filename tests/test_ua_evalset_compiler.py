"""Unit test suite for Ukrainian Calque + Grammar Evalset Compiler (#5608 / #2156)."""

import json
from pathlib import Path

from scripts.projects.ua_eval_harness.compile_evalset import (
    DEFAULT_GOLD_FIXTURE,
    DEFAULT_TAXONOMY_PATH,
    check_heritage_safeguard,
    compile_evalset,
    generate_item_id,
    load_taxonomy,
)


def test_generate_item_id_is_deterministic() -> None:
    id1 = generate_item_id("Я приймаю участь", "приймаю", "F/Calque")
    id2 = generate_item_id("Я приймаю участь", "приймаю", "F/Calque")
    assert id1 == id2
    assert id1.startswith("eval-f_calque-")


def test_load_taxonomy_spec() -> None:
    taxonomy = load_taxonomy(DEFAULT_TAXONOMY_PATH)
    assert taxonomy.get("version") == "1.0.0"
    categories = set(taxonomy.get("categories", {}).keys())
    assert "F/Calque" in categories
    assert "G/Case" in categories
    assert "G/Gender" in categories


def test_heritage_safeguard_regionalism_protection() -> None:
    verdict_reg = check_heritage_safeguard("бутелька", "пляшка")
    assert verdict_reg.is_regionalism is True
    assert verdict_reg.verdict == "heritage_protected"
    assert "heritage_dict" in verdict_reg.authority

    verdict_std = check_heritage_safeguard("уверх", "вгору")
    assert verdict_std.is_regionalism is False
    assert verdict_std.verdict == "cleared"
    assert verdict_std.authority == ["ua-gec"]


def test_compile_evalset_creates_jsonl(tmp_path: Path) -> None:
    output_file = tmp_path / "evalset_test.jsonl"
    res = compile_evalset(gold_path=DEFAULT_GOLD_FIXTURE, output_path=output_file)
    assert res == 0
    assert output_file.exists()

    lines = output_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 52

    first_item = json.loads(lines[0])
    assert first_item["lang"] == "uk"
    assert "edits" in first_item
    assert "dialect" in first_item
    assert "provenance" in first_item
    assert first_item["provenance"]["taxonomy_version"] == "1.0.0"
    assert first_item["edits"][0]["category"] in ("F/Calque", "G/Case", "G/Gender")

"""convert-set: v2 JSON Lines -> harness set (#9623). Synthetic data only."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Any

import pytest

import scripts.eval.uk_preamble.__main__ as cli
from scripts.eval.uk_preamble.common import HarnessError, sha256_file
from scripts.eval.uk_preamble.convert import ERROR_TYPE_MAP, convert_source
from scripts.eval.uk_preamble.dataset import load_set

SENTENCE = "Вчора я приймав участь у зборах, а Галя принесла пляцки."


def _at(text: str, fragment: str) -> tuple[int, int]:
    start = text.index(fragment)
    return start, start + len(fragment)


def v2_review(item_id: str, source_type: str = "lexical_russianism", **extra: Any) -> dict[str, Any]:
    start, end = _at(SENTENCE, "приймав участь")
    p_start, p_end = _at(SENTENCE, "пляцки")
    return {
        "id": item_id,
        "kind": "review",
        "level": "B1",
        "text": SENTENCE,
        "errors": [
            {
                "span": "приймав участь",
                "type": source_type,
                "corrections": ["брав участь", "бере участь"],
                "origin": "synthetic",
                "evidence": ["e"],
                "start": start,
                "end": end,
                "subtype": "s",
                "stratum": "t",
            }
        ],
        "correct_spans": [
            {
                "span": "пляцки",
                "stratum": "regional",
                "why_tricky": "w",
                "evidence": ["e"],
                "start": p_start,
                "end": p_end,
            }
        ],
        **extra,
    }


def v2_writing(item_id: str, level: str, **extra: Any) -> dict[str, Any]:
    return {
        "id": item_id,
        "kind": "writing",
        "task": "Опишіть свій вихідний день.",
        "level": level,
        "topic": "вихідний",
        "genre": "лист",
        "length_words": {"min": 80, "max": 140},
        "register": "неформальний",
        **extra,
    }


def full_v2() -> list[dict[str, Any]]:
    """Every mapped type, four items each: 64 errors and 64 protected spans, writing at A2-C1."""
    lines = [v2_review(f"R{i:02d}-{n}", source) for i, source in enumerate(ERROR_TYPE_MAP) for n in range(4)]
    lines += [v2_writing(f"W-{level}", level) for level in ("A2", "B1", "B2", "C1")]
    return lines


def write_jsonl(path: Path, lines: list[dict[str, Any]]) -> Path:
    path.write_text("".join(json.dumps(line, ensure_ascii=False) + "\n" for line in lines), encoding="utf-8")
    return path


def convert(lines: list[dict[str, Any]], set_id: str = "synthetic-v1"):
    raw = "".join(json.dumps(line, ensure_ascii=False) + "\n" for line in lines).encode("utf-8")
    return convert_source(raw, set_id)


def run_cli(outside_dir: Path, lines: list[dict[str, Any]], capsys, out_name: str = "set.json"):
    source = write_jsonl(outside_dir / "set-v2.jsonl", lines)
    output = outside_dir / out_name
    code = cli.main(["convert-set", "--input", str(source), "--output", str(output), "--set-id", "synthetic-v1"])
    captured = capsys.readouterr()
    return code, captured, source, output


# ---------------------------------------------------------------- mapping


def test_mapping_table_covers_the_sixteen_source_types_onto_known_labels():
    from scripts.eval.uk_preamble.common import ERROR_TYPES

    assert len(ERROR_TYPE_MAP) == 16
    assert set(ERROR_TYPE_MAP.values()) <= set(ERROR_TYPES)


@pytest.mark.parametrize(("source", "target"), list(ERROR_TYPE_MAP.items()))
def test_each_source_type_maps_to_its_harness_label(source: str, target: str):
    data = convert([v2_review("R1", source)]).data
    assert data["review"][0]["errors"][0]["error_type"] == target


def test_expected_mapping_is_exactly_the_specified_one():
    assert ERROR_TYPE_MAP == {
        "spelling_pravopys_2019": "spelling",
        "agreement": "agreement",
        "numeral_noun": "numeral-noun",
        "vocative": "vocative",
        "aspect": "aspect",
        "case_government": "case-government",
        "prepositional_calques": "prepositional-calque",
        "active_participle_calques": "active-participle-calque",
        "passive_reflexive_calques": "passive-reflexive-calque",
        "bureaucratic_noun_chains": "noun-chain",
        "lexical_russianism": "lexical-russianism",
        "lexical_calque": "other",
        "surzhyk": "surzhyk",
        "paronyms": "paronym",
        "english_calques": "english-calque",
        "semantically_wrong_combinations": "wrong-combination",
    }


def test_review_fields_ids_and_order_are_converted():
    line = v2_review("R7")
    line["errors"].append(
        {**line["errors"][0], "type": "surzhyk", "corrections": ["x"], "start": 0, "end": 0, "span": ""}
    )
    line["correct_spans"].append({**line["correct_spans"][0], "stratum": "heritage"})
    item = convert([line, v2_review("R8")]).data["review"][0]
    assert [e["id"] for e in item["errors"]] == ["R7-e1", "R7-e2"]
    assert [e["error_type"] for e in item["errors"]] == ["lexical-russianism", "surzhyk"]
    assert item["errors"][0]["accepted"] == ["брав участь", "бере участь"]
    assert item["errors"][0]["origin"] == "synthetic"
    assert [p["id"] for p in item["protected"]] == ["R7-p1", "R7-p2"]
    assert [p["kind"] for p in item["protected"]] == ["regional", "heritage"]
    assert set(item) == {"id", "text", "errors", "protected"}
    assert set(item["errors"][0]) == {"id", "start", "end", "span", "error_type", "accepted", "origin"}
    assert set(item["protected"][0]) == {"id", "start", "end", "span", "kind"}


def test_set_id_and_item_order_follow_the_source():
    data = convert([v2_writing("W1", "B1"), v2_review("R1"), v2_review("R0"), v2_writing("W0", "A2")], "my-set").data
    assert data["set_id"] == "my-set"
    assert [i["id"] for i in data["review"]] == ["R1", "R0"]
    assert [i["id"] for i in data["writing"]] == ["W1", "W0"]


# ---------------------------------------------------------------- refusals


def test_unknown_type_is_refused_with_line_item_and_rule_only():
    result = convert([v2_review("R1"), v2_review("R2", "not_a_type")])
    assert result.data is None
    assert [(p.line, p.item, p.rule) for p in result.problems] == [(2, "R2", "error-type-unknown")]


@pytest.mark.parametrize(
    ("mutate", "rule"),
    [
        (lambda e: e.pop("origin"), "error-fields"),
        (lambda e: e.pop("start"), "error-fields"),
        (lambda e: e.update(corrections="брав участь"), "error-corrections"),
        (lambda e: e.update(type=None), "error-type-unknown"),
        (lambda e: e.update(type=["agreement"]), "error-type-unknown"),
    ],
)
def test_malformed_source_error_is_refused(mutate, rule):
    line = v2_review("R1")
    mutate(line["errors"][0])
    assert [p.rule for p in convert([line]).problems] == [rule]


def test_other_malformed_source_lines_are_refused():
    bad_span = v2_review("R3")
    del bad_span["correct_spans"][0]["stratum"]
    no_lists = v2_review("R4")
    del no_lists["errors"]
    result = convert(
        [
            {"id": "X1", "kind": "essay"},
            {"kind": "review"},
            bad_span,
            no_lists,
            v2_writing("W1", "B1", length_words=None),
        ]
    )
    assert result.data is None
    assert {(p.item, p.rule) for p in result.problems} == {
        ("X1", "item-kind-unknown"),
        (None, "item-id"),
        ("R3", "correct-span-fields"),
        ("R4", "errors-not-list"),
        ("W1", "writing-length-words"),
    }


def test_invalid_json_and_invalid_utf8_are_refused():
    assert [(p.line, p.rule) for p in convert_source(b'{"id": "R1"\n', "s").problems] == [(1, "json-syntax")]
    with pytest.raises(HarnessError, match="UTF-8"):
        convert_source(b"\xff\xfe\n", "s")


def test_refusal_writes_nothing_and_exits_2_without_text(outside_dir: Path, capsys):
    code, captured, _, output = run_cli(outside_dir, [v2_review("R1", "bogus")], capsys)
    assert code == 2
    assert not output.exists()
    assert "line 1 item R1: error-type-unknown" in captured.err
    assert "приймав" not in captured.err + captured.out


# ---------------------------------------------------------------- offsets and text preserved


def test_offsets_spans_and_text_are_preserved_byte_for_byte():
    tricky = "Він сказав: «Привіт»  і написав ʼп’ятниця — слово ́ ."  # U+2028 raw inside a JSON string
    start, end = _at(tricky, "п’ятниця")
    line = v2_review("R1")
    line["text"] = tricky
    line["errors"] = [{**line["errors"][0], "span": "п’ятниця", "start": start, "end": end}]
    line["correct_spans"] = []
    item = convert([line]).data["review"][0]
    assert item["text"].encode("utf-8") == tricky.encode("utf-8")
    error = item["errors"][0]
    assert (error["start"], error["end"], error["span"]) == (start, end, "п’ятниця")
    assert item["text"][error["start"] : error["end"]] == error["span"]


def test_wrong_offsets_are_copied_not_repaired_and_reported_by_validation(outside_dir: Path, capsys):
    lines = full_v2()
    lines[0]["errors"][0]["start"] += 1  # span no longer equals text[start:end]
    code, _, _, output = run_cli(outside_dir, lines, capsys)
    written = json.loads(output.read_text(encoding="utf-8"))
    assert written["review"][0]["errors"][0]["start"] == lines[0]["errors"][0]["start"]
    assert code == 1


def test_lf_only_line_splitting_keeps_line_separator_characters_inside_strings():
    line = v2_review("R1")
    line["text"] = "Перший рядок"
    line["errors"], line["correct_spans"] = [], []
    raw = (json.dumps(line, ensure_ascii=False) + "\n\n").encode("utf-8")
    assert convert_source(raw, "s").data["review"][0]["text"] == "Перший рядок"


# ---------------------------------------------------------------- writing


def test_writing_appends_topic_genre_and_register_in_one_sentence():
    task = convert([v2_writing("W1", "B2")]).data["writing"][0]
    assert task == {
        "id": "W1",
        "level": "B2",
        "instruction": "Опишіть свій вихідний день. Тема: вихідний; жанр: лист; регістр: неформальний.",
        "min_words": 80,
        "max_words": 140,
    }


def test_writing_without_topic_genre_register_keeps_the_task_verbatim():
    line = v2_writing("W1", "A2")
    for key in ("topic", "genre", "register"):
        del line[key]
    line["topic"] = "  "
    assert convert([line]).data["writing"][0]["instruction"] == "Опишіть свій вихідний день."


def test_writing_with_only_some_metadata_appends_only_those():
    line = v2_writing("W1", "A2")
    del line["topic"], line["genre"]
    assert convert([line]).data["writing"][0]["instruction"].endswith("день. регістр: неформальний.")


# ---------------------------------------------------------------- end to end


def test_full_set_converts_validates_and_loads_through_the_harness(outside_dir: Path, capsys):
    code, captured, source, output = run_cli(outside_dir, full_v2(), capsys)
    report = json.loads(captured.out)
    assert code == 0, captured
    assert report["valid"] is True and report["problems"] == [] and report["protocol_shortfalls"] == []
    assert report["errors_by_type"] == {target: 4 for target in sorted(ERROR_TYPE_MAP.values())}
    assert report["protected_by_kind"] == {"regional": 64}
    assert report["items"] == {"review": 64, "writing": 4}
    assert report["input_sha256"] == sha256_file(source)
    assert report["output_sha256"] == sha256_file(output)
    eval_set = load_set(output)
    assert eval_set.set_id == "synthetic-v1"
    assert (eval_set.error_count, eval_set.protected_count) == (64, 64)
    assert "приймав" not in captured.out


def test_output_is_owner_only(outside_dir: Path, capsys):
    _, _, _, output = run_cli(outside_dir, full_v2(), capsys)
    assert stat.S_IMODE(os.stat(output).st_mode) == 0o600


def test_validation_failure_is_written_reported_by_id_and_rule_and_exits_1(outside_dir: Path, capsys):
    lines = full_v2()
    lines[3]["errors"][0]["span"] = "приймав УЧАСТЬ"  # span != text[start:end]
    lines[5]["correct_spans"][0]["start"] = lines[5]["errors"][0]["start"]  # protected overlaps an error
    lines[5]["correct_spans"][0]["end"] = lines[5]["errors"][0]["end"]
    lines[5]["correct_spans"][0]["span"] = lines[5]["errors"][0]["span"]
    lines[6]["errors"][0]["corrections"] = ["приймав участь"]  # accepted form equals the seed
    code, captured, _, output = run_cli(outside_dir, lines, capsys)
    report = json.loads(captured.out)
    assert code == 1
    assert output.is_file()
    assert report["valid"] is False
    assert report["problems"] == [
        {"item": "R00-3", "rule": "span-text-mismatch"},
        {"item": "R01-1", "rule": "error-overlaps-protected"},
        {"item": "R01-2", "rule": "accepted-form-equals-seed"},
    ]
    assert "приймав" not in captured.out + captured.err


def test_protocol_minimums_are_enforced_and_reported(outside_dir: Path, capsys):
    code, captured, _, _ = run_cli(outside_dir, [v2_review("R1"), v2_writing("W1", "B1")], capsys)
    report = json.loads(captured.out)
    assert code == 1 and report["valid"] is False and report["problems"] == []
    assert any("seeded errors" in s for s in report["protocol_shortfalls"])
    assert any("writing levels missing" in s for s in report["protocol_shortfalls"])


def test_duplicate_ids_are_reported_as_a_problem(outside_dir: Path, capsys):
    code, captured, _, _ = run_cli(outside_dir, [v2_review("R1"), v2_review("R1")], capsys)
    assert code == 1
    assert {"item": "R1", "rule": "duplicate-id"} in json.loads(captured.out)["problems"]


# ---------------------------------------------------------------- containment and usage


def test_output_inside_a_work_tree_is_refused_before_anything_is_written(outside_dir: Path, capsys):
    source = write_jsonl(outside_dir / "set-v2.jsonl", full_v2())
    repo = Path(__file__).resolve().parents[2]
    target = repo / "scratch-converted-set.json"
    code = cli.main(["convert-set", "--input", str(source), "--output", str(target), "--set-id", "s"])
    assert code == 2
    assert "inside the Git work tree" in capsys.readouterr().err
    assert not target.exists()


def test_output_symlinked_into_a_work_tree_is_refused(outside_dir: Path, capsys):
    source = write_jsonl(outside_dir / "set-v2.jsonl", full_v2())
    repo = Path(__file__).resolve().parents[2]
    link = outside_dir / "link"
    link.symlink_to(repo, target_is_directory=True)
    code = cli.main(["convert-set", "--input", str(source), "--output", str(link / "out.json"), "--set-id", "s"])
    assert code == 2
    assert not (repo / "out.json").exists()


def test_output_must_differ_from_input(outside_dir: Path, capsys):
    source = write_jsonl(outside_dir / "set-v2.jsonl", full_v2())
    before = sha256_file(source)
    assert cli.main(["convert-set", "--input", str(source), "--output", str(source), "--set-id", "s"]) == 2
    assert sha256_file(source) == before


def test_missing_input_and_blank_set_id_are_errors(outside_dir: Path, capsys):
    out = outside_dir / "o.json"
    assert cli.main(["convert-set", "--input", str(outside_dir / "nope"), "--output", str(out), "--set-id", "s"]) == 2
    source = write_jsonl(outside_dir / "in.jsonl", full_v2())
    assert cli.main(["convert-set", "--input", str(source), "--output", str(out), "--set-id", " "]) == 2
    assert not out.exists()


def test_missing_arguments_exit_2_and_help_documents_the_command(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["convert-set", "--input", "x"])
    assert exc.value.code == 2
    capsys.readouterr()
    with pytest.raises(SystemExit) as exc:
        cli.main(["convert-set", "--help"])
    assert exc.value.code == 0
    help_text = capsys.readouterr().out
    for needle in ("--input", "--output", "--set-id", "Examples:", "Exit codes:", "convert-set"):
        assert needle in help_text

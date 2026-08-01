from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import model_ready_view_production as production


def signal(
    start: int,
    end: int,
    *,
    candidate_id: str = "candidate-1",
    category: str = "modern_narration_interference",
    reason: str = "russian_or_mixed_language",
) -> production.MaskSignal:
    return production.MaskSignal(
        start=start,
        end=end,
        candidate_id=candidate_id,
        category=category,
        disposition="mask",
        evidence_grade="unresolved",
        language_identity="russian",
        representation="standard_orthography",
        discourse_role="narration",
        reason=reason,
    )


def test_operational_partition_is_gap_free_and_masks_detector_cores() -> None:
    spans = production.operational_partition("abcdefghij", [signal(2, 5)])

    assert [(row["start"], row["end"]) for row in spans] == [(0, 2), (2, 5), (5, 10)]
    assert [row["modern_loss_action"] for row in spans] == [
        "retain",
        "mask_from_loss",
        "retain",
    ]
    assert "text" not in json.dumps(spans)


def test_operational_partition_resolves_overlap_by_frozen_priority() -> None:
    spans = production.operational_partition(
        "abcdefgh",
        [
            signal(1, 6, candidate_id="quoted", category="russian_quotation", reason="quoted_or_multilingual"),
            signal(3, 5, candidate_id="mixed"),
        ],
    )

    overlap = next(row for row in spans if row["start"] == 3 and row["end"] == 5)
    assert overlap["reason"] == "russian_or_mixed_language"


@pytest.mark.parametrize("start,end", [(-1, 1), (1, 1), (1, 11)])
def test_operational_partition_rejects_invalid_spans(start: int, end: int) -> None:
    with pytest.raises(production.ProductionError, match="outside source text"):
        production.operational_partition("abcdefghij", [signal(start, end)])


def test_merge_masks_coalesces_overlap_and_adjacency() -> None:
    merged, coalesced = production._merge_masks(
        [
            {"start_char": 4, "end_char": 7},
            {"start_char": 1, "end_char": 4},
            {"start_char": 6, "end_char": 9},
        ],
        10,
    )

    assert merged == [(1, 9)]
    assert coalesced == 2


def test_word_assignment_handles_leading_space_and_shared_byte_offsets() -> None:
    text = "Річка Дніпро 𐐷"
    words = list(production.WORD_RE.finditer(text))
    offsets = [(0, 5), (5, 9), (9, 11), (12, 13), (12, 13), (12, 13), (12, 13)]

    assignments, counts = production._assign_tokens_to_words(offsets, words)

    assert assignments == [1, 2]
    assert counts["assigned_non_special_tokens"] == 3
    assert counts["unassigned_non_special_tokens"] == 4


def test_mask_projection_masks_every_byte_fallback_piece() -> None:
    projected = production._project_masks_to_tokens(
        [(0, 1), (0, 1), (0, 1), (0, 1), (1, 2)],
        [(0, 1)],
    )

    assert projected["tokens_overlapping_masks"] == 4
    assert projected["tokens_fully_masked"] == 4
    assert projected["zero_loss_tokens"] == 4


def test_mask_projection_counts_partial_leading_space_overlap() -> None:
    projected = production._project_masks_to_tokens([(5, 9)], [(6, 9)])

    assert projected["tokens_partially_masked"] == 1
    assert projected["zero_loss_tokens"] == 1


def test_token_offsets_must_be_ordered() -> None:
    with pytest.raises(production.ProductionError, match="not ordered"):
        production._project_masks_to_tokens([(2, 3), (1, 2)], [])


def test_verify_words_batches_without_losing_order(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def fake_verify(words: list[str], *, db_path: Path) -> dict[str, list[dict[str, str]]]:
        assert db_path == Path("vesum.db")
        calls.append(words)
        return {word: [{"lemma": word, "pos": "noun", "tags": ""}] for word in words}

    monkeypatch.setattr(production, "verify_words", fake_verify)
    result = production._verify_words_batched(
        ["а", "б", "в", "г", "ґ"],
        db_path=Path("vesum.db"),
        batch_size=2,
    )

    assert calls == [["а", "б"], ["в", "г"], ["ґ"]]
    assert list(result) == ["а", "б", "в", "г", "ґ"]


def test_new_receipt_schemas_are_strict_and_valid() -> None:
    for path in (
        production.PAYLOAD_RECEIPT_SCHEMA,
        production.TOKENIZER_RECEIPT_SCHEMA,
        production.PRODUCTION_RECEIPT_SCHEMA,
    ):
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        assert schema["additionalProperties"] is False


def test_blocked_silver_lane_is_empty_without_human_dependency() -> None:
    lane = production._blocked_lane(739_503)

    assert lane["state"] == "blocked"
    assert lane["eligible"] == lane["emitted"] == 0
    assert lane["blocked"] == 739_503
    assert lane["blocked_reasons"] == ["no_eligible_records"]
    assert lane["artifact"] == {
        "records": 0,
        "bytes": 0,
        "sha256": production.EMPTY_SHA256,
    }


def test_word_regex_keeps_ukrainian_apostrophe_forms() -> None:
    assert [item.group(0) for item in re.finditer(production.WORD_RE, "п'ять п’ять пʼять")] == [
        "п'ять",
        "п’ять",
        "пʼять",
    ]

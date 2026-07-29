import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts/audit"))

from check_teacher_cloze_content import validate_teacher_cloze_content


def _write_gate_files(tmp_path: Path, cards: list[dict], overrides: dict | None = None) -> tuple[Path, Path]:
    data_dir = tmp_path / "site/src/data"
    data_dir.mkdir(parents=True)
    cloze_path = data_dir / "lexicon-teacher-cloze.json"
    overrides_path = data_dir / "lexicon-teacher-cloze-overrides.json"
    cloze_path.write_text(json.dumps({"cloze": cards}, ensure_ascii=False), encoding="utf-8")
    if overrides is not None:
        overrides_path.write_text(json.dumps(overrides), encoding="utf-8")
    return cloze_path, overrides_path


def _valid_card(cloze_id: str = "teacher_cloze_1") -> dict:
    return {
        "clozeId": cloze_id,
        "lemmaId": "читати",
        "lemma": "читати",
        "form": "читаю",
        "options": [
            {"kind": "answer", "lemmaId": "читати", "label": "читаю"},
            {"kind": "distractor", "lemmaId": "писати", "label": "пишу"},
        ],
    }


def test_accepts_ukrainian_targets_without_optional_overrides(tmp_path: Path) -> None:
    cloze_path, overrides_path = _write_gate_files(tmp_path, [_valid_card()])

    assert validate_teacher_cloze_content(cloze_path, overrides_path) == []


def test_rejects_english_multiword_teacher_answer(tmp_path: Path) -> None:
    card = _valid_card()
    card["lemma"] = "curated private teacher lesson"
    cloze_path, overrides_path = _write_gate_files(tmp_path, [card])

    errors = validate_teacher_cloze_content(cloze_path, overrides_path)

    assert errors == [
        "teacher-cloze teacher_cloze_1 lemma: must not be an English multi-word descriptive phrase; "
        "got 'curated private teacher lesson'"
    ]


def test_rejects_multiword_english_answer_with_cyrillic_text(tmp_path: Path) -> None:
    card = _valid_card()
    card["lemma"] = "curated private урок"
    cloze_path, overrides_path = _write_gate_files(tmp_path, [card])

    errors = validate_teacher_cloze_content(cloze_path, overrides_path)

    assert errors == [
        "teacher-cloze teacher_cloze_1 lemma: must not be an English multi-word descriptive phrase; "
        "got 'curated private урок'"
    ]


def test_excluded_card_is_removed_before_answer_validation(tmp_path: Path) -> None:
    excluded = _valid_card("teacher_cloze_2")
    excluded["form"] = "curated private teacher lesson"
    cloze_path, overrides_path = _write_gate_files(
        tmp_path,
        [_valid_card(), excluded],
        {"excludedClozeIds": ["teacher_cloze_2"]},
    )

    assert validate_teacher_cloze_content(cloze_path, overrides_path) == []


def test_rejects_stale_or_malformed_override_ids(tmp_path: Path) -> None:
    cloze_path, overrides_path = _write_gate_files(
        tmp_path,
        [_valid_card()],
        {"excludedClozeIds": ["teacher_cloze_missing", "teacher_cloze_missing"]},
    )

    errors = validate_teacher_cloze_content(cloze_path, overrides_path)

    assert errors == [
        "teacher-cloze overrides duplicate excludedClozeIds: ['teacher_cloze_missing']",
        "teacher-cloze overrides reference unknown cloze IDs: ['teacher_cloze_missing']",
    ]

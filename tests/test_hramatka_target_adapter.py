from __future__ import annotations

import hashlib
from pathlib import Path

from scripts.audit.hramatka_target_adapter import (
    HramatkaLessonAdapter,
    canonical_serialize,
    content_sha256,
    convert_hramatka_lesson_to_review_target,
    map_hramatka_level_and_policy,
    select_learner_facing_fields,
)
from scripts.audit.qg_workflow import ReviewTarget


def _lesson() -> dict[str, object]:
    return {
        "title": "Урок: квартира",
        "level": "Intermediate",
        "anchor": {"text": "Оля шукає квартиру."},
        "teacher_notes": "Do not send this note.",
        "source": "private teacher draft",
        "blocks": [
            {
                "type": "multiple-choice",
                "teacher_prompt": "Hide this prompt",
                "activity": {
                    "title": "Оберіть відповідь",
                    "instruction": "Де живе Оля?",
                    "items": [{"prompt": "Оберіть.", "options": ["У Києві", "У Львові"]}],
                    "private_token": "do-not-capture",
                },
                "answer_key": {"correct": "У Києві"},
            }
        ],
    }


def test_selects_learner_fields_and_excludes_teacher_and_source_data() -> None:
    selected, excluded = select_learner_facing_fields(_lesson())
    blob = canonical_serialize(selected)

    assert "Оля шукає квартиру" in blob
    assert "Оберіть відповідь" in blob
    for forbidden in ("Do not send", "private teacher", "Hide this", "do-not-capture"):
        assert forbidden not in blob
    assert {"teacher_notes", "source", "teacher_prompt", "private_token"} <= set(excluded)


def test_canonical_serialization_and_hash_are_stable_across_key_order() -> None:
    first = {"lesson": {"title": "Урок", "level": "a2"}, "schema": "v1"}
    second = {"schema": "v1", "lesson": {"level": "a2", "title": "Урок"}}

    assert canonical_serialize(first) == canonical_serialize(second)
    assert content_sha256(first) == content_sha256(second)
    assert content_sha256(first) == hashlib.sha256(canonical_serialize(first).encode()).hexdigest()


def test_maps_hramatka_level_aliases_to_cefr_and_policy() -> None:
    level, policy = map_hramatka_level_and_policy({"difficulty": "Upper Intermediate"})
    assert level == "b2"
    assert policy.family == "b1_plus"

    beginner, beginner_policy = map_hramatka_level_and_policy({"level": "Beginner"})
    assert beginner == "a1"
    assert beginner_policy.family == "a1"


def test_privacy_and_retention_sanitization_removes_identifiers_and_secrets() -> None:
    lesson = _lesson()
    lesson["owner_email"] = "teacher@example.test"
    private_ip = "10" + ".0.0.1"
    lesson["blocks"] = [
        {
            "activity": {
                "instruction": f"Пишіть на olia@example.test. API_KEY=super-secret {private_ip}",
                "user_id": "user-123",
            }
        }
    ]
    selected, excluded = select_learner_facing_fields(lesson)
    blob = canonical_serialize(selected)

    assert "teacher@example.test" not in blob
    assert "olia@example.test" not in blob
    assert "super-secret" not in blob
    assert private_ip not in blob
    assert "user-123" not in blob
    assert "owner_email" in excluded
    assert "user_id" in excluded


def test_adapter_materializes_native_review_target_shape(tmp_path: Path) -> None:
    result = HramatkaLessonAdapter().adapt(_lesson(), tmp_path / "lesson", slug="flat")

    assert isinstance(result.review_target, ReviewTarget)
    assert result.review_target.level == "b1"
    assert result.review_target.slug == "flat"
    assert result.content_sha256
    assert result.policy.family == "b1_plus"
    for name in ("module.md", "activities.yaml", "vocabulary.yaml", "resources.yaml"):
        assert (result.review_target.module_dir / name).is_file()

    target = convert_hramatka_lesson_to_review_target(_lesson(), tmp_path / "direct", slug="direct")
    assert isinstance(target, ReviewTarget)
    assert target.slug == "direct"

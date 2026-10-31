from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from scripts.audit import module_size_policy_audit as audit
from scripts.audit import post_build_review as pbr

pytestmark = pytest.mark.reads_content


def _patch_roots(monkeypatch, root: Path) -> None:
    monkeypatch.setattr(audit, "PROJECT_ROOT", root)
    monkeypatch.setattr(audit, "CURRICULUM_ROOT", root / "curriculum" / "l2-uk-en")
    monkeypatch.setattr(audit, "RESEARCH_ROOT", root / "docs" / "research")


def _write_plan(root: Path, track: str, slug: str, payload: dict) -> Path:
    path = root / "curriculum" / "l2-uk-en" / "plans" / track / f"{slug}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump({"slug": slug, **payload}, sort_keys=False), encoding="utf-8")
    return path


def _write_dossier(root: Path, track: str, slug: str, words: int, *, evidence: str = "") -> Path:
    path = root / "docs" / "research" / track / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    body = " ".join(["слово"] * words)
    path.write_text(
        "\n".join(
            [
                "# Досьє",
                "",
                "https://example.org/source-a",
                "https://example.org/source-b",
                evidence,
                body,
            ]
        ),
        encoding="utf-8",
    )
    return path


def _write_module(root: Path, track: str, slug: str, words: int) -> Path:
    path = root / "curriculum" / "l2-uk-en" / track / slug / "module.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Модуль\n\n" + " ".join(["слово"] * words), encoding="utf-8")
    return path


def _write_module_text(root: Path, track: str, slug: str, text: str) -> Path:
    path = root / "curriculum" / "l2-uk-en" / track / slug / "module.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_primary_source_words_are_visible_but_excluded_from_authored_repetition() -> None:
    refrain = " ".join(f"приспів{index}" for index in range(45))
    text = f"""# Навчальна тема

Пояснення учням.

:::primary-reading
# Джерельний заголовок
{refrain}
:::

:::primary-reading
{refrain}
:::
"""

    metrics, repetition, _ = audit.markdown_module_evidence(text)

    assert metrics.authored_instructional_words == 4
    assert metrics.quoted_primary_source_words == 92
    assert metrics.learner_visible_words == 96
    assert repetition.eligible_paragraphs == 0
    assert repetition.matches == ()


def test_near_duplicate_authored_paragraphs_emit_stable_line_evidence() -> None:
    first = [f"термін{index}" for index in range(50)]
    second = [*first[:45], *(f"заміна{index}" for index in range(5))]
    text = (
        "# Перша частина\n\n"
        + " ".join(first)
        + "\n\n<!-- PRIMARY-READING -->\n"
        + " ".join(f"приспів{index}" for index in range(45))
        + "\n<!-- /PRIMARY-READING -->\n\n# Друга частина\n\n"
        + " ".join(second)
        + "\n"
    )

    _, repetition, _ = audit.markdown_module_evidence(text)

    assert repetition.eligible_paragraphs == 2
    assert len(repetition.matches) == 1
    match = repetition.matches[0]
    assert match.match_type == "near_duplicate"
    assert (match.first_start_line, match.second_start_line) == (3, 11)
    assert (match.first_heading, match.second_heading) == (
        "Перша частина",
        "Друга частина",
    )
    assert match.jaccard_similarity >= audit.REPETITION_JACCARD_THRESHOLD
    assert match.shared_shingle_count >= audit.REPETITION_MIN_SHARED_SHINGLES
    assert match.shared_text.startswith("термін0 термін1")


def test_short_intentional_recap_is_not_actionable_repetition() -> None:
    recap = "Коротко повторімо головну думку модуля для самоперевірки учня."

    _, repetition, _ = audit.markdown_module_evidence(
        f"# Підсумок\n\n{recap}\n\n## Ще раз\n\n{recap}\n"
    )

    assert repetition.eligible_paragraphs == 0
    assert repetition.matches == ()


def test_sparse_bio_dossier_counts_are_descriptive_only(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _patch_roots(monkeypatch, tmp_path)
    _write_plan(
        tmp_path,
        "bio",
        "thin-person",
        {
            "word_target": 5200,
            "content_outline": [{"section": "Огляд", "words": 5200}],
            "references": [
                {
                    "type": "dossier",
                    "path": "docs/research/bio/thin-person.md",
                }
            ],
        },
    )
    _write_dossier(tmp_path, "bio", "thin-person", 900)

    report = audit.build_report(tracks=["bio"])

    assert len(report) == 1
    row = report[0]
    assert row["density_band"] == "sparse"
    assert row["effective_min"] is None
    assert row["advisory_ceiling"] == 5200
    assert row["status"] == "advisory_ok"
    assert row["decision_signals"] == ()


def test_below_legacy_floor_does_not_require_plan_review(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _patch_roots(monkeypatch, tmp_path)
    _write_plan(
        tmp_path,
        "bio",
        "overlarge-plan",
        {
            "word_target": 6000,
            "content_outline": [{"section": "Огляд", "words": 6000}],
        },
    )
    _write_dossier(tmp_path, "bio", "overlarge-plan", 900)
    _write_module(tmp_path, "bio", "overlarge-plan", 5500)

    report = audit.build_report(tracks=["bio"], built_only=True)

    row = report[0]
    assert row["status"] == "advisory_ok"
    assert row["decision_signals"] == ()


def test_dense_folk_dossier_allows_dense_advisory_ceiling(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _patch_roots(monkeypatch, tmp_path)
    _write_plan(
        tmp_path,
        "folk",
        "rich-tradition",
        {
            "word_target": 5000,
            "content_outline": [{"section": "Корпус", "words": 5000}],
        },
    )
    _write_dossier(
        tmp_path,
        "folk",
        "rich-tradition",
        5600,
        evidence=(
            " ".join(["архів", "цитата", "верифікація", "корпус"] * 3)
            + " "
            + " ".join(["дискусія", "міф", "деколонізація"] * 2)
            + " "
            + " ".join(["варіант", "обряд", "виконавство", "регіон"] * 2)
            + "\n"
            + "\n".join(f"https://example.org/source-{index}" for index in range(10))
        ),
    )
    _write_module(tmp_path, "folk", "rich-tradition", 6100)

    report = audit.build_report(tracks=["folk"], built_only=True)

    row = report[0]
    assert row["basis"] == "research_dossier"
    assert row["density_band"] == "dense"
    assert row["advisory_ceiling"] == 8000
    assert row["status"] == "advisory_ok"
    assert row["actual_words"] >= 6100


def test_reviewed_size_policy_override_replaces_generic_band_and_keeps_metrics(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _patch_roots(monkeypatch, tmp_path)
    _write_plan(
        tmp_path,
        "bio",
        "reviewed-person",
        {
            "word_target": 4200,
            "content_outline": [{"section": "Огляд", "words": 4200}],
            "size_policy": {
                "floor_words": 4200,
                "recommended_range": [4200, 4600],
                "ceiling_words": 4800,
                "basis": "Bounded chronology with verified primary-source coverage.",
                "saturation_evidence": "The dossier exhausts the available dated sources.",
                "exceptional_justification": "required_above_ceiling",
            },
        },
    )
    _write_dossier(tmp_path, "bio", "reviewed-person", 900)

    row = audit.build_report(tracks=["bio"])[0]

    assert row["basis"] == "explicit_plan_size_policy"
    assert row["density_band"] == "reviewed_plan_override"
    assert row["effective_min"] is None
    assert row["advisory_ceiling"] == 4800
    assert row["status"] == "advisory_ok"
    assert row["metrics"]["words"] > 0
    assert "Saturation evidence:" in " ".join(row["notes"])


def test_size_policy_override_is_ignored_by_acceptance() -> None:
    plan = {
        "word_target": 4200,
        "size_policy": {
            "floor_words": 4000,
            "recommended_range": [4200, 4100],
            "ceiling_words": 4050,
            "basis": "",
            "saturation_evidence": "",
            "exceptional_justification": "optional",
        },
    }

    assert audit.validate_size_policy_override(plan) == []
    assert audit.validate_size_policy_override(
        {"word_target": 4200, "size_policy": "reviewed"}
    ) == []
    assert audit.validate_size_policy_override(
        {
            "word_target": 4200,
            "size_policy": {
                **plan["size_policy"],
                "floor_words": 0,
                "recommended_range": [0, 4100],
            },
        }
    ) == []


def test_core_c1_c2_uses_evidence_packet_basis_when_no_dossier_exists(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _patch_roots(monkeypatch, tmp_path)
    _write_plan(
        tmp_path,
        "c2",
        "research-skills",
        {
            "word_target": 5000,
            "references": [
                "Державний стандарт 2024: C2",
                "Авраменко, 11 клас",
                "ГРАК корпус",
            ],
            "content_outline": [
                {"section": "Методологія", "words": 1250, "primary_sources": ["ГРАК"]},
                {"section": "Синтез", "words": 1250, "primary_sources": ["Яворницький"]},
                {"section": "Практика", "words": 2500},
            ],
        },
    )

    report = audit.build_report(tracks=["c2"])

    row = report[0]
    assert row["basis"] == "core_evidence_packet"
    assert row["density_band"] == "core_research_extended"
    assert row["advisory_ceiling"] == 6500
    assert row["status"] == "advisory_ok"
    assert row["decision_signals"] == ()


def test_filler_heavy_module_above_floor_still_requires_repetition_revision(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _patch_roots(monkeypatch, tmp_path)
    _write_plan(
        tmp_path,
        "a1",
        "padded-core",
        {
            "word_target": 80,
            "content_outline": [{"section": "Огляд", "words": 80}],
        },
    )
    paragraph = " ".join(f"пояснення{index}" for index in range(45))
    _write_module_text(
        tmp_path,
        "a1",
        "padded-core",
        f"# Огляд\n\n{paragraph}\n\n## Повтор\n\n{paragraph}\n",
    )

    row = audit.build_report(tracks=["a1"], built_only=True)[0]

    assert row["actual_words"] > row["plan_floor"]
    assert row["status"] == "repetitive_authored_prose"
    assert row["decision_signals"] == ("repetitive_authored_prose",)
    assert len(row["repetition"]["matches"]) == 1


def test_source_dense_module_above_ceiling_is_advisory_not_size_rejection(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _patch_roots(monkeypatch, tmp_path)
    _write_plan(
        tmp_path,
        "folk",
        "long-source-dense",
        {
            "word_target": 5000,
            "content_outline": [{"section": "Корпус", "words": 5000}],
        },
    )
    _write_dossier(
        tmp_path,
        "folk",
        "long-source-dense",
        5600,
        evidence=(
            " ".join(["архів", "цитата", "верифікація", "корпус"] * 3)
            + " "
            + " ".join(["дискусія", "міф", "деколонізація"] * 2)
            + " "
            + " ".join(["варіант", "обряд", "виконавство", "регіон"] * 2)
            + "\n"
            + "\n".join(f"https://example.org/source-{index}" for index in range(10))
        ),
    )
    _write_module(tmp_path, "folk", "long-source-dense", 8100)

    row = audit.build_report(tracks=["folk"], built_only=True)[0]

    assert row["actual_words"] > row["advisory_ceiling"]
    assert row["decision_signals"] == ()
    assert row["status"] == "advisory_ok"
    assert row["repetition"]["matches"] == ()


def test_evidence_gap_routes_independently_of_legacy_floor(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _patch_roots(monkeypatch, tmp_path)
    _write_plan(
        tmp_path,
        "a1",
        "exhausted-evidence",
        {
            "word_target": 100,
            "content_outline": [{"section": "Огляд", "words": 100}],
        },
    )
    _write_module_text(
        tmp_path,
        "a1",
        "exhausted-evidence",
        "<!-- EVIDENCE_GAP: objective=explain the concept; missing evidence=source support -->\n"
        "# Огляд\n\n"
        + " ".join(["слово"] * 50),
    )

    row = audit.build_report(tracks=["a1"], built_only=True)[0]

    assert row["actual_words"] == 51
    assert row["evidence_gap"] is True
    assert row["status"] == "evidence_gap"
    assert row["decision_signals"] == ("evidence_gap",)


def test_all_core_and_seminar_tracks_have_one_size_policy_route() -> None:
    policy = pbr.load_track_policy(repo_root=audit.PROJECT_ROOT)
    core = {
        track
        for track, config in policy["tracks"].items()
        if config["family"] == "core"
    }
    seminar = {
        track
        for track, config in policy["tracks"].items()
        if config["family"] == "seminar"
    }

    assert core == audit.CORE_TRACKS
    assert seminar == audit.SEMINAR_TRACKS
    assert set(policy["tracks"]) == audit.CORE_TRACKS | audit.SEMINAR_TRACKS


def test_cli_json_output_is_stable_and_read_only(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    _patch_roots(monkeypatch, tmp_path)
    _write_plan(
        tmp_path,
        "bio",
        "built-person",
        {
            "word_target": 5000,
            "content_outline": [{"section": "Огляд", "words": 5000}],
        },
    )
    _write_dossier(tmp_path, "bio", "built-person", 1400)
    _write_module(tmp_path, "bio", "built-person", 5050)

    assert audit.main(["--tracks", "bio", "--built-only", "--format", "json"]) == 0

    output = json.loads(capsys.readouterr().out)
    assert output[0]["slug"] == "built-person"
    assert output[0]["module_path"] == "curriculum/l2-uk-en/bio/built-person/module.md"
    assert not (tmp_path / "curriculum" / "l2-uk-en" / "bio" / "built-person" / "status").exists()
    assert not (tmp_path / "data" / "telemetry").exists()

    first = json.dumps(audit.build_report(tracks=["bio"], built_only=True), sort_keys=True)
    second = json.dumps(audit.build_report(tracks=["bio"], built_only=True), sort_keys=True)
    assert first == second

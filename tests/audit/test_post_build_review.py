"""Contract, regression, and exemplar tests for post-build-review."""

from __future__ import annotations

import copy
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
import yaml
from jsonschema import ValidationError

from scripts.audit import post_build_review as pbr

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "agents_extensions" / "shared" / "skills" / "post-build-review"
FIXTURES = ROOT / "tests" / "fixtures" / "post_build_review"
BILASH_V1_GOLDEN = FIXTURES / "bio-oleksandr-bilash.result.v1.json"
BILASH_V2_GOLDEN = FIXTURES / "bio-oleksandr-bilash.result.v2.json"
REGRESSIONS = FIXTURES / "regressions.v1.yaml"
CORE_EXEMPLAR = FIXTURES / "core-semantic-exemplar.v1.json"
SCORE_CALIBRATION = FIXTURES / "score-calibration.v1.yaml"


def _reviewer() -> dict[str, object]:
    return {
        "agent": "fixture",
        "family": "fixture",
        "model": "fixture-model",
        "effort": "high",
        "capabilities": ["audio", "image", "interactive", "text", "video"],
    }


def _raw(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n").encode()


def _quality_dimensions(packet: dict | None = None) -> dict[str, dict[str, object]]:
    location = "tests/fixtures/post_build_review:1"
    excerpt = "Synthetic quality-dimension evidence."
    files = (packet or {}).get("target", {}).get("files", {})
    content_path = files.get("content") if isinstance(files, dict) else None
    if isinstance(content_path, str):
        content = (ROOT / content_path).read_text(encoding="utf-8")
        excerpt = next(line.strip() for line in content.splitlines() if len(line.strip()) >= 8)
        location = f"{content_path}:1"
    return {
        dimension: {
            "status": "PASS",
            "score": 10.0,
            "score_rationale": "No evidence-backed finding identifies a gap to 10.0.",
            "evidence": [{"location": location, "excerpt": excerpt}],
            "finding_ids": [],
        }
        for dimension in pbr.QUALITY_DIMENSIONS
    }


def _passing_semantic(packet: dict) -> dict:
    modalities = sorted(
        {item["modality"] for item in packet["deterministic"].get("evidence_requirements") or []}
    )
    return {
        "verdict": "PASS",
        "summary": "Fixture semantic review completed.",
        "quality_dimensions": _quality_dimensions(packet),
        "claim_coverage": {
            "status": "complete",
            "claims_total": 1,
            "claims_checked": 1,
            "claims_supported": 1,
        },
        "claim_ledger": [
            {
                "id": "fixture-claim-1",
                "claim": "The fixture contains one supported atomic claim.",
                "location": "tests/fixtures/post_build_review:1",
                "status": "supported",
                "evidence": "Synthetic fixture evidence.",
                "finding_id": None,
            }
        ],
        "learner_evidence_ledger": [
            {
                "id": f"fixture-{modality}-1",
                "location": "tests/fixtures/post_build_review:1",
                "task": f"Inspect the fixture {modality} evidence.",
                "modality": modality,
                "source": "fixture://evidence",
                "access_status": "verified_access",
                "verification_method": f"Direct fixture {modality} inspection.",
                "finding_id": None,
            }
            for modality in modalities
        ],
        "findings": [],
    }


def _claim_owned_finding_semantic(packet: dict) -> dict:
    semantic = _passing_semantic(packet)
    semantic["verdict"] = "REVISE"
    semantic["findings"] = [
        {
            "id": "claim-only-language-finding",
            "issue_id": "CLAIM_ONLY_LANGUAGE_FINDING",
            "category": "language",
            "severity": "high",
            "message": "A claim-specific language defect requires revision.",
            "evidence": "Synthetic claim-level evidence.",
            "location": "tests/fixtures/post_build_review:1",
        }
    ]
    semantic["claim_ledger"][0].update(
        {
            "status": "contradicted",
            "finding_id": "claim-only-language-finding",
        }
    )
    semantic["claim_coverage"]["claims_supported"] = 0
    return semantic


def _mechanical_high_deterministic() -> dict:
    """Return stable mechanical findings without coupling tests to live content."""
    findings = [
        {
            "id": f"connects-to-sequence-{index}",
            "source": "track_policy",
            "severity": "high",
            "category": "crosslink_integrity",
            "message": "Synthetic crosslink integrity failure.",
            "evidence": f"synthetic sequence mismatch {index}",
            "location": "curriculum/l2-uk-en/plans/bio/subject.yaml",
        }
        for index in range(3)
    ]
    findings.append(
        {
            "id": "forbidden-placeholder-0",
            "source": "track_policy",
            "severity": "high",
            "category": "unresolved_rights",
            "message": "Synthetic unresolved rights placeholder.",
            "evidence": "portrait_fallback.license=VERIFY",
            "location": "curriculum/l2-uk-en/plans/bio/subject.yaml",
        }
    )
    deterministic = {
        "track_audit": {"status": "complete"},
        "size_policy": {"status": "complete"},
        "policy_findings": findings,
        "skip_assessments": [],
    }
    deterministic["aggregate"] = pbr.aggregate_deterministic(deterministic)
    return deterministic


def _artifact_snapshot() -> dict[str, tuple[int, int, str]]:
    paths: list[Path] = []
    bundle = ROOT / "curriculum" / "l2-uk-en" / "bio" / "oleksandr-bilash"
    paths.extend(path for path in bundle.rglob("*") if path.is_file())
    paths.append(ROOT / "curriculum" / "l2-uk-en" / "plans" / "bio" / "oleksandr-bilash.yaml")
    for dirname in ("audit", "review", "status"):
        directory = ROOT / "curriculum" / "l2-uk-en" / "bio" / dirname
        if directory.exists():
            paths.extend(path for path in directory.glob("*oleksandr-bilash*") if path.is_file())
    return {
        pbr.display_path(path): (path.stat().st_size, path.stat().st_mtime_ns, pbr.sha256_file(path))
        for path in sorted(set(paths))
    }


@pytest.fixture(scope="module")
def bilash_packet() -> dict:
    before_status = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=ROOT,
        capture_output=True,
        check=True,
        text=True,
    ).stdout
    before_artifacts = _artifact_snapshot()
    packet = pbr.prepare_review("bio/oleksandr-bilash", _reviewer())
    after_status = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=ROOT,
        capture_output=True,
        check=True,
        text=True,
    ).stdout
    assert after_status == before_status
    assert _artifact_snapshot() == before_artifacts
    return packet


def test_track_resolution_covers_every_versioned_track() -> None:
    policy = pbr.load_track_policy()
    for track, config in policy["tracks"].items():
        resolved = pbr.resolve_track_policy(track.upper(), policy)
        assert resolved["family"] == config["family"]
        assert resolved["semantic_prompt"].endswith("-semantic-review-prompt.md")
    with pytest.raises(pbr.ReviewProtocolError, match="Unknown track"):
        pbr.resolve_track_policy("unknown", policy)


def test_every_track_inherits_the_family_size_signal_policy() -> None:
    policy = pbr.load_track_policy()

    for track, config in policy["tracks"].items():
        resolved = pbr.resolve_track_policy(track, policy)
        expected = policy["families"][config["family"]][
            "size_policy_signal_severities"
        ]
        assert resolved["size_policy_signal_severities"] == expected

    assert set(policy["tracks"]) >= {"a1", "a2", "b1", "b2", "c1", "c2"}
    assert "lit-essay" in policy["tracks"]


def test_venv_python_resolution_preserves_symlink_entrypoint(tmp_path: Path) -> None:
    """The command path must stay inside .venv so Python loads pyvenv.cfg."""
    runtime_python = tmp_path / "runtime-python"
    runtime_python.write_text("runtime placeholder\n", encoding="utf-8")
    venv_python = tmp_path / ".venv" / "bin" / "python"
    venv_python.parent.mkdir(parents=True)
    venv_python.symlink_to(runtime_python)

    resolved = pbr.resolve_venv_python(tmp_path)

    assert resolved == venv_python
    assert resolved.is_symlink()


def test_track_policy_is_derived_exactly_from_curriculum_manifest() -> None:
    policy = pbr.load_track_policy()
    manifest = yaml.safe_load((ROOT / "curriculum" / "l2-uk-en" / "curriculum.yaml").read_text(encoding="utf-8"))
    assert set(policy["tracks"]) == set(manifest["levels"])
    for track, config in manifest["levels"].items():
        expected = "core" if config["type"] == "core" else "seminar"
        assert policy["tracks"][track]["family"] == expected
    assert {"history", "lit-doc", "lit-crimea"}.isdisjoint(policy["tracks"])
    raw_policy = yaml.safe_load((SKILL / "config/track-policy.v1.yaml").read_text(encoding="utf-8"))
    assert "tracks" not in raw_policy


def test_track_policy_rejects_stale_track_overrides(tmp_path: Path) -> None:
    raw_policy = yaml.safe_load((SKILL / "config/track-policy.v1.yaml").read_text(encoding="utf-8"))
    raw_policy["track_overrides"]["lit-doc"] = {}
    path = tmp_path / "track-policy.yaml"
    path.write_text(yaml.safe_dump(raw_policy, sort_keys=False), encoding="utf-8")

    with pytest.raises(pbr.ReviewProtocolError, match="inactive tracks: lit-doc"):
        pbr.load_track_policy(path, repo_root=ROOT)


def test_target_resolution_routes_core_and_bio_families() -> None:
    core = pbr.resolve_target("a1/sounds-letters-and-hello")
    seminar = pbr.resolve_target("bio/oleksandr-bilash")
    assert core["semantic_family"] == "core"
    assert seminar["semantic_family"] == "seminar"
    assert core["files"]["content"].endswith("a1/sounds-letters-and-hello/module.md")
    assert seminar["files"]["content"].endswith("bio/oleksandr-bilash/module.md")


def test_core_semantic_exemplar_uses_core_family() -> None:
    exemplar = json.loads(CORE_EXEMPLAR.read_text(encoding="utf-8"))
    target = pbr.resolve_target(exemplar["target"])
    semantic = pbr.normalize_semantic_result(
        exemplar["semantic_result"], target["semantic_family"], _reviewer()
    )
    assert target["semantic_family"] == exemplar["expected_family"] == "core"
    assert semantic["claim_coverage"]["status"] == "not_applicable"


def test_semantic_contract_requires_exactly_five_quality_dimensions() -> None:
    semantic = _passing_semantic({"deterministic": {"evidence_requirements": []}})
    semantic["quality_dimensions"].pop("tone")

    with pytest.raises(pbr.ReviewProtocolError, match="missing=tone"):
        pbr.normalize_semantic_result(semantic, "seminar", _reviewer())


def test_quality_dimension_material_finding_preserves_stable_issue_id() -> None:
    semantic = _passing_semantic({"deterministic": {"evidence_requirements": []}})
    semantic["verdict"] = "REVISE"
    semantic["findings"] = [
        {
            "id": "awkward-passive",
            "issue_id": "AWKWARD_PASSIVE_RESULT_STATE",
            "category": "language",
            "severity": "medium",
            "message": "The passive phrasing is unnatural.",
            "evidence": "Synthetic VESUM-backed fixture evidence.",
            "location": "tests/fixtures/post_build_review:1",
        }
    ]
    semantic["quality_dimensions"]["naturalness"] = {
        **semantic["quality_dimensions"]["naturalness"],
        "status": "REVISE",
        "score": 7.0,
        "score_rationale": "The cited passive construction needs revision before it can reach 10.0.",
        "finding_ids": ["awkward-passive"],
    }

    normalized = pbr.normalize_semantic_result(semantic, "seminar", _reviewer())

    assert normalized["quality_dimensions"]["naturalness"]["status"] == "REVISE"
    assert normalized["findings"][0]["issue_id"] == "AWKWARD_PASSIVE_RESULT_STATE"


def test_score_calibration_fixture_validates_anchored_cases_and_comparability(
    bilash_packet: dict,
) -> None:
    calibration = yaml.safe_load(SCORE_CALIBRATION.read_text(encoding="utf-8"))

    assert calibration["fixture_version"] == "score-calibration.v1"
    assert calibration["score_bands"] == {
        **{
            status: f"[{lower:.1f}, {upper:.1f}{']' if includes_upper else ')'}"
            for status, (lower, upper, includes_upper) in pbr.QUALITY_DIMENSION_SCORE_BANDS.items()
        },
        "INCOMPLETE": None,
    }
    assert calibration["score_anchors"] == {
        "10.0": "no dimension findings",
        "[9.0, 10.0)": "quality target with bounded low-severity headroom",
        "[8.0, 9.0)": "release-safe with a concrete low-severity improvement",
        "[7.0, 8.0)": "focused material revision while most of the dimension remains strong",
        "[6.0, 7.0)": "substantial material defect requiring broader revision",
        "[4.0, 6.0)": "blocking defect with some usable evidence",
        "[0.0, 4.0)": "fundamentally unusable, unsafe, or unsupported",
    }
    for case in calibration["cases"]:
        semantic = _passing_semantic({"deterministic": {"evidence_requirements": []}})
        dimension = case["dimension"]
        semantic["verdict"] = case["verdict"]
        semantic["quality_dimensions"][dimension].update(case["assessment"])
        finding = case["finding"]
        if finding is not None:
            semantic["findings"] = [finding]
            semantic["quality_dimensions"][dimension]["finding_ids"] = [finding["id"]]
        normalized = pbr.normalize_semantic_result(semantic, "seminar", _reviewer())

        assert case["expected"]["valid"] is True
        if "minimum_dimension_score" in case["expected"]:
            assert pbr.minimum_dimension_score(normalized["quality_dimensions"]) == case[
                "expected"
            ]["minimum_dimension_score"]
        if "documented_semantic_cap" in case["expected"]:
            assert normalized["quality_dimensions"][dimension]["score"] == case["expected"][
                "documented_semantic_cap"
            ]

    current_result = pbr.finalize_review(
        bilash_packet, _raw(_passing_semantic(bilash_packet))
    )
    current_identity = [
        current_result["semantic_prompt_version"],
        *(
            current_result["reviewer"][key]
            for key in ("family", "model", "effort")
        ),
    ]
    assert calibration["comparability"][0]["left"] == current_identity
    for comparison in calibration["comparability"]:
        assert (comparison["left"] == comparison["right"]) is comparison["expected"]


@pytest.mark.parametrize(
    ("label", "mutate", "error_fragment"),
    [
        (
            "status-score mismatch",
            lambda semantic: (
                semantic.update(
                    {
                        "findings": [
                            {
                                "id": "band-mismatch",
                                "issue_id": "SCORE_BAND_MISMATCH",
                                "category": "pedagogy",
                                "severity": "medium",
                                "message": "Synthetic band mismatch.",
                                "evidence": "Synthetic evidence-backed finding.",
                                "location": "tests/fixtures/post_build_review:1",
                            }
                        ]
                    }
                ),
                semantic["quality_dimensions"]["pedagogical"].update(
                    {"status": "REVISE", "score": 8.0, "finding_ids": ["band-mismatch"]}
                ),
            ),
            "inconsistent with REVISE",
        ),
        (
            "missing rationale",
            lambda semantic: semantic["quality_dimensions"]["pedagogical"].pop("score_rationale"),
            "fields are invalid",
        ),
        (
            "out-of-range score",
            lambda semantic: semantic["quality_dimensions"]["pedagogical"].update({"score": 10.1}),
            "inclusive range",
        ),
        (
            "excess precision",
            lambda semantic: semantic["quality_dimensions"]["pedagogical"].update({"score": 8.01}),
            "at most one decimal",
        ),
        (
            "boolean score",
            lambda semantic: semantic["quality_dimensions"]["pedagogical"].update({"score": True}),
            "not a boolean or string",
        ),
        (
            "perfect score with backlog",
            lambda semantic: (
                semantic.update(
                    {
                        "findings": [
                            {
                                "id": "perfect-score-backlog",
                                "issue_id": "PERFECT_SCORE_BACKLOG",
                                "category": "pedagogy",
                                "severity": "low",
                                "message": "A low-severity gap remains.",
                                "evidence": "Synthetic evidence for the gap.",
                                "location": "tests/fixtures/post_build_review:1",
                            }
                        ]
                    }
                ),
                semantic["quality_dimensions"]["pedagogical"].update(
                    {"finding_ids": ["perfect-score-backlog"]}
                ),
            ),
            "score 10.0 requires no dimension findings",
        ),
        (
            "orphan material finding",
            lambda semantic: semantic.update(
                {
                    "findings": [
                        {
                            "id": "unowned-language-finding",
                            "issue_id": "UNOWNED_LANGUAGE_FINDING",
                            "category": "language",
                            "severity": "high",
                            "message": "A Russianism-class defect is present.",
                            "evidence": "Synthetic evidence-backed language finding.",
                            "location": "tests/fixtures/post_build_review:1",
                        }
                    ]
                }
            ),
            "must be referenced by a quality dimension, claim, or learner-evidence entry",
        ),
    ],
)
def test_invalid_dimension_scores_fail_closed_without_repair(
    bilash_packet: dict,
    label: str,
    mutate: object,
    error_fragment: str,
) -> None:
    semantic = _passing_semantic(bilash_packet)
    mutate(semantic)

    result = pbr.finalize_review(bilash_packet, _raw(semantic))

    assert label
    assert result["semantic_response"]["contract_status"] == "invalid"
    assert error_fragment in result["semantic_response"]["error"]
    assert result["semantic"]["verdict"] == "INCOMPLETE"
    assert result["minimum_dimension_score"] is None
    assert all(
        dimension["score"] is None and dimension["score_rationale"] is None
        for dimension in result["semantic"]["quality_dimensions"].values()
    )


def test_minimum_dimension_score_is_reporting_only_not_a_disposition_input(
    bilash_packet: dict,
) -> None:
    semantic = _passing_semantic(bilash_packet)
    semantic["findings"] = [
        {
            "id": "reporting-only-low-gap",
            "issue_id": "REPORTING_ONLY_LOW_GAP",
            "category": "pedagogy",
            "severity": "low",
            "message": "A low-severity gap remains.",
            "evidence": "Synthetic evidence-backed low gap.",
            "location": "tests/fixtures/post_build_review:1",
        }
    ]
    semantic["quality_dimensions"]["pedagogical"].update(
        {
            "score": 8.0,
            "score_rationale": "The low-severity gap prevents a 10.0 pedagogical score.",
            "finding_ids": ["reporting-only-low-gap"],
        }
    )

    result = pbr.finalize_review(bilash_packet, _raw(semantic))

    assert result["minimum_dimension_score"] == 8.0
    assert result["combined_disposition"]["status"] == "PASS"


def test_minimum_dimension_score_mismatch_fails_even_with_recomputed_key(
    bilash_packet: dict,
) -> None:
    result = pbr.finalize_review(
        bilash_packet, _raw(_passing_semantic(bilash_packet))
    )
    result["minimum_dimension_score"] = 9.9
    reproducible = {
        key: copy.deepcopy(result[key]) for key in pbr.REPRODUCIBILITY_FIELDS
    }
    result["reproducibility_key"] = pbr.sha256_text(
        pbr._stable_json(reproducible)
    )

    with pytest.raises(pbr.ReviewProtocolError, match="minimum_dimension_score"):
        pbr.validate_result(result)


def test_claim_only_owned_finding_preserves_perfect_dimension_vector(
    bilash_packet: dict,
) -> None:
    result = pbr.finalize_review(
        bilash_packet, _raw(_claim_owned_finding_semantic(bilash_packet))
    )

    assert result["semantic_response"]["contract_status"] == "valid"
    assert result["minimum_dimension_score"] == 10.0
    assert result["combined_disposition"]["status"] == "REVISE"


def test_learner_evidence_only_owned_finding_is_not_orphaned(
    bilash_packet: dict,
) -> None:
    semantic = _passing_semantic(bilash_packet)
    semantic["verdict"] = "INCOMPLETE"
    semantic["findings"] = [
        {
            "id": "learner-evidence-only-finding",
            "issue_id": "LEARNER_EVIDENCE_ONLY_FINDING",
            "category": "media",
            "severity": "high",
            "message": "Required learner evidence could not be verified.",
            "evidence": "Synthetic inaccessible learner evidence.",
            "location": "tests/fixtures/post_build_review:1",
        }
    ]
    semantic["learner_evidence_ledger"].append(
        {
            "id": "fixture-unverified-audio",
            "location": "tests/fixtures/post_build_review:1",
            "task": "Inspect the required audio evidence.",
            "modality": "audio",
            "source": "fixture://unverified-audio",
            "access_status": "reviewer_unverified",
            "verification_method": "The route could not inspect the audio bytes.",
            "finding_id": "learner-evidence-only-finding",
        }
    )

    result = pbr.finalize_review(bilash_packet, _raw(semantic))

    assert result["semantic_response"]["contract_status"] == "valid"
    assert result["minimum_dimension_score"] == 10.0
    assert result["combined_disposition"]["status"] == "INCOMPLETE"


def test_stored_v4_result_rejects_orphan_finding_with_recomputed_key(
    bilash_packet: dict,
) -> None:
    result = pbr.finalize_review(
        bilash_packet, _raw(_claim_owned_finding_semantic(bilash_packet))
    )
    result["semantic"]["claim_ledger"][0].update(
        {"status": "supported", "finding_id": None}
    )
    result["semantic"]["claim_coverage"]["claims_supported"] = 1
    reproducible = {
        key: copy.deepcopy(result[key]) for key in pbr.REPRODUCIBILITY_FIELDS
    }
    result["reproducibility_key"] = pbr.sha256_text(
        pbr._stable_json(reproducible)
    )

    with pytest.raises(pbr.ReviewProtocolError, match="must be referenced"):
        pbr.validate_result(result)


@pytest.mark.parametrize("field", ["dimension", "minimum"])
def test_v4_schema_bounds_dimension_and_minimum_scores(
    bilash_packet: dict,
    field: str,
) -> None:
    result = pbr.finalize_review(
        bilash_packet, _raw(_passing_semantic(bilash_packet))
    )
    if field == "dimension":
        result["semantic"]["quality_dimensions"]["tone"]["score"] = 10.1
    else:
        result["minimum_dimension_score"] = 10.1

    with pytest.raises(ValidationError):
        pbr.validate_result(result)


def test_quality_dimension_evidence_must_quote_the_resolved_target() -> None:
    semantic = _passing_semantic({"deterministic": {"evidence_requirements": []}})
    source_texts = {"curriculum/example.md": "Фактичний текст навчального модуля."}

    with pytest.raises(pbr.ReviewProtocolError, match="not a target file"):
        pbr.normalize_semantic_result(
            semantic,
            "seminar",
            _reviewer(),
            source_texts=source_texts,
        )


def test_prompt_carries_every_legacy_canary_issue_class() -> None:
    from scripts.audit.llm_qg_canaries import CANARIES

    issue_ids = {
        issue_id
        for canary in CANARIES
        for issue_id in canary.required_issue_ids | canary.forbidden_issue_ids
    }
    prompt = (SKILL / "prompts" / "common-semantic-review-prompt.md").read_text(
        encoding="utf-8"
    )

    assert issue_ids
    assert all(issue_id in prompt for issue_id in issue_ids)


def test_effective_prompt_uses_common_plus_exactly_one_family(bilash_packet: dict) -> None:
    prompt = bilash_packet["semantic_prompt"]
    assert "Common semantic post-build review prompt" in prompt
    assert "Seminar semantic post-build review prompt" in prompt
    assert "Core semantic post-build review prompt" not in prompt
    assert "exhaustive claim ledger" in prompt.lower()
    assert "Metadata can support catalog facts" in prompt
    assert "learner_evidence_ledger" in prompt
    assert "must not repair, merge, reconcile, or normalize" in prompt
    assert pbr.sha256_text(prompt) == bilash_packet["prompt_sha256"]

    changed = prompt.replace("Exhaustive claim ledger", "Complete claim ledger", 1)
    assert pbr.sha256_text(changed) != bilash_packet["prompt_sha256"]


def test_failed_deterministic_stage_renders_incomplete_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    """A null result from a failed audit must remain evidence, not crash prompt assembly."""
    deterministic = {
        "track_audit": {
            "status": "error",
            "result": None,
            "error": "synthetic deterministic failure",
            "provenance": {},
        },
        "size_policy": {
            "status": "complete",
            "result": None,
            "error": None,
            "provenance": {},
        },
    }
    monkeypatch.setattr(
        pbr,
        "run_existing_deterministic_audits",
        lambda *args, **kwargs: copy.deepcopy(deterministic),
    )

    packet = pbr.prepare_review("bio/oleksandr-bilash", _reviewer())

    assert packet["deterministic"]["aggregate"]["status"] == "incomplete"
    assert packet["deterministic"]["track_audit"]["result"] is None
    assert '"deterministic_summary": null' in packet["semantic_prompt"]
    assert '"deterministic_findings": null' in packet["semantic_prompt"]


def test_prompt_versions_match_track_policy() -> None:
    policy = pbr.load_track_policy()
    marker = f"Semantic prompt version: `{policy['semantic_prompt_version']}`"
    for path in (SKILL / "prompts").glob("*-semantic-review-prompt.md"):
        assert marker in path.read_text(encoding="utf-8")


def test_mechanical_track_policy_detects_crosslinks_and_rights(tmp_path: Path) -> None:
    plan_root = tmp_path / "curriculum" / "l2-uk-en" / "plans" / "bio"
    plan_root.mkdir(parents=True)
    subject_plan = plan_root / "subject.yaml"
    subject_plan.write_text(
        yaml.safe_dump(
            {
                "connects_to": [
                    "bad-format",
                    "bio-1-missing",
                    "bio-999-existing",
                ],
                "portrait_fallback": {"license": "VERIFY"},
            }
        ),
        encoding="utf-8",
    )
    (plan_root / "existing.yaml").write_text(
        yaml.safe_dump({"sequence": 1}),
        encoding="utf-8",
    )
    target = {
        "files": {
            "plan": "curriculum/l2-uk-en/plans/bio/subject.yaml",
        }
    }
    track_policy = pbr.resolve_track_policy("bio", pbr.load_track_policy())

    findings = pbr.evaluate_mechanical_track_policy(
        target,
        track_policy,
        repo_root=tmp_path,
        size_record={"status": "explicit_override"},
    )

    categories = [finding["category"] for finding in findings]
    assert categories.count("crosslink_integrity") == 3
    assert categories.count("unresolved_rights") == 1
    assert {finding["severity"] for finding in findings} == {"high"}
    assert {finding["id"] for finding in findings} == {
        "connects-to-format-0",
        "connects-to-missing-1",
        "connects-to-sequence-2",
        "forbidden-placeholder-0",
    }


def test_deterministic_provenance_and_skips_are_explicit(bilash_packet: dict) -> None:
    deterministic = bilash_packet["deterministic"]
    argv = deterministic["track_audit"]["provenance"]["argv"]
    assert argv[0] == ".venv/bin/python"
    assert deterministic["track_audit"]["provenance"]["executed_argv"] == argv
    assert "--run-mdx-generation-validate" not in argv
    assert "--output" not in argv
    assert deterministic["track_audit"]["provenance"]["config_version"] == "1"
    skips = {item["category"]: item["disposition"] for item in deterministic["skip_assessments"]}
    assert skips == {
        "llm_qg": "capabilities_absorbed_by_semantic_v4",
        "mdx_generation_validate": "accepted_read_only_omission",
        "external_resource_liveness": "advisory_external",
    }


def test_bilash_size_policy_is_exemplar_only(bilash_packet: dict) -> None:
    size = bilash_packet["deterministic"]["size_policy"]["result"]
    assert size["status"] == "explicit_override"
    assert size["effective_min"] <= size["actual_words"] <= size["band_max"]
    assert [size["band_min"], size["band_max"]] == [2200, 2800]
    assert size["advisory_ceiling"] == 4000
    policy_text = (SKILL / "config" / "track-policy.v1.yaml").read_text(encoding="utf-8")
    assert "2200" not in policy_text
    assert "4000" not in policy_text


@pytest.mark.parametrize(
    ("signal", "expected_severity", "expected_disposition"),
    [
        ("below_plan_floor", "high", "BLOCK"),
        ("repetitive_authored_prose", "medium", "REVISE"),
        ("over_advisory_ceiling", "info", "PASS"),
    ],
)
def test_size_policy_signals_drive_fail_closed_post_build_disposition(
    signal: str,
    expected_severity: str,
    expected_disposition: str,
) -> None:
    policy = pbr.load_track_policy()
    track_policy = pbr.resolve_track_policy("bio", policy)
    target = {
        "files": {
            "plan": "curriculum/l2-uk-en/plans/bio/subject.yaml",
            "content": "curriculum/l2-uk-en/bio/subject/module.md",
        }
    }
    findings = pbr._check_size_policy_status(
        target,
        track_policy,
        {
            "status": signal,
            "decision_signals": [signal],
            "notes": ["synthetic regression evidence"],
            "repetition": {
                "matches": [{"first_start_line": 10, "second_start_line": 40}]
                if signal == "repetitive_authored_prose"
                else []
            },
        },
    )
    deterministic = {
        "track_audit": {"status": "complete"},
        "size_policy": {"status": "complete"},
        "policy_findings": findings,
        "skip_assessments": [],
    }
    deterministic["aggregate"] = pbr.aggregate_deterministic(deterministic)
    semantic = {
        "verdict": "PASS",
        "claim_coverage": {
            "status": "complete",
            "claims_total": 1,
            "claims_checked": 1,
        },
        "learner_evidence_ledger": [],
    }

    assert [finding["severity"] for finding in findings] == [expected_severity]
    assert (
        pbr.combine_disposition(deterministic, semantic, findings)["status"]
        == expected_disposition
    )


def test_multiple_size_policy_signals_are_not_hidden_by_status_priority() -> None:
    track_policy = pbr.resolve_track_policy("a1", pbr.load_track_policy())
    target = {
        "files": {
            "plan": "curriculum/l2-uk-en/plans/a1/subject.yaml",
            "content": "curriculum/l2-uk-en/a1/subject/module.md",
        }
    }

    findings = pbr._check_size_policy_status(
        target,
        track_policy,
        {
            "status": "plan_review_needed",
            "decision_signals": ["plan_review_needed", "below_plan_floor"],
            "notes": ["SIZE_POLICY_MISMATCH"],
            "repetition": None,
        },
    )

    assert [finding["id"] for finding in findings] == [
        "size-policy-plan_review_needed",
        "size-policy-below_plan_floor",
    ]
    assert {finding["severity"] for finding in findings} == {"high"}


def test_semantic_pass_cannot_override_mechanical_high(monkeypatch: pytest.MonkeyPatch) -> None:
    policy_findings = _mechanical_high_deterministic()["policy_findings"]
    monkeypatch.setattr(
        pbr,
        "evaluate_mechanical_track_policy",
        lambda *args, **kwargs: copy.deepcopy(policy_findings),
    )
    packet = pbr.prepare_review("bio/oleksandr-bilash", _reviewer())
    result = pbr.finalize_review(packet, _raw(_passing_semantic(packet)))

    assert result["combined_disposition"]["status"] == "BLOCK"
    assert any(finding["source"] == "track_policy" for finding in result["findings"])
    pbr.validate_result(result)


@pytest.mark.parametrize(
    ("stage_status", "severity", "skip_disposition", "expected"),
    [
        ("complete", None, None, "clear"),
        ("complete", "medium", None, "review"),
        ("complete", "high", None, "block"),
        ("error", None, None, "incomplete"),
        ("complete", None, "required", "incomplete"),
    ],
)
def test_deterministic_aggregation(
    stage_status: str,
    severity: str | None,
    skip_disposition: str | None,
    expected: str,
) -> None:
    deterministic = {
        "track_audit": {
            "status": stage_status,
            "result": {"findings": []},
        },
        "size_policy": {"status": "complete", "result": {}},
        "policy_findings": [],
        "skip_assessments": [],
    }
    if severity:
        deterministic["policy_findings"].append({"severity": severity})
    if skip_disposition:
        deterministic["skip_assessments"].append({"category": "required-check", "disposition": skip_disposition})
    assert pbr.aggregate_deterministic(deterministic)["status"] == expected


@pytest.mark.parametrize(
    ("semantic_verdict", "severity", "expected"),
    [
        ("PASS", None, "PASS"),
        ("REVISE", "medium", "REVISE"),
        ("PASS", "high", "REVISE"),
        ("BLOCK", "blocker", "BLOCK"),
        ("INCOMPLETE", None, "INCOMPLETE"),
    ],
)
def test_combined_disposition_precedence(semantic_verdict: str, severity: str | None, expected: str) -> None:
    deterministic = {
        "track_audit": {"status": "complete"},
        "size_policy": {"status": "complete"},
        "skip_assessments": [],
        "aggregate": {"status": "clear", "reasons": []},
    }
    semantic = {
        "verdict": semantic_verdict,
        "claim_coverage": {"status": "complete", "claims_total": 1, "claims_checked": 1},
        "learner_evidence_ledger": [],
    }
    findings = []
    if severity:
        findings.append({"source": "semantic", "severity": severity})
    assert pbr.combine_disposition(deterministic, semantic, findings)["status"] == expected


def test_incomplete_coverage_fails_closed() -> None:
    deterministic = {
        "track_audit": {"status": "complete"},
        "size_policy": {"status": "complete"},
        "skip_assessments": [],
        "aggregate": {"status": "clear", "reasons": []},
    }
    semantic = {
        "verdict": "PASS",
        "claim_coverage": {"status": "incomplete", "claims_total": 8, "claims_checked": 7},
        "learner_evidence_ledger": [],
    }
    assert pbr.combine_disposition(deterministic, semantic, [])["status"] == "INCOMPLETE"


def test_seminar_complete_requires_nonzero_claim_ledger() -> None:
    with pytest.raises(pbr.ReviewProtocolError, match="enumerate factual claims"):
        pbr.normalize_semantic_result(
            {
                "verdict": "PASS",
                "summary": "",
                "quality_dimensions": _quality_dimensions(),
                "claim_coverage": {
                    "status": "complete",
                    "claims_total": 0,
                    "claims_checked": 0,
                    "claims_supported": 0,
                },
                "claim_ledger": [],
                "learner_evidence_ledger": [],
                "findings": [],
            },
            "seminar",
            _reviewer(),
        )


def test_duplicate_semantic_json_fails_closed_with_raw_provenance(bilash_packet: dict) -> None:
    raw = b'{"verdict":"PASS"}\n{"verdict":"PASS"}\n'

    result = pbr.finalize_review(bilash_packet, raw)

    assert result["combined_disposition"]["status"] == "INCOMPLETE"
    assert result["semantic_response"]["raw_sha256"] == pbr.sha256_bytes(raw)
    assert result["semantic_response"]["parse_status"] == "invalid"
    assert any(finding["category"] == "semantic_response_integrity" for finding in result["findings"])


@pytest.mark.parametrize(
    "raw",
    [
        b"```json\n{\"verdict\":\"PASS\"}\n```\n",
        b'{"verdict":"PASS","verdict":"BLOCK"}\n',
        b'{"verdict":NaN}\n',
    ],
)
def test_strict_semantic_parser_rejects_wrappers_duplicates_and_constants(raw: bytes) -> None:
    parsed, provenance = pbr.parse_semantic_response(raw)

    assert parsed is None
    assert provenance["parse_status"] == "invalid"
    assert provenance["raw_sha256"] == pbr.sha256_bytes(raw)
    assert provenance["error"]


def test_cli_malformed_semantic_response_writes_valid_incomplete(
    bilash_packet: dict, tmp_path: Path
) -> None:
    packet_path = tmp_path / "packet.json"
    response_path = tmp_path / "response.json"
    result_path = tmp_path / "result.json"
    packet_path.write_text(json.dumps(bilash_packet), encoding="utf-8")
    response_path.write_text('{"verdict":"PASS"}\n{"verdict":"PASS"}\n', encoding="utf-8")

    exit_code = pbr.main(
        [
            "finalize",
            "--packet",
            str(packet_path),
            "--semantic-response",
            str(response_path),
            "--output",
            str(result_path),
        ]
    )

    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert exit_code == 1
    assert result["combined_disposition"]["status"] == "INCOMPLETE"
    pbr.validate_result(result)


def test_seminar_claim_counts_must_match_atomic_ledger() -> None:
    semantic = {
        "verdict": "PASS",
        "summary": "Unsupported aggregate count.",
        "quality_dimensions": _quality_dimensions(),
        "claim_coverage": {
            "status": "complete",
            "claims_total": 65,
            "claims_checked": 65,
            "claims_supported": 65,
        },
        "claim_ledger": [
            {
                "id": f"claim-{index}",
                "claim": f"Atomic claim {index}",
                "location": "curriculum/example.md:1",
                "status": "supported",
                "evidence": "Authoritative fixture evidence.",
                "finding_id": None,
            }
            for index in range(28)
        ],
        "learner_evidence_ledger": [],
        "findings": [],
    }

    with pytest.raises(pbr.ReviewProtocolError, match=r"claims_total.*ledger"):
        pbr.normalize_semantic_result(semantic, "seminar", {"capabilities": ["text"]})


def test_duplicate_claim_ids_are_contract_invalid() -> None:
    semantic = _passing_semantic({"deterministic": {"evidence_requirements": []}})
    semantic["claim_ledger"].append(copy.deepcopy(semantic["claim_ledger"][0]))
    semantic["claim_coverage"] = {
        "status": "complete",
        "claims_total": 2,
        "claims_checked": 2,
        "claims_supported": 2,
    }

    with pytest.raises(pbr.ReviewProtocolError, match="Duplicate claim id"):
        pbr.normalize_semantic_result(semantic, "seminar", _reviewer())


def test_generic_learner_workflow_leakage_is_mechanical_policy() -> None:
    policy = pbr.resolve_track_policy("bio", pbr.load_track_policy())
    text = (
        "Прийняте дослідницьке досьє встановлює межу. "
        "Однак доступний пакет не подає тексту виступу. "
        "Проєктний літературний корпус підтвердив цитату. "
        "У цьому пошуку не знайдено листа. "
        "Складіть карту доказів і запишіть атомарне твердження. "
        "Назвіть джерельну межу та межу доказу. "
        "Не приписуйте зміст непрочитаній справі. "
        "Зіставте заголовок статті з її основним текстом."
    )

    findings = pbr.scan_learner_workflow_leakage(
        {"content": text},
        policy["mechanical_checks"]["learner_workflow_leakage"],
    )

    assert {finding["category"] for finding in findings} == {"learner_workflow_leakage"}
    assert {finding["severity"] for finding in findings} == {"high"}
    assert {finding["evidence"] for finding in findings} == {
        "Прийняте дослідницьке досьє",
        "доступний пакет",
        "Проєктний літературний корпус",
        "У цьому пошуку не знайдено",
        "карту доказів",
        "атомарне твердження",
        "джерельну межу",
        "межу доказу",
        "зміст непрочитаній справі",
        "заголовок статті з її основним текстом",
    }


def test_malyshko_regression_has_no_current_workflow_leakage() -> None:
    target = pbr.resolve_target("bio/andrii-malyshko")
    policy = pbr.resolve_track_policy("bio", pbr.load_track_policy())

    findings = pbr.evaluate_mechanical_track_policy(
        target,
        policy,
        size_record={"status": "explicit_override"},
    )

    leakage = [finding for finding in findings if finding["category"] == "learner_workflow_leakage"]
    assert leakage == []


def test_maiboroda_regression_replaces_audio_task_with_text_evidence() -> None:
    target = pbr.resolve_target("bio/platon-maiboroda")
    policy = pbr.resolve_track_policy("bio", pbr.load_track_policy())
    texts = pbr._learner_surface_texts(target)

    requirements = pbr.inventory_evidence_requirements(
        texts,
        policy["mechanical_checks"]["evidence_requirements"],
    )

    audio = [item for item in requirements if item["modality"] == "audio"]
    assert not audio
    assert "Текстова лабораторія" in texts[target["files"]["activities"]]
    assert "Лабораторія одного опису" in texts[target["files"]["content"]]


def test_folk_productive_performance_is_not_supplied_audio_evidence() -> None:
    target = pbr.resolve_target("folk/narodna-kultura-yak-systema")
    policy = pbr.resolve_track_policy("folk", pbr.load_track_policy())
    texts = pbr._learner_surface_texts(target)

    assert "show_record_button: true" in next(
        text for path, text in texts.items() if path.endswith("activities.yaml")
    )

    requirements = pbr.inventory_evidence_requirements(
        texts,
        policy["mechanical_checks"]["evidence_requirements"],
    )

    assert requirements == []


def test_bilash_modality_vocabulary_does_not_create_evidence_requirements() -> None:
    target = pbr.resolve_target("bio/oleksandr-bilash")
    policy = pbr.resolve_track_policy("bio", pbr.load_track_policy())
    texts = pbr._learner_surface_texts(target)

    requirements = pbr.inventory_evidence_requirements(
        texts,
        policy["mechanical_checks"]["evidence_requirements"],
    )

    assert not [item for item in requirements if item["modality"] in {"audio", "video"}]


def test_optional_ungraded_media_does_not_hide_required_listening() -> None:
    policy = pbr.resolve_track_policy("bio", pbr.load_track_policy())
    texts = {
        "resources.yaml": (
            "notes: Необов'язкове позааудиторне прослуховування; "
            "запис не використовується в оцінюваних завданнях.\n"
            "notes: Перегляд необов'язковий і не оцінюється.\n"
        ),
        "module.md": "Прослухайте запис і назвіть виразно почуті слова.\n",
    }

    requirements = pbr.inventory_evidence_requirements(
        texts,
        policy["mechanical_checks"]["evidence_requirements"],
    )

    assert [(item["modality"], item["location"]) for item in requirements] == [
        ("audio", "module.md:1")
    ]


def test_audio_evidence_requires_matching_reviewer_capability() -> None:
    semantic = {
        "verdict": "PASS",
        "summary": "Metadata was incorrectly promoted to auditory verification.",
        "quality_dimensions": _quality_dimensions(),
        "claim_coverage": {
            "status": "complete",
            "claims_total": 1,
            "claims_checked": 1,
            "claims_supported": 1,
        },
        "claim_ledger": [
            {
                "id": "catalog-fact",
                "claim": "The catalog identifies the performer.",
                "location": "curriculum/example.md:1",
                "status": "supported",
                "evidence": "Catalog metadata.",
                "finding_id": None,
            }
        ],
        "learner_evidence_ledger": [
            {
                "id": "recording-1",
                "location": "curriculum/example.yaml:10",
                "task": "Identify breaths and melodic contour.",
                "modality": "audio",
                "source": "https://example.invalid/player",
                "access_status": "verified_access",
                "verification_method": "Read page metadata.",
                "finding_id": None,
            }
        ],
        "findings": [],
    }

    with pytest.raises(pbr.ReviewProtocolError, match="audio capability"):
        pbr.normalize_semantic_result(semantic, "seminar", {"capabilities": ["text"]})


def test_metadata_only_perceptual_evidence_cannot_be_downgraded_to_info() -> None:
    semantic = {
        "verdict": "PASS",
        "summary": "A text reviewer saw catalog metadata but not the recording.",
        "quality_dimensions": _quality_dimensions(),
        "claim_coverage": {
            "status": "complete",
            "claims_total": 1,
            "claims_checked": 1,
            "claims_supported": 1,
        },
        "claim_ledger": [
            {
                "id": "catalog-fact",
                "claim": "The catalog identifies the performer.",
                "location": "curriculum/example.md:1",
                "status": "supported",
                "evidence": "Catalog metadata.",
                "finding_id": None,
            }
        ],
        "learner_evidence_ledger": [
            {
                "id": "recording-1",
                "location": "curriculum/example.yaml:10",
                "task": "Identify breaths and melodic contour.",
                "modality": "audio",
                "source": "https://example.invalid/player",
                "access_status": "metadata_only",
                "verification_method": "Read page metadata only.",
                "finding_id": "audio-not-reviewed",
            }
        ],
        "findings": [
            {
                "id": "audio-not-reviewed",
                "issue_id": "AUDIO_NOT_REVIEWED",
                "category": "grounding",
                "severity": "info",
                "message": "Timestamped auditory claims were not inspected.",
                "evidence": "Only the catalog page metadata was read.",
                "location": "curriculum/example.yaml:10",
            }
        ],
    }

    with pytest.raises(pbr.ReviewProtocolError, match="requires a high or blocker finding"):
        pbr.normalize_semantic_result(semantic, "seminar", {"capabilities": ["text"]})


def test_schema_validates_historical_v1_v2_v3_and_rejects_missing_versions(
    bilash_packet: dict,
) -> None:
    historical = json.loads(BILASH_V1_GOLDEN.read_text(encoding="utf-8"))
    pbr.validate_result(historical)
    golden = json.loads(BILASH_V2_GOLDEN.read_text(encoding="utf-8"))
    pbr.validate_result(golden)
    historical_v3 = pbr.finalize_review(bilash_packet, _raw(_passing_semantic(bilash_packet)))
    historical_v3["schema_version"] = "post-build-review.result.v3"
    historical_v3.pop("minimum_dimension_score")
    for assessment in historical_v3["semantic"]["quality_dimensions"].values():
        assessment.pop("score")
        assessment.pop("score_rationale")
    historical_reproducible = {
        key: copy.deepcopy(historical_v3[key])
        for key in pbr.V3_REPRODUCIBILITY_FIELDS
    }
    historical_v3["reproducibility_key"] = pbr.sha256_text(pbr._stable_json(historical_reproducible))
    pbr.validate_result(historical_v3)
    historical_v3["semantic"]["summary"] = "Tampered historical v3 result."
    with pytest.raises(pbr.ReviewProtocolError, match="reproducibility key"):
        pbr.validate_result(historical_v3)
    for field in (
        "review_protocol_version",
        "deterministic_contract_version",
        "semantic_prompt_version",
        "track_policy_version",
        "prompt_sha256",
        "reviewer",
        "semantic_response",
        "deterministic",
    ):
        invalid = copy.deepcopy(golden)
        invalid.pop(field)
        with pytest.raises(ValidationError):
            pbr.validate_result(invalid)


def test_current_bilash_result_is_reproducible(bilash_packet: dict) -> None:
    response = _raw(_passing_semantic(bilash_packet))
    first = pbr.finalize_review(bilash_packet, response)
    second = pbr.finalize_review(bilash_packet, response)

    assert first["schema_version"] == "post-build-review.result.v4"
    assert first["reproducibility_key"] == second["reproducibility_key"]
    assert first["combined_disposition"] == second["combined_disposition"]
    assert set(first["semantic"]["quality_dimensions"]) == set(pbr.QUALITY_DIMENSIONS)
    assert first["minimum_dimension_score"] == 10.0


def test_v4_result_rejects_reproducibility_key_tampering(bilash_packet: dict) -> None:
    result = pbr.finalize_review(bilash_packet, _raw(_passing_semantic(bilash_packet)))
    result["semantic"]["summary"] = "Tampered after canonical finalization."

    with pytest.raises(pbr.ReviewProtocolError, match="reproducibility key"):
        pbr.validate_result(result)


def test_v4_result_revalidates_quality_dimension_consistency(bilash_packet: dict) -> None:
    result = pbr.finalize_review(bilash_packet, _raw(_passing_semantic(bilash_packet)))
    result["semantic"]["quality_dimensions"]["tone"]["evidence"] = []
    reproducible = {key: copy.deepcopy(result[key]) for key in pbr.REPRODUCIBILITY_FIELDS}
    result["reproducibility_key"] = pbr.sha256_text(pbr._stable_json(reproducible))

    with pytest.raises(pbr.ReviewProtocolError, match="tone requires cited evidence"):
        pbr.validate_result(result)


def test_repository_output_paths_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(pbr.ReviewProtocolError, match="outside the repository"):
        pbr.ensure_output_outside_repo(ROOT / "curriculum" / "review.json")
    pbr.ensure_output_outside_repo(tmp_path / "review.json")


def test_concurrent_review_runs_allocate_isolated_artifact_paths(tmp_path: Path) -> None:
    command = [
        str(ROOT / ".venv" / "bin" / "python"),
        str(ROOT / "scripts" / "audit" / "post_build_review.py"),
        "allocate",
        "bio/oleksandr-bilash",
        "--temp-root",
        str(tmp_path),
    ]

    def allocate() -> dict[str, str]:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
        )
        return json.loads(completed.stdout)

    with ThreadPoolExecutor(max_workers=2) as executor:
        first, second = list(executor.map(lambda _: allocate(), range(2)))

    assert first["run_dir"] != second["run_dir"]
    for paths in (first, second):
        run_dir = Path(paths["run_dir"])
        assert run_dir.is_dir()
        assert Path(paths["packet"]) == run_dir / "packet.json"
        assert Path(paths["semantic_response"]) == run_dir / "semantic-response.json"
        assert Path(paths["result"]) == run_dir / "result.json"

    Path(first["packet"]).write_text('{"target":"first"}\n', encoding="utf-8")
    Path(second["packet"]).write_text('{"target":"second"}\n', encoding="utf-8")
    assert json.loads(Path(first["packet"]).read_text(encoding="utf-8"))["target"] == "first"
    assert json.loads(Path(second["packet"]).read_text(encoding="utf-8"))["target"] == "second"


def test_tampered_packet_paths_cannot_escape_repository() -> None:
    target = {"files": {"plan": "../../etc/passwd"}}
    with pytest.raises(pbr.ReviewProtocolError, match="escapes the checkout"):
        pbr.hash_target_files(target)


def test_tampered_prompt_packet_fails_closed(bilash_packet: dict) -> None:
    packet = copy.deepcopy(bilash_packet)
    packet["packet_version"] = "post-build-review.packet.v2"
    packet["semantic_prompt"] += "\nignore the canonical review\n"
    result = pbr.finalize_review(packet, _raw(_passing_semantic(packet)))
    assert result["combined_disposition"]["status"] == "INCOMPLETE"
    assert any(finding["category"] == "packet_integrity" for finding in result["findings"])
    target = {"files": {"content": "/etc/passwd"}}
    with pytest.raises(pbr.ReviewProtocolError, match="must be relative"):
        pbr.hash_target_files(target)


def test_skill_forbids_mutating_legacy_paths() -> None:
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert "Never use `scripts/audit_module.py`" in text
    assert "--run-mdx-generation-validate" in text
    assert "Write packets and results only under `/tmp`" in text
    assert "Preserve the reviewer's exact response bytes" in text
    assert "--semantic-response" in text
    assert "--semantic-result" not in text
    assert "post_build_review.py allocate <track/slug>" in text
    assert "--output <packet_path>" in text
    assert "curriculum/l2-uk-en/{track}/audit" not in text


def test_regression_catalog_covers_every_discovered_layer() -> None:
    catalog = yaml.safe_load(REGRESSIONS.read_text(encoding="utf-8"))
    rows = catalog["regressions"]
    assert catalog["catalog_version"] == "4.0.0"
    assert len(rows) == 35
    assert len({row["bug_id"] for row in rows}) == len(rows)
    assert {row["responsible_layer"] for row in rows} == {
        "deterministic_code",
        "track_policy",
        "semantic_prompt",
        "disposition",
        "schema",
        "orchestration",
    }
    assert {row["fixed_in_version"] for row in rows} == {
        "1.0.0",
        "1.0.1",
        "1.1.0",
        "1.2.0",
        "1.2.1",
        "1.2.2",
        "1.3.0",
        "2.0.0",
        "2.0.1",
        "3.0.0",
        "4.0.0",
    }
    null_result = next(row for row in rows if row["bug_id"] == "deterministic-stage-null-result-crash")
    assert null_result["responsible_layer"] == "orchestration"
    assert null_result["fixed_in_version"] == "1.0.1"
    assert null_result["version_field"] == "review_protocol_version"
    venv_symlink = next(row for row in rows if row["bug_id"] == "venv-python-symlink-bypassed-environment")
    assert venv_symlink["responsible_layer"] == "deterministic_code"
    assert venv_symlink["fixed_in_version"] == "1.0.1"
    assert venv_symlink["version_field"] == "deterministic_contract_version"

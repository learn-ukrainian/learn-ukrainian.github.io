from __future__ import annotations

import json
import shutil
from collections.abc import Mapping
from pathlib import Path

import pytest
import yaml

from scripts.orchestration import curriculum_readiness as readiness

pytestmark = pytest.mark.reads_content

REPO_ROOT = Path(__file__).resolve().parents[2]
BIO_SLUG = "borys-hrinchenko"


def _copy(repo_root: Path, relative: str | Path) -> None:
    relative = Path(relative)
    source = REPO_ROOT / relative
    target = repo_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, target)
    else:
        shutil.copy2(source, target)


def _copy_contracts(repo_root: Path) -> None:
    _copy(repo_root, "agents_extensions/shared/curriculum-lifecycle")
    _copy(repo_root, "agents_extensions/shared/prompt-contracts")


def _bio_fixture(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    _copy_contracts(repo_root)
    for relative in (
        "curriculum/l2-uk-en/curriculum.yaml",
        "curriculum/l2-uk-en/bio/promotion-evidence.yaml",
        f"curriculum/l2-uk-en/plans/bio/{BIO_SLUG}.yaml",
        f"curriculum/l2-uk-en/bio/discovery/{BIO_SLUG}.yaml",
        f"docs/research/bio/{BIO_SLUG}.md",
        f"wiki/figures/{BIO_SLUG}.md",
        f"wiki/figures/{BIO_SLUG}.sources.yaml",
    ):
        _copy(repo_root, relative)
    dossier = repo_root / f"docs/research/bio/{BIO_SLUG}.md"
    dossier.write_text(
        dossier.read_text(encoding="utf-8")
        + """

## Використані джерела

1. https://history.org.ua/fixture-one
2. https://uk.wikipedia.org/wiki/Fixture_two
3. https://esu.com.ua/fixture-three
4. https://litopys.org.ua/fixture-four

## Хронологія

- 1900 — fixture event.
- 1910 — fixture event.

## Engagement Hooks

- [!history] Fixture hook one.
- [!context] Fixture hook two.
- [!analysis] Fixture hook three.

## Section-Mapped Research Notes

### Section one

Fixture note.

### Section two

Fixture note.

### Section three

Fixture note.
""",
        encoding="utf-8",
    )
    return repo_root


def _write_manifest(repo_root: Path, track: str, manifest_type: str, slug: str) -> None:
    path = repo_root / readiness.MANIFEST_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            {
                "version": "1.0",
                "levels": {track: {"type": manifest_type, "modules": [slug]}},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    profiles_path = repo_root / "agents_extensions/shared/prompt-contracts/profiles/curriculum-lifecycle.v1.yaml"
    profiles = yaml.safe_load(profiles_path.read_text(encoding="utf-8"))
    selected = profiles["selectors"]["tracks"].get(track)
    profiles["selectors"]["tracks"] = {track: selected} if selected else {}
    profiles["selectors"]["manifest_types"] = {
        manifest_type: profiles["selectors"]["manifest_types"][manifest_type]
    }
    profiles_path.write_text(yaml.safe_dump(profiles, sort_keys=False), encoding="utf-8")
    readiness_path = repo_root / readiness.CONFIG_PATH
    readiness_config = yaml.safe_load(readiness_path.read_text(encoding="utf-8"))
    readiness_selected = readiness_config["selectors"]["tracks"].get(track)
    readiness_config["selectors"]["tracks"] = (
        {track: readiness_selected} if readiness_selected else {}
    )
    readiness_config["selectors"]["manifest_types"] = {
        manifest_type: readiness_config["selectors"]["manifest_types"][manifest_type]
    }
    readiness_path.write_text(yaml.safe_dump(readiness_config, sort_keys=False), encoding="utf-8")


def _inventory_fixture(tmp_path: Path) -> tuple[Path, dict[str, dict]]:
    repo_root = tmp_path / "repo"
    _copy_contracts(repo_root)
    levels = {
        "bio": {
            "type": "track",
            "modules": ["bio-missing", "bio-current", "bio-drift", "bio-hold"],
        },
        "a1": {"type": "core", "modules": ["a1-audit", "a1-plan"]},
    }
    manifest_path = repo_root / readiness.MANIFEST_PATH
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        yaml.safe_dump({"version": "1.0", "levels": levels}, sort_keys=False),
        encoding="utf-8",
    )
    for relative in (
        readiness.CONFIG_PATH,
        Path("agents_extensions/shared/prompt-contracts/profiles/curriculum-lifecycle.v1.yaml"),
    ):
        config_path = repo_root / relative
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        config["selectors"]["tracks"] = {
            track: profile for track, profile in config["selectors"]["tracks"].items() if track in levels
        }
        config["selectors"]["manifest_types"] = {
            manifest_type: profile
            for manifest_type, profile in config["selectors"]["manifest_types"].items()
            if manifest_type in {level["type"] for level in levels.values()}
        }
        config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return repo_root, levels


def _fake_inventory_result(
    *,
    track: str,
    slug: str,
    profile_id: str,
    profile: Mapping,
    failed: set[str] | None = None,
    module_state: str = "unbuilt",
    preparation_state: str = "missing",
    state: str = "preparation-required",
    next_action: str = "prepare",
    findings: list[dict] | None = None,
) -> dict:
    failed = failed or set()
    return {
        "track": track,
        "slug": slug,
        "profile_id": profile_id,
        "profile_version": str(profile["version"]),
        "module_state": module_state,
        "preparation_state": preparation_state,
        "state": state,
        "next_action": next_action,
        "requirements": [
            {
                "id": requirement["id"],
                "owner": requirement["owner"],
                "passed": requirement["id"] not in failed,
            }
            for requirement in profile["requirements"]
        ],
        "findings": findings or [],
    }


def _create_bundle(repo_root: Path, track: str, slug: str) -> None:
    directory = repo_root / "curriculum" / "l2-uk-en" / track / slug
    directory.mkdir(parents=True, exist_ok=True)
    for filename in readiness.MODULE_BUNDLE_FILES:
        (directory / filename).write_text(f"fixture: {filename}\n", encoding="utf-8")


def _requirement(result: Mapping, requirement_id: str) -> Mapping:
    return next(item for item in result["requirements"] if item["id"] == requirement_id)


def _write_readings(repo_root: Path, track: str, slug: str, readings: list[dict]) -> Path:
    path = repo_root / f"curriculum/l2-uk-en/plans/{track}/{slug}.yaml"
    plan = yaml.safe_load(path.read_text(encoding="utf-8"))
    plan["readings"] = readings
    path.write_text(yaml.safe_dump(plan, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def test_single_target_cli_json_remains_byte_and_shape_compatible(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    repo_root = _bio_fixture(tmp_path)
    expected = readiness.evaluate_preparation("bio", BIO_SLUG, repo_root=repo_root)

    def evaluate(track: str, slug: str, *, consumed_preparation_identity=None):
        assert (track, slug, consumed_preparation_identity) == ("bio", BIO_SLUG, None)
        return expected

    monkeypatch.setattr(readiness, "evaluate_preparation", evaluate)

    assert readiness.main(["--track", "bio", "--slug", BIO_SLUG]) == 0
    output = capsys.readouterr().out

    assert output == json.dumps(expected, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    assert json.loads(output) == expected
    readiness.validate_result(expected, repo_root=repo_root)


def test_missing_only_is_manifest_ordered_and_preparation_safe(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo_root, _levels = _inventory_fixture(tmp_path)
    specs = {
        ("bio", "bio-missing"): {
            "failed": {"dossier"},
            "findings": [{"id": "PREPARATION_DOSSIER", "owner": "preparation"}],
        },
        ("bio", "bio-current"): {
            "preparation_state": "current",
            "state": "prepared-plan",
            "next_action": "build",
        },
        ("bio", "bio-drift"): {
            "module_state": "built",
            "preparation_state": "stale",
            "state": "built-preparation-drift",
            "findings": [{"id": "PREPARATION_IDENTITY_DRIFT", "owner": "preparation"}],
        },
        ("bio", "bio-hold"): {
            "next_action": "stop",
            "findings": [{"id": "PREPARATION_HOLD_ACTIVE", "owner": "preparation"}],
        },
        ("a1", "a1-audit"): {
            "module_state": "built",
            "preparation_state": "stale",
            "state": "built-preparation-drift",
            "findings": [{"id": "PREPARATION_IDENTITY_MISSING", "owner": "audit_tooling"}],
        },
        ("a1", "a1-plan"): {
            "failed": {"plan"},
            "state": "missing-plan",
            "next_action": "plan",
            "findings": [{"id": "PREPARATION_PLAN", "owner": "plan"}],
        },
    }

    def evaluate(**kwargs):
        return _fake_inventory_result(
            track=kwargs["track"],
            slug=kwargs["slug"],
            profile_id=kwargs["profile_id"],
            profile=kwargs["profile"],
            **specs[(kwargs["track"], kwargs["slug"])],
        )

    monkeypatch.setattr(readiness, "_evaluate_manifest_target", evaluate)

    inventory = readiness.evaluate_inventory(mode="missing-only", repo_root=repo_root)

    assert inventory["candidate_count"] == 4
    assert [(row["track"], row["slug"]) for row in inventory["rows"]] == [
        ("bio", "bio-missing"),
        ("bio", "bio-drift"),
        ("bio", "bio-hold"),
        ("a1", "a1-plan"),
    ]
    rows = {row["slug"]: row for row in inventory["rows"]}
    assert rows["bio-missing"]["failed_requirements"] == [{"id": "dossier", "owner": "preparation"}]
    assert rows["bio-drift"]["preparation_reason_codes"] == ["PREPARATION_IDENTITY_DRIFT"]
    assert rows["bio-hold"]["preparation_reason_codes"] == ["PREPARATION_HOLD_ACTIVE"]
    assert rows["a1-plan"]["failed_requirements"] == [{"id": "plan", "owner": "plan"}]
    assert "bio-current" not in rows
    assert "a1-audit" not in rows


def test_prepared_unbuilt_bio_uses_real_validators_and_exact_sources(tmp_path: Path) -> None:
    repo_root = _bio_fixture(tmp_path)

    result = readiness.evaluate_preparation("bio", BIO_SLUG, repo_root=repo_root)

    assert result["profile_id"] == "bio"
    assert result["module_state"] == "unbuilt"
    assert result["preparation_state"] == "current"
    assert result["state"] == "prepared-plan"
    assert result["next_action"] == "build"
    assert result["findings"] == []
    assert all(requirement["passed"] for requirement in result["requirements"])
    assert len(result["preparation_identity"]) == 64
    readiness.validate_result(result, repo_root=repo_root)


def test_preparation_identity_is_stable_across_clean_repository_roots(tmp_path: Path) -> None:
    first_root = _bio_fixture(tmp_path / "first")
    second_root = _bio_fixture(tmp_path / "second")

    first = readiness.evaluate_preparation("bio", BIO_SLUG, repo_root=first_root)
    second = readiness.evaluate_preparation("bio", BIO_SLUG, repo_root=second_root)

    assert first["preparation_identity"] == second["preparation_identity"]
    assert first["sources"] == second["sources"]


def test_registered_prompt_profile_bytes_are_preparation_identity_inputs(tmp_path: Path) -> None:
    repo_root = _bio_fixture(tmp_path)
    before = readiness.evaluate_preparation("bio", BIO_SLUG, repo_root=repo_root)
    prompt_profiles = repo_root / "agents_extensions/shared/prompt-contracts/profiles/curriculum-lifecycle.v1.yaml"
    prompt_profiles.write_text(prompt_profiles.read_text(encoding="utf-8") + "# identity change\n", encoding="utf-8")

    after = readiness.evaluate_preparation("bio", BIO_SLUG, repo_root=repo_root)

    assert after["state"] == before["state"]
    assert after["preparation_identity"] != before["preparation_identity"]


def test_missing_bio_evidence_fails_closed_with_preparation_owner(tmp_path: Path) -> None:
    repo_root = _bio_fixture(tmp_path)
    (repo_root / f"docs/research/bio/{BIO_SLUG}.md").unlink()

    result = readiness.evaluate_preparation("bio", BIO_SLUG, repo_root=repo_root)

    assert result["state"] == "preparation-required"
    assert result["next_action"] == "prepare"
    finding = next(item for item in result["findings"] if item["id"] == "PREPARATION_DOSSIER")
    assert finding["owner"] == "preparation"


def test_reviewed_active_hold_is_a_terminal_stop_with_a_blocker_receipt(tmp_path: Path) -> None:
    repo_root = _bio_fixture(tmp_path)
    registry_path = repo_root / "curriculum/l2-uk-en/bio/promotion-evidence.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["entries"][BIO_SLUG]["hold"] = {
        "status": "pass",
        "reviewer_family": "codex",
        "date": "2026-07-19",
        "evidence_url": "https://example.test/reviewed-hold",
        "active": True,
        "reason": "The terminal factual review found an unresolved source conflict.",
        "owner": "bio-preparation-controller",
        "checked_evidence": ["immutable packet review and adopted source set"],
        "unblock_condition": "A stable authoritative source resolves the conflict.",
    }
    registry_path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")

    result = readiness.evaluate_preparation("bio", BIO_SLUG, repo_root=repo_root)

    assert result["preparation_state"] == "missing"
    assert result["state"] == "preparation-required"
    assert result["next_action"] == "stop"
    assert "PREPARATION_HOLD_ACTIVE" in {item["id"] for item in result["findings"]}
    readiness.validate_result(result, repo_root=repo_root)

    _create_bundle(repo_root, "bio", BIO_SLUG)
    built = readiness.evaluate_preparation(
        "bio",
        BIO_SLUG,
        consumed_preparation_identity=result["preparation_identity"],
        repo_root=repo_root,
    )

    assert built["module_state"] == "built"
    assert built["preparation_state"] == "missing"
    assert built["state"] == "preparation-required"
    assert built["next_action"] == "stop"
    assert "PREPARATION_HOLD_ACTIVE" in {item["id"] for item in built["findings"]}
    readiness.validate_result(built, repo_root=repo_root)


def test_missing_plan_routes_to_plan_owner(tmp_path: Path) -> None:
    repo_root = _bio_fixture(tmp_path)
    (repo_root / f"curriculum/l2-uk-en/plans/bio/{BIO_SLUG}.yaml").unlink()

    result = readiness.evaluate_preparation("bio", BIO_SLUG, repo_root=repo_root)

    assert result["state"] == "missing-plan"
    assert result["next_action"] == "plan"
    finding = next(item for item in result["findings"] if item["id"] == "PREPARATION_PLAN")
    assert finding["owner"] == "plan"


def test_built_module_is_current_only_with_consumed_preparation_identity(tmp_path: Path) -> None:
    repo_root = _bio_fixture(tmp_path)
    prepared = readiness.evaluate_preparation("bio", BIO_SLUG, repo_root=repo_root)
    _create_bundle(repo_root, "bio", BIO_SLUG)

    missing_link = readiness.evaluate_preparation("bio", BIO_SLUG, repo_root=repo_root)
    current = readiness.evaluate_preparation(
        "bio",
        BIO_SLUG,
        consumed_preparation_identity=prepared["preparation_identity"],
        repo_root=repo_root,
    )

    assert missing_link["state"] == "built-preparation-drift"
    assert "PREPARATION_IDENTITY_MISSING" in {item["id"] for item in missing_link["findings"]}
    assert current["state"] == "built-current"
    assert current["preparation_state"] == "current"
    assert current["next_action"] == "certify"


def test_preparation_change_invalidates_build_pbr_and_qg_identities(tmp_path: Path) -> None:
    repo_root = _bio_fixture(tmp_path)
    prepared = readiness.evaluate_preparation("bio", BIO_SLUG, repo_root=repo_root)
    consumed = prepared["preparation_identity"]
    before = {
        evidence_class: readiness.dependent_evidence_identity(
            evidence_class,
            consumed,
            {"artifact": "fixture-v1"},
        )
        for evidence_class in readiness.DEPENDENT_EVIDENCE_CLASSES
    }
    _create_bundle(repo_root, "bio", BIO_SLUG)
    dossier = repo_root / f"docs/research/bio/{BIO_SLUG}.md"
    dossier.write_text(dossier.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    drifted = readiness.evaluate_preparation(
        "bio",
        BIO_SLUG,
        consumed_preparation_identity=consumed,
        repo_root=repo_root,
    )
    after = {
        evidence_class: readiness.dependent_evidence_identity(
            evidence_class,
            drifted["preparation_identity"],
            {"artifact": "fixture-v1"},
        )
        for evidence_class in readiness.DEPENDENT_EVIDENCE_CLASSES
    }

    assert drifted["state"] == "built-preparation-drift"
    assert drifted["preparation_identity"] != consumed
    assert before.keys() == after.keys()
    assert all(before[key] != after[key] for key in before)


@pytest.mark.parametrize(
    ("track", "manifest_type", "slug", "plan_source", "expected_profile"),
    [
        ("a1", "core", "sounds-letters-and-hello", "plans/a1/sounds-letters-and-hello.yaml", "core"),
        ("hist", "track", "trypillian-civilization", "plans/hist/trypillian-civilization.yaml", "seminar"),
    ],
)
def test_unbuilt_core_and_generic_seminar_profile_seams(
    tmp_path: Path,
    track: str,
    manifest_type: str,
    slug: str,
    plan_source: str,
    expected_profile: str,
) -> None:
    repo_root = tmp_path / track
    _copy_contracts(repo_root)
    _write_manifest(repo_root, track, manifest_type, slug)
    _copy(repo_root, f"curriculum/l2-uk-en/{plan_source}")

    result = readiness.evaluate_preparation(track, slug, repo_root=repo_root)

    assert result["profile_id"] == expected_profile
    assert result["module_state"] == "unbuilt"
    assert result["state"] == "preparation-required"
    assert result["next_action"] == "prepare"
    assert _requirement(result, "reading-or-rights")["passed"] is False
    assert _requirement(result, "wiki-document")["passed"] is False
    assert _requirement(result, "wiki-sources")["passed"] is False
    research_id = "research-evidence" if expected_profile == "core" else "dossier"
    assert _requirement(result, research_id)["passed"] is False


def test_core_research_requirement_accepts_explicit_packet_or_wiki_registry(
    tmp_path: Path,
    monkeypatch,
) -> None:
    track = "a1"
    slug = "sounds-letters-and-hello"

    packet_root = tmp_path / "packet"
    _copy_contracts(packet_root)
    _write_manifest(packet_root, track, "core", slug)
    _copy(packet_root, f"curriculum/l2-uk-en/plans/{track}/{slug}.yaml")
    packet_path = packet_root / f"curriculum/l2-uk-en/{track}/research/{slug}-research.md"
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    packet_path.write_text("# Deterministic research packet\n", encoding="utf-8")
    monkeypatch.setattr(
        readiness.research_quality,
        "assess_research_compat",
        lambda *_args, **_kwargs: {"quality": "solid", "score": 7},
    )

    packet_result = readiness.evaluate_preparation(track, slug, repo_root=packet_root)
    packet_requirement = _requirement(packet_result, "research-evidence")
    assert packet_requirement["passed"] is True
    assert [option["passed"] for option in packet_requirement["options"]] == [True, False]

    registry_root = tmp_path / "registry"
    _copy_contracts(registry_root)
    _write_manifest(registry_root, track, "core", slug)
    for relative in (
        f"curriculum/l2-uk-en/plans/{track}/{slug}.yaml",
        f"wiki/pedagogy/{track}/{slug}.md",
        f"wiki/pedagogy/{track}/{slug}.sources.yaml",
    ):
        _copy(registry_root, relative)

    registry_result = readiness.evaluate_preparation(track, slug, repo_root=registry_root)
    registry_requirement = _requirement(registry_result, "research-evidence")
    assert registry_requirement["passed"] is True
    assert [option["passed"] for option in registry_requirement["options"]] == [False, True]


@pytest.mark.parametrize(
    ("score", "quality", "expected"),
    [(6, "adequate", False), (7, "solid", True)],
)
def test_research_quality_uses_existing_solid_score_floor(
    tmp_path: Path,
    monkeypatch,
    score: int,
    quality: str,
    expected: bool,
) -> None:
    repo_root = tmp_path / "repo"
    path = repo_root / "docs/research/hist/demo.md"
    path.parent.mkdir(parents=True)
    path.write_text("# Research fixture\n", encoding="utf-8")
    context = readiness.ValidationContext(repo_root, "hist", "demo", ("demo",))
    monkeypatch.setattr(
        readiness.research_quality,
        "assess_research_compat",
        lambda *_args, **_kwargs: {"quality": quality, "score": score},
    )

    result = readiness._research_quality(path, {}, context)

    assert result.passed is expected
    assert f"({score}/10)" in result.detail


@pytest.mark.parametrize(
    ("registry_text", "expected_detail"),
    [
        ("sources: []\n", "non-empty sources list"),
        ("plain: mapping\n", "non-empty sources list"),
        ("sources:\n  - id: S1\n", "invalid wiki source registry"),
    ],
)
def test_wiki_source_registry_fails_closed_when_empty_or_malformed(
    tmp_path: Path,
    registry_text: str,
    expected_detail: str,
) -> None:
    repo_root = tmp_path / "repo"
    article = repo_root / "wiki/pedagogy/a1/demo.md"
    registry = article.with_suffix(".sources.yaml")
    article.parent.mkdir(parents=True)
    article.write_text("# Demo\n\nGrounded claim [S1].\n", encoding="utf-8")
    registry.write_text(registry_text, encoding="utf-8")
    context = readiness.ValidationContext(repo_root, "a1", "demo", ("demo",))

    result = readiness._wiki_sources_registry(registry, {}, context)

    assert result.passed is False
    assert expected_detail in result.detail


def test_verified_reading_catalog_and_reviewed_rights_are_explicit_alternatives(tmp_path: Path) -> None:
    track = "a1"
    slug = "sounds-letters-and-hello"
    repo_root = tmp_path / "repo"
    _copy_contracts(repo_root)
    _write_manifest(repo_root, track, "core", slug)
    _copy(repo_root, f"curriculum/l2-uk-en/plans/{track}/{slug}.yaml")
    plan_path = _write_readings(
        repo_root,
        track,
        slug,
        [{"title": "Internal packet", "source_locator": "corpus:fixture-a1"}],
    )
    context = readiness.ValidationContext(repo_root, track, slug, (slug,))

    verified = readiness._verified_reading_catalog(plan_path, {}, context)
    assert verified.passed is True

    _write_readings(
        repo_root,
        track,
        slug,
        [{"source_name": "External packet", "source": "https://example.test/reading"}],
    )
    source_alias = readiness._verified_reading_catalog(plan_path, {}, context)
    assert source_alias.passed is True

    _write_readings(
        repo_root,
        track,
        slug,
        [{"source_name": "Provider label", "source": "Archive provider prose"}],
    )
    provider_prose = readiness._verified_reading_catalog(plan_path, {}, context)
    assert provider_prose.passed is False
    assert "HTTP(S) URL or explicit internal source locator" in provider_prose.detail

    _write_readings(
        repo_root,
        track,
        slug,
        [{"title": "Placeholder", "source_url": "reading-needed"}],
    )
    registry_path = repo_root / f"curriculum/l2-uk-en/{track}/promotion-evidence.yaml"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        """version: 1
entries:
  sounds-letters-and-hello:
    reading_rights:
      status: pass
      reviewer_family: human
      date: 2026-07-19
      evidence_url: https://example.test/reviewed-rights
      disposition: link-only-approved
""",
        encoding="utf-8",
    )

    result = readiness.evaluate_preparation(track, slug, repo_root=repo_root)
    requirement = _requirement(result, "reading-or-rights")
    assert requirement["passed"] is True
    assert [option["passed"] for option in requirement["options"]] == [False, True]


def test_bio_reading_policy_is_ukrainian_only_and_requires_two_candidate_roles(tmp_path: Path) -> None:
    repo_root = _bio_fixture(tmp_path)
    plan_path = repo_root / f"curriculum/l2-uk-en/plans/bio/{BIO_SLUG}.yaml"
    context = readiness.ValidationContext(repo_root, "bio", BIO_SLUG, (BIO_SLUG,))

    passing = readiness._bio_reading_policy(plan_path, {}, context)
    assert passing.passed is True

    plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
    plan["readings"][0]["language"] = "en"
    plan_path.write_text(yaml.safe_dump(plan, allow_unicode=True, sort_keys=False), encoding="utf-8")
    non_ukrainian = readiness._bio_reading_policy(plan_path, {}, context)
    assert non_ukrainian.passed is False
    assert "language: uk" in non_ukrainian.detail

    plan["readings"] = [
        {
            "title": "Context only",
            "language": "uk",
            "source_type": "encyclopedia",
            "source_url": "https://example.test/context",
        }
    ]
    plan_path.write_text(yaml.safe_dump(plan, allow_unicode=True, sort_keys=False), encoding="utf-8")
    incomplete = readiness._bio_reading_policy(plan_path, {}, context)
    assert incomplete.passed is False
    assert "distinct reference/context" in incomplete.detail


def test_off_manifest_target_fails_with_authority_owner(tmp_path: Path) -> None:
    repo_root = _bio_fixture(tmp_path)

    result = readiness.evaluate_preparation("bio", "not-in-curriculum", repo_root=repo_root)

    assert result["state"] == "off-manifest"
    assert result["next_action"] == "stop"
    assert result["preparation_identity"] is None
    assert result["findings"] == [
        {
            "id": "OFF_MANIFEST_TARGET",
            "category": "authority",
            "severity": "blocker",
            "summary": "Target is not an active curriculum manifest member",
            "owner": "authority",
        }
    ]


def test_partial_bundle_stops_for_built_artifact_recovery(tmp_path: Path) -> None:
    repo_root = _bio_fixture(tmp_path)
    module_dir = repo_root / "curriculum/l2-uk-en/bio" / BIO_SLUG
    module_dir.mkdir(parents=True)
    (module_dir / "module.md").write_text("# Partial\n", encoding="utf-8")

    result = readiness.evaluate_preparation("bio", BIO_SLUG, repo_root=repo_root)

    assert result["state"] == "partial-bundle"
    assert result["next_action"] == "stop"
    assert "PARTIAL_LEARNER_BUNDLE" in {item["id"] for item in result["findings"]}


def test_host_path_only_text_change_ignores_baked_checkout_rewrites() -> None:
    # Fictional macOS and Linux checkouts; only their shape matters to the matcher.
    macos_checkout = "/".join(("", "Users", "fixture-user", "projects", "learn-ukrainian"))
    linux_checkout = "/".join(("", "home", "fixture-user", "learn-ukrainian"))
    baked_script = (
        f"Run `.venv/bin/python {macos_checkout}/"
        "scripts/audit/check_dossier_wordcount.py "
        "--changed`.\n"
    )
    baked_venv = (
        f"- [ ] `{macos_checkout}/"
        ".venv/bin/python scripts/audit/lint_bio_dossier_xref.py "
        "--paths docs/research/bio/pavlo-pavliuk-but.md`\n"
    )
    scrubbed_script = (
        "Run `.venv/bin/python scripts/audit/check_dossier_wordcount.py "
        "--changed`.\n"
    )
    scrubbed_venv = (
        "- [ ] `.venv/bin/python scripts/audit/lint_bio_dossier_xref.py "
        "--paths docs/research/bio/pavlo-pavliuk-but.md`\n"
    )
    assert readiness.is_host_path_only_text_change(baked_script, scrubbed_script)
    assert readiness.is_host_path_only_text_change(baked_venv, scrubbed_venv)
    assert readiness.is_host_path_only_text_change(
        f"Run `.venv/bin/python {linux_checkout}/scripts/audit/check_dossier_wordcount.py --changed`.\n",
        scrubbed_script,
    )
    # Another repository under the same home is a real change, not a baked checkout.
    assert not readiness.is_host_path_only_text_change(
        "Run `.venv/bin/python "
        + "/".join(("", "home", "fixture-user", "other-repo"))
        + "/scripts/audit/check_dossier_wordcount.py --changed`.\n",
        scrubbed_script,
    )
    assert not readiness.is_host_path_only_text_change(
        baked_script, baked_script + "\n## Extra\n"
    )
    assert not readiness.is_host_path_only_text_change("", scrubbed_venv)

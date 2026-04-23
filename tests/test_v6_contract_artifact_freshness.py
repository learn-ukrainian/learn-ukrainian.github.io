from __future__ import annotations

import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import build.phases.plan_contract as plan_contract
from build import v6_build
from build.alignment_manifest import manifest_hash


def _write_plan(curriculum_root: Path, level: str, slug: str, *, title: str) -> None:
    plan_path = curriculum_root / "plans" / level / f"{slug}.yaml"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        yaml.safe_dump(
            {
                "module": 1,
                "slug": slug,
                "level": level,
                "title": title,
                "content_outline": [],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        "utf-8",
    )


def _current_manifest(curriculum_root: Path, level: str, slug: str) -> dict[str, str]:
    plan_path = curriculum_root / "plans" / level / f"{slug}.yaml"
    plan = yaml.safe_load(plan_path.read_text("utf-8")) or {}
    return {"plan_title": str(plan.get("title") or "")}


def test_ensure_contract_artifacts_stamps_and_reuses_fresh_sidecars(
    tmp_path: Path,
    monkeypatch,
) -> None:
    level = "a1"
    slug = "demo"
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    _write_plan(curriculum_root, level, slug, title="Original")
    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    monkeypatch.setattr(
        v6_build,
        "_current_alignment_manifest",
        lambda level, slug: _current_manifest(curriculum_root, level, slug),
    )

    build_calls: list[str] = []
    logs: list[str] = []

    def fake_build_contract(plan, wiki_packet, *, level, slug, module_num):
        build_calls.append(str(plan["title"]))
        return (
            {"module": {"slug": slug}, "title": plan["title"]},
            {"sections": {"Intro": {"excerpt": wiki_packet or "none"}}},
        )

    monkeypatch.setattr(plan_contract, "build_contract", fake_build_contract)
    monkeypatch.setattr(v6_build, "_log", logs.append)

    contract, excerpts = v6_build._ensure_contract_artifacts(level, 1, slug, log_creation=True)
    reused_contract, reused_excerpts = v6_build._ensure_contract_artifacts(
        level,
        1,
        slug,
        log_creation=True,
    )
    current_manifest = _current_manifest(curriculum_root, level, slug)

    assert build_calls == ["Original"]
    assert contract["alignment_manifest"]["composite_hash"] == manifest_hash(current_manifest)
    assert excerpts["alignment_manifest"]["composite_hash"] == manifest_hash(current_manifest)
    assert reused_contract == contract
    assert reused_excerpts == excerpts
    assert any("sidecars fresh" in entry for entry in logs)


def test_ensure_contract_artifacts_rebuilds_when_plan_hash_changes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    level = "a1"
    slug = "demo"
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    _write_plan(curriculum_root, level, slug, title="Before")
    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    monkeypatch.setattr(
        v6_build,
        "_current_alignment_manifest",
        lambda level, slug: _current_manifest(curriculum_root, level, slug),
    )

    build_calls: list[str] = []
    logs: list[str] = []

    def fake_build_contract(plan, wiki_packet, *, level, slug, module_num):
        build_calls.append(str(plan["title"]))
        return (
            {"module": {"slug": slug}, "title": plan["title"]},
            {"sections": {"Intro": {"excerpt": wiki_packet or "none"}}},
        )

    monkeypatch.setattr(plan_contract, "build_contract", fake_build_contract)
    monkeypatch.setattr(v6_build, "_log", logs.append)

    v6_build._ensure_contract_artifacts(level, 1, slug, log_creation=False)
    _write_plan(curriculum_root, level, slug, title="After")

    contract, excerpts = v6_build._ensure_contract_artifacts(level, 1, slug, log_creation=False)
    current_manifest = _current_manifest(curriculum_root, level, slug)

    assert build_calls == ["Before", "After"]
    assert contract["title"] == "After"
    assert contract["alignment_manifest"]["composite_hash"] == manifest_hash(current_manifest)
    assert excerpts["alignment_manifest"]["composite_hash"] == manifest_hash(current_manifest)
    assert any("Rebuilding contract/excerpts — stale sidecar" in entry for entry in logs)

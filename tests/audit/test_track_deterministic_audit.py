from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scripts.audit import track_deterministic_audit as audit


@dataclass
class DummyModule:
    slug: str
    title: str
    level: str
    local_num: int


def write_minimal_module(root: Path, slug: str, num: int, *, english_leak: bool = False) -> None:
    curriculum = root / "curriculum" / "l2-uk-en"
    module_dir = curriculum / "b2" / slug
    module_dir.mkdir(parents=True)
    (curriculum / "plans" / "b2").mkdir(parents=True, exist_ok=True)
    (root / "wiki" / "grammar" / "b2").mkdir(parents=True, exist_ok=True)
    (root / "site" / "src" / "content" / "docs" / "b2").mkdir(parents=True, exist_ok=True)
    (root / "site" / "src" / "content" / "readings").mkdir(parents=True, exist_ok=True)

    body = "This paragraph explains the entire grammar point in English before Ukrainian appears.\n" if english_leak else ""
    (module_dir / "module.md").write_text(f"# Модуль {num}\n\n{body}**Я чекаю на автобус.**\n", encoding="utf-8")
    (module_dir / "activities.yaml").write_text(
        "- type: quiz\n"
        "  title: Перевірка\n"
        "  items:\n"
        "    - question: Що правильно?\n"
        "      options:\n"
        "        - text: Так\n"
        "          correct: true\n"
        "        - text: Ні\n"
        "          correct: false\n",
        encoding="utf-8",
    )
    (module_dir / "vocabulary.yaml").write_text(
        "- word: слово\n"
        "  translation: word\n",
        encoding="utf-8",
    )
    (curriculum / "plans" / "b2" / f"{slug}.yaml").write_text("title: Test\n", encoding="utf-8")
    (root / "wiki" / "grammar" / "b2" / f"{slug}.md").write_text("# Вікі\n", encoding="utf-8")
    (root / "wiki" / "grammar" / "b2" / f"{slug}.sources.yaml").write_text("sources: []\n", encoding="utf-8")
    (root / "site" / "src" / "content" / "docs" / "b2" / f"{slug}.mdx").write_text(
        "---\ntitle: Test\n---\n\n[Self](/b2/test-one)\n",
        encoding="utf-8",
    )


def patch_roots(monkeypatch, root: Path) -> None:
    monkeypatch.setattr(audit, "PROJECT_ROOT", root)
    monkeypatch.setattr(audit, "CURRICULUM_ROOT", root / "curriculum" / "l2-uk-en")
    monkeypatch.setattr(audit, "SITE_DOCS_ROOT", root / "site" / "src" / "content" / "docs")
    monkeypatch.setattr(audit, "SITE_READINGS_ROOT", root / "site" / "src" / "content" / "readings")
    monkeypatch.setattr(
        audit,
        "get_modules_for_level",
        lambda track: [
            DummyModule("test-one", "Test One", track, 1),
            DummyModule("test-two", "Test Two", track, 2),
        ],
    )
    monkeypatch.setattr(audit, "check_protected_diff", lambda track: [])


def base_config() -> dict:
    return {
        "defaults": {
            "required_files": ["plan", "module_md", "activities", "vocabulary", "site_mdx", "wiki", "wiki_sources"],
            "optional_files": ["resources"],
            "checks": {
                "activity_yaml": False,
                "vocabulary_yaml": True,
                "resources_yaml": True,
                "surface_gates": True,
                "internal_leakage": True,
                "mdx_routes": True,
                "protected_diff": True,
            },
            "severity": {
                "missing_required_file": "high",
                "optional_missing": "info",
            },
        },
        "tracks": {},
    }


def test_parse_range() -> None:
    assert audit.parse_range("1-3") == (1, 3)


def test_track_audit_json_contract_and_llm_qg_exclusion(tmp_path, monkeypatch) -> None:
    patch_roots(monkeypatch, tmp_path)
    write_minimal_module(tmp_path, "test-one", 1)
    write_minimal_module(tmp_path, "test-two", 2)
    index = tmp_path / "site" / "src" / "content" / "docs" / "b2" / "index.mdx"
    index.write_text('slug: "test-one"\nslug: "test-two"\n', encoding="utf-8")

    result = audit.audit_track(
        track="b2",
        config=base_config(),
        range_filter=(1, 1),
        slugs=None,
        run_mdx_generation_validate=False,
    )

    assert result["track"] == "b2"
    assert result["summary"]["modules_selected"] == 1
    assert result["summary"]["llm_qg_excluded_pending_2156"] is True
    assert any(item["category"] == "llm_qg" for item in result["skipped"])
    assert all("llm_qg_status" not in item for item in result["findings"])
    assert not (tmp_path / "curriculum" / "l2-uk-en" / "b2" / "test-one" / "status").exists()
    assert not (tmp_path / "curriculum" / "l2-uk-en" / "b2" / "test-one" / "audit").exists()


def test_vocabulary_validation_reports_missing_translation(tmp_path, monkeypatch) -> None:
    patch_roots(monkeypatch, tmp_path)
    write_minimal_module(tmp_path, "test-one", 1)
    vocab = tmp_path / "curriculum" / "l2-uk-en" / "b2" / "test-one" / "vocabulary.yaml"
    vocab.write_text("- word: слово\n", encoding="utf-8")

    paths = audit.select_modules("b2", (1, 1), None)[0]
    findings = audit.check_vocabulary_yaml(paths)

    assert any(item.category == "vocabulary_validity" and item.severity == "high" for item in findings)


def test_surface_gate_reports_b2_english_leak(tmp_path, monkeypatch) -> None:
    patch_roots(monkeypatch, tmp_path)
    write_minimal_module(tmp_path, "test-one", 1, english_leak=True)

    paths = audit.select_modules("b2", (1, 1), None)[0]
    findings = audit.check_surface(paths)

    assert any(item.category == "english_internal_leakage" and item.severity == "high" for item in findings)


def test_internal_leakage_skips_resource_provenance_key(tmp_path, monkeypatch) -> None:
    """`chunk_id:` / `packet_chunk_id:` keys in resources.yaml are non-rendering
    corpus-provenance metadata (consumed by the plan-reference gate), so a bare
    provenance-key line must NOT be flagged — but prose mentioning the term still is."""
    patch_roots(monkeypatch, tmp_path)
    write_minimal_module(tmp_path, "test-one", 1)
    resources = tmp_path / "curriculum" / "l2-uk-en" / "b2" / "test-one" / "resources.yaml"
    resources.write_text(
        "- title: Буквар 1 клас, с. 24\n"
        "  role: textbook\n"
        "  chunk_id: 1-klas-bukvar-2018_s0023\n"
        "  packet_chunk_id: 1-klas-bukvar-2018_s0024\n"
        "  notes: retrieved via search_text; no literal chunk_id in plan\n",
        encoding="utf-8",
    )

    paths = audit.select_modules("b2", (1, 1), None)[0]
    findings = audit.check_internal_leakage(paths)
    leaks = [f for f in findings if f.file and f.file.endswith("resources.yaml")]

    # The bare provenance-key lines are skipped...
    assert not any(f.line == 3 for f in leaks), "chunk_id: key line should not be flagged"
    assert not any(f.line == 4 for f in leaks), "packet_chunk_id: key line should not be flagged"
    # ...but the notes prose that MENTIONS chunk_id still leaks (renders in Resources tab).
    assert any(f.line == 5 for f in leaks), "notes prose mentioning chunk_id must still be flagged"


def test_module_paths_wiki_resolution() -> None:
    # 1. A1 should point under pedagogy/a1
    a1_module = DummyModule("greeting", "Greeting", "a1", 1)
    a1_paths = audit.module_paths("a1", a1_module)
    assert "wiki/pedagogy/a1/greeting.md" in a1_paths.wiki.as_posix()
    assert "wiki/pedagogy/a1/greeting.sources.yaml" in a1_paths.wiki_sources.as_posix()

    # 2. B1 should point under grammar/b1
    b1_module = DummyModule("aspect", "Aspect", "b1", 1)
    b1_paths = audit.module_paths("b1", b1_module)
    assert "wiki/grammar/b1/aspect.md" in b1_paths.wiki.as_posix()
    assert "wiki/grammar/b1/aspect.sources.yaml" in b1_paths.wiki_sources.as_posix()

    # 3. Seminar tracks should use the compiler's track-aware write domains
    bio_module = DummyModule("oleksandr-bilash", "Oleksandr Bilash", "bio", 1)
    bio_paths = audit.module_paths("bio", bio_module)
    assert "wiki/figures/oleksandr-bilash.md" in bio_paths.wiki.as_posix()
    assert "wiki/figures/oleksandr-bilash.sources.yaml" in bio_paths.wiki_sources.as_posix()
    assert "wiki/grammar/bio" not in bio_paths.wiki.as_posix()
    assert "wiki/grammar/bio" not in bio_paths.wiki_sources.as_posix()

    hist_module = DummyModule("kyivan-rus", "Kyivan Rus", "hist", 1)
    hist_paths = audit.module_paths("hist", hist_module)
    assert "wiki/periods/kyivan-rus.md" in hist_paths.wiki.as_posix()
    assert "wiki/periods/kyivan-rus.sources.yaml" in hist_paths.wiki_sources.as_posix()

    folk_module = DummyModule("koliadky-shchedrivky", "Koliadky", "folk", 1)
    folk_paths = audit.module_paths("folk", folk_module)
    assert "wiki/folk/ritual/koliadky-shchedrivky.md" in folk_paths.wiki.as_posix()
    assert "wiki/folk/ritual/koliadky-shchedrivky.sources.yaml" in folk_paths.wiki_sources.as_posix()

    # 4. Unknown tracks preserve the compiler fallback domain.
    unmapped_module = DummyModule("topic", "Topic", "unknown-track", 1)
    unmapped_paths = audit.module_paths("unknown-track", unmapped_module)
    assert "wiki/unknown-track/topic.md" in unmapped_paths.wiki.as_posix()
    assert "wiki/unknown-track/topic.sources.yaml" in unmapped_paths.wiki_sources.as_posix()


def test_a1_config_requires_wiki_like_b2() -> None:
    """#4305 user decision 2026-07-06: A1 (published entry-point track)
    promotes wiki + wiki_sources to required, mirroring B2; resources stays
    optional and optional_missing stays info-level."""
    import yaml
    from audit.track_deterministic_audit import DEFAULT_CONFIG, merged_track_config

    config = yaml.safe_load(DEFAULT_CONFIG.read_text(encoding="utf-8"))
    for track in ("a1", "b2"):
        merged = merged_track_config(config, track)
        assert "wiki" in merged["required_files"], track
        assert "wiki_sources" in merged["required_files"], track
        assert "resources" in merged["optional_files"], track
        assert merged["severity"]["optional_missing"] == "info", track

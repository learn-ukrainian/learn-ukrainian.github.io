"""Focused coverage for deterministic Atlas course-usage backfills."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from scripts.lexicon import backfill_course_usage as backfill


def test_backfill_matches_exact_vesum_apostrophe_stress_and_multiword(tmp_path: Path) -> None:
    curriculum_root, manifest_path, module_numbers = _fixture_corpus(tmp_path)

    result = backfill.backfill_course_usage(
        curriculum_root=curriculum_root,
        manifest_path=manifest_path,
        vesum_forms_lookup=_fake_vesum_forms,
    )
    updates = {update.lemma: update.rows for update in result.updates}

    assert _slugs(updates["бакалаврат"]) == ["exact"]
    assert _slugs(updates["кіт"]) == ["vesum"]
    assert _slugs(updates["м'яч"]) == ["apostrophe-modifier", "apostrophe-curly"]
    assert _slugs(updates["мама"]) == ["stress"]
    assert _slugs(updates["добрий день"]) == ["phrase"]
    assert {row["module_num"] for row in updates["м'яч"]} == {
        module_numbers["apostrophe-modifier"],
        module_numbers["apostrophe-curly"],
    }
    assert all(row["context"] == "content_backfill" for rows in updates.values() for row in rows)
    assert all(set(row) == {"track", "module_num", "slug", "context"} for rows in updates.values() for row in rows)


def test_backfill_fails_closed_for_shared_form_and_ignores_nonvisible_text(tmp_path: Path) -> None:
    curriculum_root, manifest_path, _module_numbers = _fixture_corpus(tmp_path)

    result = backfill.backfill_course_usage(
        curriculum_root=curriculum_root,
        manifest_path=manifest_path,
        vesum_forms_lookup=_fake_vesum_forms,
    )
    updates = {update.lemma: update.rows for update in result.updates}

    assert "замок" not in updates
    assert "замка" not in updates
    assert "інший" not in updates
    assert _slugs(updates["спільний"]) == ["exact-shared"]
    assert "код" not in updates
    assert "коментар" not in updates
    assert result.ambiguous_surface_forms_skipped == 2


def test_backfill_caps_rows_and_ranks_exact_matches_first(tmp_path: Path) -> None:
    curriculum_root, manifest_path, module_numbers = _fixture_corpus(tmp_path)

    result = backfill.backfill_course_usage(
        curriculum_root=curriculum_root,
        manifest_path=manifest_path,
        vesum_forms_lookup=_fake_vesum_forms,
    )
    rows = next(update.rows for update in result.updates if update.lemma == "тест")

    assert len(rows) == 6
    assert _slugs(rows) == [f"cap-exact-{number}" for number in range(1, 7)]
    assert [row["module_num"] for row in rows] == [module_numbers[slug] for slug in _slugs(rows)]


def test_dry_run_default_does_not_write_and_cli_emits_json(tmp_path: Path, monkeypatch, capsys) -> None:
    curriculum_root, manifest_path, _module_numbers = _fixture_corpus(tmp_path)
    before = manifest_path.read_bytes()
    monkeypatch.setattr(backfill, "verify_lemma", _fake_vesum_forms)

    assert (
        backfill.main(
            [
                "--manifest",
                str(manifest_path),
                "--curriculum-root",
                str(curriculum_root),
                "--json",
            ]
        )
        == 0
    )

    assert manifest_path.read_bytes() == before
    assert not (manifest_path.parent / "lexicon-manifest.fingerprint.json").exists()
    summary = json.loads(capsys.readouterr().out)
    assert summary["entries_would_gain_course_usage"] == 7
    assert summary["manifest_written"] is False
    assert summary["fingerprint_written"] is False


def test_write_uses_manifest_serializer_and_restamps_fingerprint(tmp_path: Path) -> None:
    curriculum_root, manifest_path, _module_numbers = _fixture_corpus(tmp_path)
    fingerprint_path = manifest_path.parent / "lexicon-manifest.fingerprint.json"

    result = backfill.backfill_course_usage(
        curriculum_root=curriculum_root,
        manifest_path=manifest_path,
        write=True,
        vesum_forms_lookup=_fake_vesum_forms,
        fingerprint_path=fingerprint_path,
    )

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    exact = next(entry for entry in payload["entries"] if entry["lemma"] == "бакалаврат")
    existing = next(entry for entry in payload["entries"] if entry["lemma"] == "готове")
    assert exact["course_usage"] == [
        {
            "track": "b1",
            "module_num": 1,
            "slug": "exact",
            "context": "content_backfill",
        }
    ]
    assert existing["course_usage"] == [{"track": "b1", "module_num": 99, "slug": "existing"}]
    assert (
        payload["manifest_fingerprint"]["fingerprint"]
        == json.loads(fingerprint_path.read_text(encoding="utf-8"))["fingerprint"]
    )
    assert result.manifest_written is True
    assert result.fingerprint_written is True


def _fixture_corpus(tmp_path: Path) -> tuple[Path, Path, dict[str, int]]:
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    track_root = curriculum_root / "b1"
    modules = [
        ("exact", "Починаємо новий етап."),
        ("vesum", "Коти сплять."),
        ("boundary", "Кітка спить."),
        ("shared", "Замки стоять."),
        ("exact-shared", "Спільний випадок залишається точним збігом."),
        ("apostrophe-modifier", "Мʼяч летить."),
        ("apostrophe-curly", "М’яч летить."),
        ("stress", "Ма́ма тут."),
        ("fenced", "```uk\nКод не має потрапити до пошуку.\n```"),
        ("fenced-tilde", "~~~uk\nКод не має потрапити до пошуку.\n~~~"),
        ("comment", "<!-- Коментар не має потрапити до пошуку. -->"),
        ("phrase", "Добрий де́нь, друзі!"),
        ("phrase-partial", "Добрий гарний день, друзі!"),
        ("cap-form", "Тести бувають складними."),
        *[(f"cap-exact-{number}", "Тест.") for number in range(1, 8)],
    ]
    for slug, content in modules:
        module_dir = track_root / slug
        module_dir.mkdir(parents=True)
        (module_dir / "module.md").write_text(content, encoding="utf-8")
    (track_root / "exact" / "module.mdx").write_text("Бакалаврат також є в MDX.", encoding="utf-8")
    (curriculum_root / "curriculum.yaml").write_text(
        yaml.safe_dump(
            {"levels": {"b1": {"modules": [slug for slug, _content in modules]}}},
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    manifest_path = tmp_path / "lexicon-manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "entries": [
                    {"lemma": "бакалаврат", "course_usage": []},
                    {"lemma": "кіт", "course_usage": []},
                    {"lemma": "замок", "course_usage": []},
                    {"lemma": "замка", "course_usage": []},
                    {"lemma": "спільний", "course_usage": []},
                    {"lemma": "інший", "course_usage": []},
                    {"lemma": "м'яч", "course_usage": []},
                    {"lemma": "мама", "course_usage": []},
                    {"lemma": "код", "course_usage": []},
                    {"lemma": "коментар", "course_usage": []},
                    {"lemma": "добрий день", "course_usage": []},
                    {"lemma": "тест", "course_usage": []},
                    {"lemma": "готове", "course_usage": [{"track": "b1", "module_num": 99, "slug": "existing"}]},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return curriculum_root, manifest_path, {slug: index for index, (slug, _content) in enumerate(modules, start=1)}


def _fake_vesum_forms(lemma: str) -> list[dict[str, str]]:
    return {
        "кіт": [{"word_form": "коти"}],
        "замок": [{"word_form": "замки"}],
        "замка": [{"word_form": "замки"}],
        "інший": [{"word_form": "спільний"}],
        "тест": [{"word_form": "тести"}],
    }.get(lemma, [])


def _slugs(rows: tuple[dict[str, object], ...]) -> list[str]:
    return [str(row["slug"]) for row in rows]

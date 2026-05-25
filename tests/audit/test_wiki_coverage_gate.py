from __future__ import annotations

from typing import Any

from scripts.audit.wiki_coverage_gate import check_wiki_coverage, parse_implementation_map
from scripts.build.phases.implementation_map import seed_implementation_map

BAN_1_RULE = (
    "При викладанні теми «Мій ранок» та семантики зворотних дієслів категорично заборонено "
    "використовувати будь-які російськомовні пояснення, паралелі чи фонетичні порівняння. "
    "Це абсолютна вимога деколонізованої педагогіки [S9]."
)
BAN_4_RULE = (
    "У лексичному наповненні теми ранкової рутини слід рішуче відкидати русизми, суржик "
    "та кальки, які можуть випадково просочитися в тексти. Слід суворо контролювати чистоту "
    "словника: використовуємо виключно «рушник» (не «полотенце»), «сніданок» (не «завтрак»), "
    "«одягатися» (не «одіватися») [S2, S3]. Процес навчання має занурювати студента в "
    "автентичний простір, де панує українська мова без сторонніх домішок [S3]. Будь-які "
    "конструкції, що вказують на вік, на кшталт «Я маю N років» (калька) беззастережно "
    "замінюються на питомо українські: «Мені N років» [S8, S9]."
)


def _ban_manifest(rule: str) -> dict[str, Any]:
    return {
        "slug": "fixture",
        "wiki_path": "wiki/pedagogy/a1/fixture.md",
        "sequence_steps": [],
        "l2_errors": [],
        "phonetic_rules": [],
        "decolonization_bans": [
            {
                "id": "ban-1",
                "rule": rule,
                "source_lines": "50",
            }
        ],
        "external_resources": [],
    }


def _claim() -> dict[str, dict[str, str]]:
    return {
        "ban-1": {
            "artifact": "module.md",
            "location": "whole file",
            "treatment": "decolonization ban treatment",
        }
    }


def _ban_result(report: dict[str, Any]) -> dict[str, Any]:
    return next(item for item in report["obligations"] if item["obligation_id"] == "ban-1")


def test_decolonization_ban_substance_required_passes_when_pair_present() -> None:
    manifest = _ban_manifest(BAN_4_RULE)

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map=_claim(),
        module_md=(
            "Use «рушник» (не «полотенце»), «сніданок» (не «завтрак»), "
            "and «одягатися» (не «одіватися»). Prefer «Мені N років» over "
            "the calque «Я маю N років»."
        ),
        activities_yaml="[]",
        seeded_map=seed_implementation_map(manifest),
    )

    result = _ban_result(report)
    assert report["passed"] is True
    assert result["status"] == "PASS"
    assert result["reason"] == "ban_substance_present"
    assert result["subtype"] == "substance_required"


def test_decolonization_ban_substance_required_fails_when_pair_missing() -> None:
    manifest = _ban_manifest(BAN_4_RULE)

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map=_claim(),
        module_md="This paragraph is present but does not include the lexical substitutions.",
        activities_yaml="[]",
        seeded_map=seed_implementation_map(manifest),
    )

    result = _ban_result(report)
    assert report["passed"] is False
    assert result["status"] == "FAIL"
    assert result["reason"] == "ban_substance_missing"
    assert result["subtype"] == "substance_required"


def test_decolonization_ban_absence_required_passes_automatically() -> None:
    manifest = _ban_manifest(BAN_1_RULE)

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map=_claim(),
        module_md="This module teaches the Ukrainian morning routine with Ukrainian-only framing.",
        activities_yaml="[]",
        seeded_map=seed_implementation_map(manifest),
    )

    result = _ban_result(report)
    assert report["passed"] is True
    assert result["status"] == "PASS"
    assert result["reason"] == "absence_obligation_assumed_satisfied"
    assert result["subtype"] == "absence_required"


def test_decolonization_ban_legacy_manifest_without_subtype_field() -> None:
    manifest = _ban_manifest(BAN_1_RULE)

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map=_claim(),
        module_md="This module avoids the prohibited framing.",
        activities_yaml="[]",
    )

    result = _ban_result(report)
    assert report["passed"] is False
    assert result["status"] == "FAIL"
    assert result["reason"] == "ban_substance_missing"
    assert "subtype" not in result


# Regression tests for two bugs that masked the build #6 a1/my-morning gate
# (2026-05-21). Both fixes are required for the gate to recognise content
# the writer and correction loop actually emitted.


def _sequence_step_manifest() -> dict[str, Any]:
    return {
        "slug": "fixture",
        "wiki_path": "wiki/pedagogy/a1/fixture.md",
        "sequence_steps": [
            {
                "id": "step-5",
                "heading": (
                    "Крок 5: Розширення лексичного контексту. "
                    "Тема ранкової рутини наповнюється іменниками "
                    "(вода, зарядка, сніданок) та прислівниками "
                    "часу і частотності (раненько, завжди, ніколи)."
                ),
                "step_num": 5,
                "required_claim": (
                    "Крок 5: Розширення лексичного контексту. "
                    "Тема ранкової рутини наповнюється іменниками "
                    "(вода, зарядка, сніданок) та прислівниками "
                    "часу і частотності (раненько, завжди, ніколи)."
                ),
                "source_lines": "31",
            }
        ],
        "l2_errors": [],
        "phonetic_rules": [],
        "decolonization_bans": [],
        "external_resources": [],
    }


def _phonetic_l2_error_manifest() -> dict[str, Any]:
    return {
        "slug": "fixture",
        "wiki_path": "wiki/pedagogy/a1/fixture.md",
        "sequence_steps": [],
        "l2_errors": [
            {
                "id": "err-2",
                "incorrect": "Вимова: [прокидайешся]",
                "correct": "Вимова: [прокидайес':а]",
                "why": (
                    "Побуквене прочитання. Учень намагається чітко "
                    "вимовити звук [ш], хоча українська норма вимагає "
                    "повної асиміляції в подовжений м'який [с':а]."
                ),
                "treatment": "contrast_pair",
                "source_lines": "40",
            }
        ],
        "phonetic_rules": [],
        "decolonization_bans": [],
        "external_resources": [],
    }


def test_sequence_step_passes_when_h1_title_collides_with_h2_section() -> None:
    """`_location_text` must prefer the deeper heading when an H1 module
    title and an H2 section share the same name. The build-#6 regression:
    module starts with `# Мій ранок` (title) and contains `## Мій ранок`
    (section); the gate was scoping to the H1 title-only block and
    failing step-5 even though the section had the required substance."""
    manifest = _sequence_step_manifest()
    module_md = (
        "# Мій ранок\n\n"
        "Two roommates compare their mornings. Listen for **-ся**.\n\n"
        "## Діалоги\n\nDialogue content here.\n\n"
        "## Дієслова на -ся\n\nGrammar content here.\n\n"
        "## Мій ранок\n\n"
        "**Sequence words** — these are the connective tissue:\n\n"
        "- **спочатку** — first\n- **потім** — then\n"
        "- **нарешті** — finally\n- **завжди** — always\n\n"
        "Build a narrative from **іменниками** like **сніданок** "
        "and **зарядка**, plus **прислівниками** of time.\n\n"
        "## Підсумок\n\nWrap-up here.\n"
    )
    implementation_map = {
        "step-5": {
            "artifact": "module.md",
            "location": "§Мій ранок (sequence-words + nouns block)",
            "treatment": "in-prose vocabulary expansion",
        }
    }

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map=implementation_map,
        module_md=module_md,
        activities_yaml="[]",
        seeded_map=seed_implementation_map(manifest),
    )

    step_result = next(
        item for item in report["obligations"] if item["obligation_id"] == "step-5"
    )
    assert step_result["status"] == "PASS", (
        f"step-5 should PASS when H2 section has the substance, even "
        f"with a colliding H1 title; got reason={step_result['reason']!r}"
    )


def test_sequence_step_h2_section_includes_h3_subsection_content() -> None:
    """Build-#8 regression: PR #2184's `_location_text` correctly picks
    the H2 section over the H1 module title, but ended the section at
    the next heading regardless of depth. When the H2 contains H3
    sub-sections (writer uses `### Крок N: ...` markers), the returned
    text is only the H2 intro + space before the first H3 — all H3
    sub-content is excluded from substance matching.

    The H3 is structurally INSIDE the H2 section; the section boundary
    should be the next heading whose depth is <= chosen depth (a
    sibling or shallower heading), so H3+ sub-content stays included.

    Build #8 of a1/my-morning ended at 17/18 with this exact shape:
    only the parent H2 matched (writer's H3 title diverged from the
    implementation_map's subsection name), and the returned 620-char
    H2 intro excluded the H3 paradigm tables that carried the
    substance-term overlap step-5's claim needed."""
    manifest = _sequence_step_manifest()
    module_md = (
        "## Дієслова на -ся\n\n"
        "Short H2 intro paragraph that mentions ранкової only briefly.\n\n"
        "### Крок 1: Шаблон\n\nReader paradigm content here.\n\n"
        "### Крок 2: Зворотні дієслова\n\n"
        "Substance lives here: іменниками вода зарядка сніданок "
        "прислівниками часу частотності раненько швиденько завжди "
        "ніколи — all the wiki-claim stems the substance check needs.\n\n"
        "## Підсумок\n\nWrap-up.\n"
    )
    implementation_map = {
        "step-5": {
            "artifact": "module.md",
            "location": "§Дієслова на -ся",
            "treatment": "in-prose vocabulary block in H3 sub-section",
        }
    }

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map=implementation_map,
        module_md=module_md,
        activities_yaml="[]",
        seeded_map=seed_implementation_map(manifest),
    )

    step_result = next(
        item for item in report["obligations"] if item["obligation_id"] == "step-5"
    )
    assert step_result["status"] == "PASS", (
        f"H2 section must include its H3 sub-section content when "
        f"computing target_text; got reason={step_result['reason']!r}"
    )


def _phonetic_rule_manifest() -> dict[str, Any]:
    """Manifest for testing phonetic_rule obligations.

    Mirrors the a1/my-morning wiki obligations for `-ться → [ц':а]` and
    `-ся → [с':а]` rules — the two phon-2 / phon-3 obligations whose
    `claimed_location_missing` failure motivated PR #2207's resolver
    fallback (see `test_phonetic_rule_falls_back_to_whole_artifact_when_location_unresolved`).
    """
    return {
        "slug": "fixture",
        "wiki_path": "wiki/pedagogy/a1/fixture.md",
        "sequence_steps": [],
        "l2_errors": [],
        "phonetic_rules": [
            {
                "id": "phon-2",
                "written": "-ться",
                "spoken": "[ц':а]",
                "treatment": "explicit_explanation",
                "source_lines": "15",
            }
        ],
        "decolonization_bans": [],
        "external_resources": [],
    }


def test_phonetic_rule_falls_back_to_whole_artifact_when_location_unresolved() -> None:
    """`_location_text` must degrade gracefully when the writer's claim
    location is a descriptive phrase that doesn't anchor to a heading.

    Build #14 of a1/my-morning (2026-05-22) wrote the `-ться → [ц':а]`
    rule into a `:::caution[Спелінг ≠ Вимова]` block under
    `## Дієслова на -ся`. The writer's implementation_map for phon-2
    described the location as `"same :::caution block, bullet 2"` —
    accurate prose, but not a heading and not a literal substring of the
    module. The resolver returned empty target_text → FAIL with
    `claimed_location_missing`, even though both the `written` (-ться)
    and `spoken` ([ц':а]) markers were present in the module a few lines
    apart.

    The fix: when no heading matches AND the location isn't a literal
    substring of the artifact, fall back to whole-artifact matching. The
    obligation-specific substance check (phonetic_rule requires both
    `written` and `spoken` to appear in `target_text`) is the real
    correctness gate; writer drift on the descriptive `location` field
    must not silently fail obligations whose content is genuinely present.
    """
    manifest = _phonetic_rule_manifest()
    module_md = (
        "## Дієслова на -ся\n\n"
        "Intro paragraph.\n\n"
        ":::caution[Спелінг ≠ Вимова]\n"
        "Spelling diverges from pronunciation here:\n\n"
        "- Written **-ться** → spoken **[ц':а]**: прокидається → [прокидайец':а].\n"
        "- Written **-ся** → spoken **[с':а]**: прокидаюся → [прокидайус':а].\n"
        ":::\n"
    )
    implementation_map = {
        "phon-2": {
            "artifact": "module.md",
            # Writer's descriptive prose anchor: no `## same :::caution block`
            # heading exists, and this string is not a substring of the
            # module either. Pre-fix behaviour: FAIL claimed_location_missing.
            "location": "same :::caution block, bullet 2",
            "treatment": "explicit IPA",
        }
    }

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map=implementation_map,
        module_md=module_md,
        activities_yaml="[]",
        seeded_map=seed_implementation_map(manifest),
    )

    phon_result = next(
        item for item in report["obligations"] if item["obligation_id"] == "phon-2"
    )
    assert phon_result["status"] == "PASS", (
        f"phon-2 must PASS via whole-artifact fallback when the writer's "
        f"location string doesn't anchor to a heading and the substance "
        f"(-ться + [ц':а]) is present somewhere in module.md; got "
        f"reason={phon_result['reason']!r}"
    )


def test_phonetic_rule_still_fails_when_substance_absent_anywhere() -> None:
    """The whole-artifact fallback must NOT bypass the substance check.

    The fix in `_location_text` makes location a hint rather than a hard
    contract, but the obligation-specific substance check still gates
    correctness. If the writer claims a phon obligation is satisfied but
    neither the `written` nor the `spoken` markers appear anywhere in
    the artifact, the gate must still FAIL — just with the more accurate
    `phonetic_rule_missing` reason instead of `claimed_location_missing`.
    """
    manifest = _phonetic_rule_manifest()
    module_md = (
        "## Дієслова на -ся\n\n"
        "Plain paragraph about morning routines. No reflexive ending\n"
        "discussion here, no phonetic transcription, just narrative prose.\n"
    )
    implementation_map = {
        "phon-2": {
            "artifact": "module.md",
            "location": "same :::caution block, bullet 2",
            "treatment": "explicit IPA",
        }
    }

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map=implementation_map,
        module_md=module_md,
        activities_yaml="[]",
        seeded_map=seed_implementation_map(manifest),
    )

    phon_result = next(
        item for item in report["obligations"] if item["obligation_id"] == "phon-2"
    )
    assert phon_result["status"] == "FAIL", (
        "phon-2 must FAIL when neither the written nor the spoken marker is "
        "present anywhere in the module — the location fallback must not "
        "create a false-positive escape hatch"
    )
    assert phon_result["reason"] == "phonetic_rule_missing", (
        f"FAIL reason must now reflect the actual substance gap, not the "
        f"location-resolution failure; got {phon_result['reason']!r}"
    )


def test_l2_error_passes_when_marker_contains_apostrophe() -> None:
    """`_activity_text` must surface activity content without YAML re-
    serialisation double-escaping apostrophes. The build-#6 regression:
    `correction: \"Вимова: [прокидайес':а]\"` round-tripped through
    `yaml.safe_dump` as `[прокидайес'':а]` (double apostrophe), so the
    marker substring match failed even though the artifact was correct."""
    manifest = _phonetic_l2_error_manifest()
    activities_yaml = (
        "- id: act-5\n"
        "  type: error-correction\n"
        "  title: Fix the trap forms\n"
        "  items:\n"
        "    - sentence: 'Вимова: [прокидайешся]'\n"
        "      error: 'Вимова: [прокидайешся]'\n"
        "      correction: \"Вимова: [прокидайес':а]\"\n"
        "      explanation: phonetic assimilation explanation.\n"
    )
    implementation_map = {
        "err-2": {
            "artifact": "activities.yaml",
            "location": "act-5 item 2",
            "treatment": "contrast_pair for phonetic assimilation",
        }
    }

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map=implementation_map,
        module_md="# Module body unrelated to err-2.\n",
        activities_yaml=activities_yaml,
        seeded_map=seed_implementation_map(manifest),
    )

    err_result = next(
        item for item in report["obligations"] if item["obligation_id"] == "err-2"
    )
    assert err_result["status"] == "PASS", (
        f"err-2 should PASS when activity contains the correct apostrophe "
        f"marker; got reason={err_result['reason']!r}"
    )


def test_l2_error_resolves_via_title_when_workbook_activity_omits_id() -> None:
    """`_activity_text` MUST fall back to ``title`` matching when the writer
    targets a workbook activity, because workbook activities legitimately
    omit ``id`` per ``scripts/build/phases/linear-write.md`` L700 (#2218).

    The codex-tools build-205831 regression: writer packed 6 ``err-N``
    items into one workbook activity titled
    ``workbook error-correction item 5`` and emitted
    ``location: workbook error-correction item N`` per row. The pre-fix
    resolver only matched on ``activity.id``, so every workbook row hard-
    failed ``claimed_location_missing`` even though the activity's
    flattened text contained the required contrast pair.
    """
    manifest = _phonetic_l2_error_manifest()
    activities_yaml = (
        "- type: error-correction\n"
        "  title: workbook error-correction item 5\n"
        "  items:\n"
        "    - sentence: 'Вимова: [прокидайешся]'\n"
        "      error: 'Вимова: [прокидайешся]'\n"
        "      correction: \"Вимова: [прокидайес':а]\"\n"
        "      explanation: assimilation rule.\n"
    )
    implementation_map = {
        "err-2": {
            "artifact": "activities.yaml",
            # Codex's actual claim string, not present anywhere as an
            # activity id (no `id` field on workbook activity).
            "location": "workbook error-correction item 2",
            "treatment": "sentence/error/correction contrast",
        }
    }

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map=implementation_map,
        module_md="# Module body unrelated to err-2.\n",
        activities_yaml=activities_yaml,
        seeded_map=seed_implementation_map(manifest),
    )

    err_result = next(
        item for item in report["obligations"] if item["obligation_id"] == "err-2"
    )
    assert err_result["status"] == "PASS", (
        f"err-2 must PASS via title-substring fallback when the writer's "
        f"location string overlaps the workbook activity's `title` field; "
        f"got reason={err_result['reason']!r}"
    )


def test_l2_error_resolves_via_bare_activities_yaml_location() -> None:
    """When the writer copies the seeded ``location_hint: \"activities.yaml\"``
    verbatim, ``_activity_text`` MUST return all activities flattened so the
    substance check has a chance to find the markers.

    ``scripts/build/phases/implementation_map.py::_location_hint`` seeds
    activity-targeted obligations with the bare string ``\"activities.yaml\"``.
    Pre-fix resolver returned empty string when no activity ``id`` matched
    that literal, hard-failing every faithful copy of the seeded hint.
    """
    manifest = _phonetic_l2_error_manifest()
    activities_yaml = (
        "- type: error-correction\n"
        "  title: Fix the contrast pair\n"
        "  items:\n"
        "    - sentence: 'Вимова: [прокидайешся]'\n"
        "      error: 'Вимова: [прокидайешся]'\n"
        "      correction: \"Вимова: [прокидайес':а]\"\n"
        "      explanation: assimilation rule.\n"
    )
    implementation_map = {
        "err-2": {
            "artifact": "activities.yaml",
            "location": "activities.yaml",
            "treatment": "sentence/error/correction contrast",
        }
    }

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map=implementation_map,
        module_md="# Module body unrelated to err-2.\n",
        activities_yaml=activities_yaml,
        seeded_map=seed_implementation_map(manifest),
    )

    err_result = next(
        item for item in report["obligations"] if item["obligation_id"] == "err-2"
    )
    assert err_result["status"] == "PASS", (
        f"err-2 must PASS when the writer's location equals the seeded "
        f"bare-artifact hint and the contrast pair is present anywhere "
        f"in activities.yaml; got reason={err_result['reason']!r}"
    )


def test_parse_implementation_map_accepts_compact_pipe_rows_on_same_line() -> None:
    """Codex sometimes emits compact implementation-map rows without
    ``obligation_id:`` labels. The parser must still recognize every row,
    even when multiple rows share one ``<implementation_map>`` line."""
    implementation_map = (
        "<implementation_map>"
        "err-1 | activities.yaml | workbook error-correction | first contrast. "
        "err-2 | activities.yaml | workbook error-correction | second contrast. "
        "ban-1 | module.md | §Intro | absence of banned framing."
        "</implementation_map>"
    )

    parsed = parse_implementation_map(implementation_map)

    assert parsed["err-1"]["artifact"] == "activities.yaml"
    assert parsed["err-1"]["location"] == "workbook error-correction"
    assert parsed["err-2"]["treatment"] == "second contrast."
    assert parsed["ban-1"]["artifact"] == "module.md"


def test_parse_implementation_map_accepts_compact_markdown_table_rows() -> None:
    implementation_map = """
<implementation_map>
| err-1 | activities.yaml | workbook error-correction | first contrast. |
| err-2 | activities.yaml | workbook fill-in review | second contrast. |
| ban-1 | module.md | §Intro | absence of banned framing. |
</implementation_map>
"""

    parsed = parse_implementation_map(implementation_map)

    assert parsed["err-1"]["artifact"] == "activities.yaml"
    assert parsed["err-1"]["treatment"] == "first contrast."
    assert parsed["err-2"]["location"] == "workbook fill-in review"
    assert parsed["err-2"]["treatment"] == "second contrast."
    assert parsed["ban-1"]["artifact"] == "module.md"


def test_l2_error_passes_with_compact_pipe_workbook_location() -> None:
    """The compact Codex pipe-map shape plus a generic workbook location
    should widen to all activities, then let the substance check decide."""
    manifest = _phonetic_l2_error_manifest()
    activities_yaml = (
        "- type: error-correction\n"
        "  title: Редагування типових помилок\n"
        "  items:\n"
        "    - sentence: 'Вимова: [прокидайешся]'\n"
        "      error: 'Вимова: [прокидайешся]'\n"
        "      correction: \"Вимова: [прокидайес':а]\"\n"
        "      explanation: assimilation rule.\n"
    )
    implementation_map = (
        "<implementation_map>"
        "err-2 | activities.yaml | workbook error-correction | sentence/error/correction contrast."
        "</implementation_map>"
    )

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map=implementation_map,
        module_md="# Module body unrelated to err-2.\n",
        activities_yaml=activities_yaml,
        seeded_map=seed_implementation_map(manifest),
    )

    err_result = next(
        item for item in report["obligations"] if item["obligation_id"] == "err-2"
    )
    assert err_result["status"] == "PASS", (
        f"err-2 must PASS from compact pipe-map claim when the workbook "
        f"activity contains the contrast pair; got reason={err_result['reason']!r}"
    )


def test_l2_error_widens_for_any_workbook_aggregate_activity_type() -> None:
    """Workbook aggregate map locations name practice buckets, not stable ids.

    The resolver should therefore widen all ``workbook <type>`` references for
    known workbook activity types, not only the original error-correction case.
    The obligation substance check still decides whether the widened text is
    sufficient.
    """
    manifest = _phonetic_l2_error_manifest()
    activities_yaml = (
        "- type: error-correction\n"
        "  title: Comprehensive contrast review\n"
        "  items:\n"
        "    - sentence: 'Вимова: [прокидайешся]'\n"
        "      error: 'Вимова: [прокидайешся]'\n"
        "      correction: \"Вимова: [прокидайес':а]\"\n"
        "      explanation: assimilation rule.\n"
    )
    implementation_map = (
        "<implementation_map>"
        "err-2 | activities.yaml | workbook fill-in review | contrast in workbook bucket."
        "</implementation_map>"
    )

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map=implementation_map,
        module_md="# Module body unrelated to err-2.\n",
        activities_yaml=activities_yaml,
        seeded_map=seed_implementation_map(manifest),
    )

    err_result = next(
        item for item in report["obligations"] if item["obligation_id"] == "err-2"
    )
    assert err_result["status"] == "PASS", (
        f"err-2 must PASS when a known workbook aggregate type widens to the "
        f"activity text and the contrast pair is present; got "
        f"reason={err_result['reason']!r}"
    )


def test_l2_error_still_fails_when_workbook_activity_lacks_substance() -> None:
    """Title-fallback resolution MUST NOT bypass the substance check.

    Companion to ``test_phonetic_rule_still_fails_when_substance_absent_anywhere``:
    if ``_activity_text`` widens the search window via title fallback OR
    bare-artifact fallback, the obligation-specific substance check must
    still reject activities that don't contain the required
    ``expected_error_value`` / ``expected_correction_value`` markers. The
    gate's leniency is a hint-resolution concession, not a substance
    waiver.
    """
    manifest = _phonetic_l2_error_manifest()
    activities_yaml = (
        "- type: order\n"
        "  title: workbook error-correction item 5\n"
        "  items:\n"
        "    - Спочатку я прокидаюся.\n"
        "    - Потім я вмиваюся.\n"
        "    - Нарешті я йду на роботу.\n"
        "  correct_order: [0, 1, 2]\n"
    )
    implementation_map = {
        "err-2": {
            "artifact": "activities.yaml",
            "location": "workbook error-correction item 2",
            "treatment": "sentence/error/correction contrast",
        }
    }

    report = check_wiki_coverage(
        manifest=manifest,
        implementation_map=implementation_map,
        module_md="# Module body unrelated to err-2.\n",
        activities_yaml=activities_yaml,
        seeded_map=seed_implementation_map(manifest),
    )

    err_result = next(
        item for item in report["obligations"] if item["obligation_id"] == "err-2"
    )
    assert err_result["status"] == "FAIL", (
        "err-2 must FAIL when the title-matched activity does NOT contain "
        "the required incorrect/correct contrast pair — the widened "
        "resolution window must not create a false-positive escape hatch"
    )

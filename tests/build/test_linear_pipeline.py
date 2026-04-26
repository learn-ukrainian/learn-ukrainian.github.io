from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
import yaml

from scripts.build import linear_pipeline
from scripts.common.thresholds import QG_DIMS


def _write_yaml(path: Path, payload: object) -> None:
    path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _small_plan() -> dict:
    return {
        "module": "a1-020",
        "level": "A1",
        "sequence": 20,
        "slug": "my-morning",
        "title": "Мій ранок",
        "subtitle": "Зворотні дієслова",
        "word_target": 20,
        "content_outline": [
            {
                "section": "Діалоги",
                "words": 20,
                "points": ["Introduce a morning dialogue."],
            }
        ],
        "references": [{"title": "Караман Grade 10, p.176"}],
    }


def test_plan_check_accepts_a1_20_plan() -> None:
    plan = linear_pipeline.plan_check(
        linear_pipeline.plan_path_for("a1", "my-morning")
    )

    assert plan["module"] == "a1-020"
    assert plan["sequence"] == 20
    assert plan["word_target"] == 1200


def test_plan_check_rejects_missing_required_key(tmp_path: Path) -> None:
    plan = _small_plan()
    plan.pop("references")
    path = tmp_path / "bad.yaml"
    _write_yaml(path, plan)

    with pytest.raises(linear_pipeline.LinearPipelineError, match="references"):
        linear_pipeline.plan_check(path)


def test_render_phase_prompt_fills_registered_tokens() -> None:
    plan_path = linear_pipeline.plan_path_for("a1", "my-morning")
    plan = linear_pipeline.plan_check(plan_path)
    context = linear_pipeline.writer_context(
        plan,
        plan_path.read_text(encoding="utf-8"),
        "Knowledge packet excerpt.",
    )

    rendered = linear_pipeline.render_phase_prompt(
        linear_pipeline.PROJECT_ROOT / "scripts/build/phases/linear-write.md",
        context,
    )

    assert "{NORTH_STAR}" not in rendered
    assert "{LESSON_CONTRACT}" not in rendered
    assert "{LEVEL}" not in rendered
    assert "TARGET: 15-35% Ukrainian." in rendered


@pytest.mark.parametrize(
    ("writer", "agent_name"),
    [
        ("claude-tools", "claude"),
        ("gemini-tools", "gemini"),
    ],
)
def test_invoke_writer_routes_supported_writers(
    tmp_path: Path,
    writer: str,
    agent_name: str,
) -> None:
    calls = []

    class Result:
        response = "writer output"

    def fake_invoker(agent: str, prompt: str, **kwargs: object) -> Result:
        calls.append((agent, prompt, kwargs))
        return Result()

    response = linear_pipeline.invoke_writer(
        "Write the module.",
        writer=writer,
        cwd=tmp_path,
        invoker=fake_invoker,
    )

    assert response == "writer output"
    assert calls[0][0] == agent_name
    assert calls[0][1] == "Write the module."
    assert calls[0][2]["mode"] == "workspace-write"
    assert calls[0][2]["cwd"] == tmp_path
    assert calls[0][2]["entrypoint"] == "dispatch"
    assert calls[0][2]["model"] == linear_pipeline.WRITER_DEFAULTS[writer]["model"]
    assert calls[0][2]["effort"] == linear_pipeline.WRITER_DEFAULTS[writer]["effort"]
    assert calls[0][2]["tool_config"] == {"output_format": "text"}


def test_invoke_writer_rejects_unknown_writer(tmp_path: Path) -> None:
    with pytest.raises(linear_pipeline.LinearPipelineError, match="Unknown writer"):
        linear_pipeline.invoke_writer("Write the module.", writer="bogus", cwd=tmp_path)


def test_parse_writer_output_strict_json() -> None:
    output = """```markdown file=module.md
# Мій ранок
```

```json file=activities.yaml
[
  {"id": "act-1", "type": "fill-in", "title": "Додайте -ся"}
]
```

```json file=vocabulary.yaml
[
  {
    "lemma": "ранок",
    "translation": "morning",
    "pos": "noun",
    "usage": "Мій ранок простий."
  }
]
```

```json file=resources.yaml
[
  {
    "title": "Караман Grade 10, p.176",
    "notes": "Зворотні дієслова: суфікс -ся означає дію на себе."
  }
]
```
"""

    artifacts = linear_pipeline.parse_writer_output_strict_json(output)

    assert tuple(artifacts) == linear_pipeline.WRITER_ARTIFACTS
    assert artifacts["module.md"].startswith("# Мій ранок")
    assert yaml.safe_load(artifacts["activities.yaml"])[0]["id"] == "act-1"
    assert yaml.safe_load(artifacts["vocabulary.yaml"])[0]["lemma"] == "ранок"
    assert yaml.safe_load(artifacts["resources.yaml"])[0]["title"] == (
        "Караман Grade 10, p.176"
    )


def test_parse_writer_output_rejects_yaml_block() -> None:
    output = """```markdown file=module.md
# Мій ранок
```

```yaml file=activities.yaml
- id: act-1
  type: fill-in
```

```json file=vocabulary.yaml
[
  {
    "lemma": "ранок",
    "translation": "morning",
    "pos": "noun",
    "usage": "Мій ранок простий."
  }
]
```

```json file=resources.yaml
[
  {"title": "Караман Grade 10, p.176"}
]
```
"""

    with pytest.raises(
        linear_pipeline.LinearPipelineError,
        match=r"activities\.yaml must be fenced as json",
    ):
        linear_pipeline.parse_writer_output_strict_json(output)


def test_parse_writer_output_rejects_invalid_json() -> None:
    output = """```markdown file=module.md
# Мій ранок
```

```json file=activities.yaml
[
  {"id": "act-1", "type": "fill-in",}
]
```

```json file=vocabulary.yaml
[
  {
    "lemma": "ранок",
    "translation": "morning",
    "pos": "noun",
    "usage": "Мій ранок простий."
  }
]
```

```json file=resources.yaml
[
  {"title": "Караман Grade 10, p.176"}
]
```
"""

    with pytest.raises(
        linear_pipeline.LinearPipelineError,
        match=r"activities\.yaml invalid JSON: .*line 2 column",
    ):
        linear_pipeline.parse_writer_output_strict_json(output)


def test_parse_writer_output_rejects_missing_artifact() -> None:
    output = """```markdown file=module.md
# Мій ранок
```
"""

    with pytest.raises(linear_pipeline.LinearPipelineError, match="missing"):
        linear_pipeline.parse_writer_output_strict_json(output)


def test_parse_writer_output_rejects_nan_and_infinity() -> None:
    """Strict-JSON contract rejects `NaN` / `Infinity` / `-Infinity` tokens.

    Adversarial review (Codex gpt-5.5, 2026-04-26): Python's `json.loads`
    accepts these by default; without `parse_constant=`, they would round-
    trip through `yaml.safe_dump` as `.nan` / `.inf`, leaking non-portable
    YAML into the artifact files. RFC 8259 forbids these tokens.
    """
    output = """```markdown file=module.md
# Мій ранок
```

```json file=activities.yaml
[
  {"id": "act-1", "type": "fill-in", "score": NaN}
]
```

```json file=vocabulary.yaml
[
  {
    "lemma": "ранок",
    "translation": "morning",
    "pos": "noun",
    "usage": "Мій ранок простий."
  }
]
```

```json file=resources.yaml
[
  {"title": "Караман Grade 10, p.176"}
]
```
"""

    with pytest.raises(
        linear_pipeline.LinearPipelineError,
        match=r"activities\.yaml invalid JSON.*NaN",
    ):
        linear_pipeline.parse_writer_output_strict_json(output)


def test_parse_writer_output_rejects_extra_fields_in_vocabulary() -> None:
    """Schema strict-extra-keys rejects hallucinated fields in vocabulary.yaml.

    Adversarial review (Gemini + Codex, 2026-04-26): without strict extra-
    key rejection, an LLM that hallucinates `{"lemma": ..., "kek": "..."}`
    would silently leak `kek` into the YAML artifact. The vocabulary schema
    has a tight allowlist; unknown keys must fail.
    """
    output = """```markdown file=module.md
# Мій ранок
```

```json file=activities.yaml
[
  {"id": "act-1", "type": "fill-in"}
]
```

```json file=vocabulary.yaml
[
  {
    "lemma": "ранок",
    "translation": "morning",
    "pos": "noun",
    "usage": "Мій ранок простий.",
    "kek": "hallucinated field"
  }
]
```

```json file=resources.yaml
[
  {"title": "Караман Grade 10, p.176"}
]
```
"""

    with pytest.raises(
        linear_pipeline.LinearPipelineError,
        match=r"vocabulary\.yaml.*unexpected fields \['kek'\]",
    ):
        linear_pipeline.parse_writer_output_strict_json(output)


def test_parse_writer_output_rejects_label_vs_fence_name_mismatch() -> None:
    """A label line + fence info that disagree must fail loud, not silently pick one.

    Adversarial review (Codex gpt-5.5, 2026-04-26): if the writer emits a
    plain `activities.yaml` label line followed by a fence with
    `file=vocabulary.yaml`, the prior code silently let the fence info
    override `pending_name`, recording content under the wrong artifact
    and surfacing a confusing "missing artifact" error downstream. Now
    we detect the mismatch at the source.
    """
    output = """```markdown file=module.md
# Мій ранок
```

activities.yaml

```json file=vocabulary.yaml
[
  {
    "lemma": "ранок",
    "translation": "morning",
    "pos": "noun",
    "usage": "Мій ранок простий."
  }
]
```

```json file=vocabulary.yaml
[
  {
    "lemma": "ранок",
    "translation": "morning",
    "pos": "noun",
    "usage": "Мій ранок простий."
  }
]
```

```json file=resources.yaml
[
  {"title": "Караман Grade 10, p.176"}
]
```
"""

    with pytest.raises(
        linear_pipeline.LinearPipelineError,
        match=r"mismatched artifact label and fence name.*activities\.yaml.*vocabulary\.yaml",
    ):
        linear_pipeline.parse_writer_output_strict_json(output)


def test_validate_writer_json_artifact_error_messages_include_actual_value() -> None:
    """Schema validation errors must include the actual value/type for redispatch.

    Adversarial review (Gemini + Codex, 2026-04-26): the prior error
    `requires {field} as str` didn't say what was actually present (None?
    int? empty string?). The corrective redispatch needs that context to
    correct the writer.
    """
    # Wrong type: lemma is int instead of str.
    with pytest.raises(
        linear_pipeline.LinearPipelineError,
        match=r"requires lemma as str, got int \(123\)",
    ):
        linear_pipeline._validate_writer_json_artifact(
            "vocabulary.yaml",
            [{"lemma": 123, "translation": "x", "pos": "n", "usage": "y"}],
        )

    # Empty string: now reports the non-empty constraint separately.
    with pytest.raises(
        linear_pipeline.LinearPipelineError,
        match=r"requires lemma as a non-empty string",
    ):
        linear_pipeline._validate_writer_json_artifact(
            "vocabulary.yaml",
            [{"lemma": "   ", "translation": "x", "pos": "n", "usage": "y"}],
        )


def test_parse_review_response_accepts_json_fence() -> None:
    response = """```json
{"score": 9.2, "evidence": "\\"Мій ранок простий.\\"", "verdict": "PASS"}
```"""

    parsed = linear_pipeline.parse_review_response(response, "pedagogical")

    assert parsed == {
        "score": 9.2,
        "evidence": '"Мій ранок простий."',
        "verdict": "PASS",
    }


def test_aggregate_llm_review_requires_exact_qg_dims() -> None:
    report = {
        dim: {
            "score": 9.0,
            "evidence": '"Specific quoted evidence."',
            "verdict": "PASS",
        }
        for dim in QG_DIMS
    }
    report["extra"] = {
        "score": 9.0,
        "evidence": '"Specific quoted evidence."',
        "verdict": "PASS",
    }

    with pytest.raises(linear_pipeline.LinearPipelineError, match="extra"):
        linear_pipeline.aggregate_llm_review(report, "A1")


def test_aggregate_llm_review_requires_quoted_evidence() -> None:
    report = {
        dim: {
            "score": 9.0,
            "evidence": '"Specific quoted evidence."',
            "verdict": "PASS",
        }
        for dim in QG_DIMS
    }
    report["tone"]["evidence"] = "Specific but unquoted evidence."

    with pytest.raises(linear_pipeline.LinearPipelineError, match="quoted excerpt"):
        linear_pipeline.aggregate_llm_review(report, "A1")


def _passing_qg_fixture(tmp_path: Path) -> tuple[Path, Path, Callable]:
    """Build a minimal but green QG fixture; tests then mutate one artifact."""
    plan_path = tmp_path / "plan.yaml"
    module_dir = tmp_path / "my-morning"
    module_dir.mkdir()
    _write_yaml(plan_path, _small_plan())
    (module_dir / "module.md").write_text(
        "\n".join(
            [
                "# Мій ранок",
                "",
                "## Діалоги",
                "",
                "This morning pattern is simple and concrete for careful adult",
                "learners. Use **прокидаюся**, **вмиваюся**, **одягаюся**,",
                "and **снідаю** before breakfast today clearly.",
                "",
                "<!-- INJECT_ACTIVITY: act-1 -->",
            ]
        ),
        encoding="utf-8",
    )
    _write_yaml(
        module_dir / "activities.yaml",
        [
            {
                "id": "act-1",
                "type": "fill-in",
                "title": "Додайте -ся",
                "items": [
                    {
                        "sentence": "Я вмиваю__.",
                        "answer": "ся",
                        "options": ["ся", "ти", "ми"],
                    }
                ],
            }
        ],
    )
    _write_yaml(
        module_dir / "vocabulary.yaml",
        [
            {
                "lemma": "прокидатися",
                "translation": "to wake up",
                "pos": "verb",
                "usage": "Я прокидаюся.",
            }
        ],
    )
    _write_yaml(
        module_dir / "resources.yaml",
        [{"title": "Караман Grade 10, p.176", "source_ref": "Караман Grade 10, p.176"}],
    )

    def fake_verify(words: list[str]) -> dict[str, list[dict]]:
        return {word: [{"lemma": word, "pos": "x", "tags": ""}] for word in words}

    return module_dir, plan_path, fake_verify


def test_ai_slop_gate_ignores_correction_field_in_error_correction_activity(
    tmp_path: Path,
) -> None:
    """The `correction:` YAML field name in error-correction activities is not slop.

    Round 3 (2026-04-26) failed `ai_slop_clean` because the `\\bCorrection:`
    contamination pattern (case-insensitive) matched the `correction:` field
    name in act-my-morning-9. That field is part of the schema, not prose.
    """
    module_dir, plan_path, fake_verify = _passing_qg_fixture(tmp_path)
    _write_yaml(
        module_dir / "activities.yaml",
        [
            {
                "id": "act-1",
                "type": "fill-in",
                "title": "Додайте -ся",
                "items": [
                    {
                        "sentence": "Я вмиваю__.",
                        "answer": "ся",
                        "options": ["ся", "ти", "ми"],
                    }
                ],
            },
            {
                "id": "act-2",
                "type": "error-correction",
                "title": "Знайдіть помилку",
                "sentences": [
                    {
                        "error": "Ти прокидаєштся о сьомій.",
                        "correction": "Ти прокидаєшся о сьомій.",
                        "translation": "You wake up at seven.",
                    }
                ],
            },
        ],
    )

    report = linear_pipeline.run_python_qg(
        module_dir, plan_path, verify_words_fn=fake_verify
    )

    assert report["gates"]["ai_slop_clean"]["passed"] is True
    assert report["gates"]["ai_slop_clean"]["hits"] == []


def test_vesum_gate_lowercases_before_lookup(tmp_path: Path) -> None:
    """Sentence-initial Ukrainian words must match VESUM lemmas.

    VESUM stores lemmas in lowercase. Before this fix, `Спочатку` (capital С,
    sentence-initial) returned 0 matches even though `спочатку` exists.
    """
    module_dir, plan_path, _ = _passing_qg_fixture(tmp_path)
    (module_dir / "module.md").write_text(
        "## Діалоги\n\nСпочатку я **прокидаюся**, потім вмиваюся.",
        encoding="utf-8",
    )

    received: list[list[str]] = []

    def lc_only_verify(words: list[str]) -> dict[str, list[dict]]:
        received.append(list(words))
        return {
            word: [{"lemma": word, "pos": "x", "tags": ""}] if word == word.lower() else []
            for word in words
        }

    report = linear_pipeline.run_python_qg(
        module_dir, plan_path, verify_words_fn=lc_only_verify
    )

    # All forwarded lookups are lowercase.
    assert received and all(word == word.lower() for word in received[0])
    assert report["gates"]["vesum_verified"]["passed"] is True


def test_vesum_gate_strips_phonetic_transcriptions_in_brackets(tmp_path: Path) -> None:
    """Phonetic notation in `[...]` must NOT be tokenized for VESUM lookup."""
    module_dir, plan_path, _fake_verify = _passing_qg_fixture(tmp_path)
    (module_dir / "module.md").write_text(
        "\n".join(
            [
                "## Діалоги",
                "",
                "Pronounce **вмивається** as [ц':а] and **вмиваєшся** as [с':а].",
            ]
        ),
        encoding="utf-8",
    )

    received: list[list[str]] = []

    def capturing_verify(words: list[str]) -> dict[str, list[dict]]:
        received.append(list(words))
        return {word: [{"lemma": word, "pos": "x", "tags": ""}] for word in words}

    linear_pipeline.run_python_qg(
        module_dir, plan_path, verify_words_fn=capturing_verify
    )

    forwarded = received[0]
    # Bracket fragments must not appear in the VESUM lookup set.
    for fragment in ("ц':а", "с':а", "ц", "т''с''а"):
        assert fragment not in forwarded, (
            f"phonetic fragment {fragment!r} leaked into VESUM lookup: {forwarded}"
        )


def test_vesum_gate_strips_hyphen_prefix_morpheme_notation(tmp_path: Path) -> None:
    """Conjugation suffix labels like `-шся`, `-ться` are morpheme notation.

    Ukrainian grammar texts conventionally write conjugation endings with a
    leading hyphen (compare English `-tion`, `-ness`). These fragments are
    not VESUM lemmas and must be excluded from lookup. Legitimate hyphenated
    compounds like `темно-синій` (preceded by a word character) stay intact.
    """
    module_dir, plan_path, _fake_verify = _passing_qg_fixture(tmp_path)
    (module_dir / "module.md").write_text(
        "\n".join(
            [
                "## Діалоги",
                "",
                "The ending **-шся** sounds like [с':а]. The ending **-ться**",
                "sounds like [ц':а]. Compare with the legitimate compound",
                "**темно-синій** which has both halves as real words.",
            ]
        ),
        encoding="utf-8",
    )

    received: list[list[str]] = []

    def capturing_verify(words: list[str]) -> dict[str, list[dict]]:
        received.append(list(words))
        return {word: [{"lemma": word, "pos": "x", "tags": ""}] for word in words}

    linear_pipeline.run_python_qg(
        module_dir, plan_path, verify_words_fn=capturing_verify
    )

    forwarded = received[0]
    # Morpheme-notation fragments are stripped.
    for fragment in ("шся", "ться"):
        assert fragment not in forwarded, (
            f"morpheme fragment {fragment!r} leaked into VESUM lookup: {forwarded}"
        )
    # The compound `темно-синій` survives intact (one match — the word regex
    # allows internal hyphens in word characters).
    assert "темно-синій" in forwarded


def test_vesum_gate_strips_fill_in_blank_syntax(tmp_path: Path) -> None:
    """Fill-in passages with `{ся}`, `{ться}` blank markers are not lemmas.

    The fill-in activity passage syntax `Я вмиваю{ся}. Він прокидає{ться}.`
    marks the blanks the student fills in. The content inside `{...}` is a
    suffix fragment, not a VESUM-checkable word.
    """
    module_dir, plan_path, _fake_verify = _passing_qg_fixture(tmp_path)
    _write_yaml(
        module_dir / "activities.yaml",
        [
            {
                "id": "act-1",
                "type": "fill-in",
                "title": "Додайте -ся",
                "passage": "Я вмиваю{ся}. Ти одягаєш{ся}. Він прокидає{ться}. Ми збираємо{ся}.",
            }
        ],
    )

    received: list[list[str]] = []

    def capturing_verify(words: list[str]) -> dict[str, list[dict]]:
        received.append(list(words))
        return {word: [{"lemma": word, "pos": "x", "tags": ""}] for word in words}

    linear_pipeline.run_python_qg(
        module_dir, plan_path, verify_words_fn=capturing_verify
    )

    forwarded = received[0]
    for fragment in ("ся", "ться"):
        assert fragment not in forwarded, (
            f"fill-in blank fragment {fragment!r} leaked into VESUM lookup: "
            f"{forwarded}"
        )
    # The verb stems around the blanks (вмиваю, одягаєш, etc.) ARE checked.
    assert "вмиваю" in forwarded
    assert "прокидає" in forwarded


def test_vesum_gate_skips_error_field_of_error_correction_activity(
    tmp_path: Path,
) -> None:
    """Intentional misspellings in `error:` fields must not be VESUM-checked.

    The `error-correction` activity type stores the typo students must fix in
    the `error:` field. Verifying that against VESUM would always fail.
    """
    module_dir, plan_path, _ = _passing_qg_fixture(tmp_path)
    _write_yaml(
        module_dir / "activities.yaml",
        [
            {
                "id": "act-1",
                "type": "error-correction",
                "title": "Знайдіть помилку",
                "sentences": [
                    {
                        "error": "Ти прокидаєштся о сьомій.",
                        "correction": "Ти прокидаєшся о сьомій.",
                        "translation": "You wake up at seven.",
                    }
                ],
            }
        ],
    )

    received: list[list[str]] = []

    def capturing_verify(words: list[str]) -> dict[str, list[dict]]:
        received.append(list(words))
        return {word: [{"lemma": word, "pos": "x", "tags": ""}] for word in words}

    linear_pipeline.run_python_qg(
        module_dir, plan_path, verify_words_fn=capturing_verify
    )

    # The intentionally-misspelled token (lowercased) is excluded.
    forwarded = received[0]
    assert "прокидаєштся" not in forwarded, (
        f"intentional typo leaked into VESUM lookup: {forwarded}"
    )
    # The correction (well-formed) IS verified.
    assert "прокидаєшся" in forwarded


def test_immersion_gate_strips_jsx_blocks_before_long_sentence_check(
    tmp_path: Path,
) -> None:
    """A `<DialogueBox lines=[...]/>` is one structural element, not one sentence.

    Round 3 (2026-04-26) failed `immersion.long_ukrainian_sentences` because
    the entire DialogueBox JSX prop array (10+ Ukrainian lines) was read as a
    single sentence. JSX must be stripped before sentence-boundary parsing.
    """
    module_dir, plan_path, fake_verify = _passing_qg_fixture(tmp_path)
    (module_dir / "module.md").write_text(
        "\n".join(
            [
                "## Діалоги",
                "",
                "Listen to **Ліна** and **Настя** talk about their morning routine.",
                "Pay attention to verbs ending in **-ся** and copy the pattern.",
                "",
                "<DialogueBox",
                '  characters={{ "Ліна": "Ліна", "Настя": "Настя" }}',
                "  lines={[",
                '    { speaker: "Ліна", text: "Коли ти прокидаєшся?", translation: "When?" },',
                '    { speaker: "Настя", text: "Я прокидаюся о сьомій.", translation: "Seven." },',
                '    { speaker: "Ліна", text: "Що ти робиш потім?", translation: "Then what?" },',
                '    { speaker: "Настя", text: "Вмиваюся, одягаюся і снідаю.", translation: "Routine." },',
                '    { speaker: "Ліна", text: "А коли ти йдеш на роботу?", translation: "When?" },',
                '    { speaker: "Настя", text: "О восьмій.", translation: "At eight." }',
                "  ]}",
                "/>",
                "",
                "<!-- INJECT_ACTIVITY: act-1 -->",
            ]
        ),
        encoding="utf-8",
    )

    report = linear_pipeline.run_python_qg(
        module_dir, plan_path, verify_words_fn=fake_verify
    )

    immersion = report["gates"]["immersion"]
    # The dialogue text inside JSX still counts toward the percent (Ukrainian
    # tokens were tokenized from the raw body), but the JSX block is no longer
    # treated as one giant sentence.
    assert immersion["long_ukrainian_sentences"] == [], (
        f"JSX block was incorrectly read as a long sentence: "
        f"{immersion['long_ukrainian_sentences']}"
    )


def test_run_python_qg_passes_structural_fixture(tmp_path: Path) -> None:
    plan_path = tmp_path / "plan.yaml"
    module_dir = tmp_path / "my-morning"
    module_dir.mkdir()
    _write_yaml(plan_path, _small_plan())
    (module_dir / "module.md").write_text(
        "\n".join(
            [
                "# Мій ранок",
                "",
                "## Діалоги",
                "",
                "This morning pattern is simple and concrete for careful adult",
                "learners. Use **прокидаюся**, **вмиваюся**, **одягаюся**,",
                "and **снідаю** before breakfast today clearly.",
                "",
                "<!-- INJECT_ACTIVITY: act-1 -->",
            ]
        ),
        encoding="utf-8",
    )
    _write_yaml(
        module_dir / "activities.yaml",
        [
            {
                "id": "act-1",
                "type": "fill-in",
                "title": "Додайте -ся",
                "items": [
                    {
                        "sentence": "Я вмиваю__.",
                        "answer": "ся",
                        "options": ["ся", "ти", "ми"],
                    }
                ],
            }
        ],
    )
    _write_yaml(
        module_dir / "vocabulary.yaml",
        [
            {
                "lemma": "прокидатися",
                "translation": "to wake up",
                "pos": "verb",
                "usage": "Я прокидаюся.",
            }
        ],
    )
    _write_yaml(
        module_dir / "resources.yaml",
        [{"title": "Караман Grade 10, p.176", "source_ref": "Караман Grade 10, p.176"}],
    )

    def fake_verify(words: list[str]) -> dict[str, list[dict]]:
        return {word: [{"lemma": word, "pos": "x", "tags": ""}] for word in words}

    report = linear_pipeline.run_python_qg(
        module_dir,
        plan_path,
        verify_words_fn=fake_verify,
    )

    assert report["gates"]["passed"] is True
    assert report["gates"]["russianisms_clean"]["passed"] is True
    assert report["gates"]["surzhyk_clean"]["passed"] is True
    assert report["gates"]["calques_clean"]["passed"] is True
    assert report["gates"]["paronym_clean"]["passed"] is True

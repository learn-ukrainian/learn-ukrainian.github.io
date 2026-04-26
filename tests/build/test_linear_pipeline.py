from __future__ import annotations

import json
import re
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


def test_vesum_gate_preserves_markdown_link_text(tmp_path: Path) -> None:
    """Markdown link text `[слово](url)` must reach VESUM, not be stripped.

    Adversarial review (Gemini, 2026-04-26): a too-broad `[...]` strip would
    consume the link text portion and hide misspellings inside `[слово](url)`
    from VESUM. Phonetic-bracket strip is now narrowed to short, no-space
    content so Markdown links survive intact.
    """
    module_dir, plan_path, _fake_verify = _passing_qg_fixture(tmp_path)
    (module_dir / "module.md").write_text(
        "## Діалоги\n\nПрочитай статтю на [Вікіпедії](https://uk.wikipedia.org).",
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
    # The link text "Вікіпедії" must reach VESUM (lowercased).
    assert "вікіпедії" in forwarded, (
        f"Markdown link text was stripped — would hide misspellings: {forwarded}"
    )


def test_vesum_gate_preserves_jsx_object_literal_strings(tmp_path: Path) -> None:
    """JSX object literals `{ speaker: "Маркіян", text: "..." }` must survive `_BRACES_RE`.

    Adversarial review (Codex, 2026-04-26): a too-broad `{...}` strip would
    consume JSX object rows along with their Ukrainian text, hiding
    misspellings in dialogue components from VESUM. Brace strip is now
    narrowed to fill-in-shape content (Ukrainian-letter-only).

    The sentinel name `Маркіян` must NOT live in
    `scripts.audit.config.PROPER_NAME_WHITELIST`; if a future change adds it,
    pick a different rare-but-real Ukrainian first name (e.g. `Северин`,
    `Зеновій`) so this test continues to probe the brace-strip path rather
    than the whitelist filter (#1602 round 3.5 surfaced this same trap when
    `Ліна` got whitelisted).
    """
    module_dir, plan_path, _fake_verify = _passing_qg_fixture(tmp_path)
    # A bare JSX object row outside a full component (in case the JSX block
    # regex doesn't consume it) — its Ukrainian text must reach VESUM.
    (module_dir / "module.md").write_text(
        '## Діалоги\n\nПриклад: { speaker: "Маркіян", text: "Прокидаюся рано." }',
        encoding="utf-8",
    )

    # Self-test the sentinel: if `Маркіян` slipped into PROPER_NAME_WHITELIST
    # since this test was written, the assertion below would silently weaken
    # to a no-op. Fail loud instead.
    from scripts.audit.config import PROPER_NAME_WHITELIST
    assert "Маркіян" not in PROPER_NAME_WHITELIST, (
        "Test sentinel `Маркіян` is now whitelisted; pick a different rare "
        "Ukrainian first name so the brace-strip path stays exercised."
    )

    received: list[list[str]] = []

    def capturing_verify(words: list[str]) -> dict[str, list[dict]]:
        received.append(list(words))
        return {word: [{"lemma": word, "pos": "x", "tags": ""}] for word in words}

    linear_pipeline.run_python_qg(
        module_dir, plan_path, verify_words_fn=capturing_verify
    )

    forwarded = received[0]
    for word in ("маркіян", "прокидаюся", "рано"):
        assert word in forwarded, (
            f"JSX object literal was stripped — would hide misspellings: "
            f"missing {word!r} in {forwarded}"
        )


def test_vesum_gate_strips_morpheme_fragment_with_underscore_bold(
    tmp_path: Path,
) -> None:
    """Underscore-bold `__-шся__` must strip the morpheme fragment.

    Adversarial review (Gemini, 2026-04-26): the original `\\B` lookbehind
    failed when the hyphen was preceded by `_` because Python treats `_` as
    a word character. The morpheme regex now uses an explicit lookbehind
    that excludes Ukrainian + Latin letters + digits + underscore.
    """
    module_dir, plan_path, _fake_verify = _passing_qg_fixture(tmp_path)
    (module_dir / "module.md").write_text(
        "## Діалоги\n\nThe ending __-шся__ sounds like [с':а].",
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
    assert "шся" not in forwarded, (
        f"morpheme fragment leaked despite underscore-bold context: {forwarded}"
    )


def test_vesum_gate_skips_nested_error_subtree_in_error_correction(
    tmp_path: Path,
) -> None:
    """Future schema `error: { text: "...", note: "..." }` must still skip the typo.

    Adversarial review (Gemini + Codex, 2026-04-26): the leaf-level skip
    predicate would let a nested `error:` subtree through (parent_key would
    be `text` or `note`, not `error`). The walker now skips the entire
    `error:` subtree, regardless of nesting.
    """
    module_dir, plan_path, _fake_verify = _passing_qg_fixture(tmp_path)
    _write_yaml(
        module_dir / "activities.yaml",
        [
            {
                "id": "act-1",
                "type": "error-correction",
                "title": "Знайдіть помилку",
                "sentences": [
                    {
                        "error": {
                            "text": "Ти прокидаєштся о сьомій.",
                            "note": "Зверніть увагу на закінчення.",
                        },
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

    forwarded = received[0]
    assert "прокидаєштся" not in forwarded, (
        f"intentional typo leaked from nested error: subtree: {forwarded}"
    )


def test_immersion_gate_recognizes_unicode_sentence_boundaries(
    tmp_path: Path,
) -> None:
    """Ukrainian dialogue punctuation `…`, `‼`, `⁇` must split sentences.

    Adversarial review (Codex, 2026-04-26): without these, a Ukrainian run
    like "Так… Потім вмиваюся… І одягаюся… Нарешті йду." was treated as one
    long sentence, producing a false long-sentence flag.
    """
    module_dir, plan_path, fake_verify = _passing_qg_fixture(tmp_path)
    (module_dir / "module.md").write_text(
        "## Діалоги\n\n"
        "Так… Потім вмиваюся… І одягаюся… Нарешті йду на роботу.",
        encoding="utf-8",
    )

    report = linear_pipeline.run_python_qg(
        module_dir, plan_path, verify_words_fn=fake_verify
    )

    # Without the `…` boundary, all 4 short sentences would join into one
    # 12-Ukrainian-word run, exceeding the >10 threshold.
    assert report["gates"]["immersion"]["long_ukrainian_sentences"] == [], (
        f"Ukrainian ellipsis was not treated as sentence boundary: "
        f"{report['gates']['immersion']['long_ukrainian_sentences']}"
    )


def test_immersion_gate_credits_ukrainian_in_jsx_text_props(tmp_path: Path) -> None:
    """JSX `text="..."` Ukrainian content counts; prop keys do NOT count.

    Adversarial review (Gemini + Codex, 2026-04-26): raw-body tokenization
    counted English JSX prop keys (`speaker`, `text`, `translation`) and
    English translation strings as English tokens, deflating the immersion
    percentage. Now the JSX block is stripped from the body, then string-
    valued Ukrainian inside JSX is added back via `_JSX_STRING_VALUE_RE`.
    """
    module_dir, plan_path, fake_verify = _passing_qg_fixture(tmp_path)
    # Body has English meta-narration prose AND a DialogueBox with Ukrainian
    # `text:` props. Without the fix, English prop keys + English
    # translations would dominate. With the fix, only learner-facing
    # Ukrainian inside JSX adds to the count.
    (module_dir / "module.md").write_text(
        "\n".join(
            [
                "## Діалоги",
                "",
                "<DialogueBox",
                "  characters={{}}",
                "  lines={[",
                '    { speaker: "Ліна", text: "Прокидаюся рано і вмиваюся." },',
                '    { speaker: "Настя", text: "А я снідаю і йду на роботу." },',
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

    pct = report["gates"]["immersion"]["pct"]
    # The body has effectively no English prose (one heading, one comment).
    # All counted tokens come from Ukrainian dialogue text. Prop keys
    # (`speaker`, `text`, `lines`, `characters`) are excluded; English
    # translations are absent. Immersion should be high (>50%).
    assert pct > 50.0, (
        f"JSX-extracted Ukrainian gave a too-low immersion pct: {pct}%; "
        "prop keys may still be counted as English tokens"
    )


def test_immersion_gate_strips_jsx_blocks_with_gt_in_prop_expressions(
    tmp_path: Path,
) -> None:
    """JSX prop expressions like `condition={count > 0}` must not break the strip.

    Regression guard for the gemini-code-assist review of PR #1599: the
    initial `_JSX_BLOCK_RE` used `[^<>]` for inner content, which terminated
    the match at the first standalone `>` inside a prop expression. That
    would re-introduce the long-sentence false positive this PR fixes.
    """
    module_dir, plan_path, fake_verify = _passing_qg_fixture(tmp_path)
    (module_dir / "module.md").write_text(
        "\n".join(
            [
                "## Діалоги",
                "",
                "<DialogueBox",
                "  condition={count > 0}",
                "  lines={[",
                '    { text: "Коли ти прокидаєшся?" },',
                '    { text: "Я прокидаюся о сьомій." },',
                '    { text: "Що ти робиш потім?" },',
                '    { text: "Вмиваюся, одягаюся і снідаю." },',
                '    { text: "А коли ти йдеш на роботу?" },',
                '    { text: "О восьмій." },',
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

    assert report["gates"]["immersion"]["long_ukrainian_sentences"] == [], (
        "JSX with `>` in a prop expression broke the regex strip and the "
        "DialogueBox lines were re-read as one giant sentence: "
        f"{report['gates']['immersion']['long_ukrainian_sentences']}"
    )


def test_immersion_gate_recognizes_start_of_string_bullets(tmp_path: Path) -> None:
    """A bullet list at the very start of body content is a sentence boundary.

    Regression guard for the gemini-code-assist review of PR #1599: the
    initial `sentence_split_re` required `\\n` before bullet markers, which
    miscategorized list items appearing immediately after frontmatter strip
    (no preceding newline). The split now anchors `(?:\\n|^)` so start-of-
    string bullets are recognized.
    """
    module_dir, plan_path, fake_verify = _passing_qg_fixture(tmp_path)
    # Module body opens directly with a bullet list of long Ukrainian
    # sentences. Each bullet IS a separate sentence — must not be conflated.
    (module_dir / "module.md").write_text(
        "\n".join(
            [
                "## Діалоги",
                "",
                "* Спочатку я **прокидаюся** о сьомій. Потім вмиваюся.",
                "* Потім я **одягаюся** і снідаю. Нарешті я йду на роботу.",
                "",
                "<!-- INJECT_ACTIVITY: act-1 -->",
            ]
        ),
        encoding="utf-8",
    )

    report = linear_pipeline.run_python_qg(
        module_dir, plan_path, verify_words_fn=fake_verify
    )

    # Each individual bullet contains <10 Ukrainian words — neither should
    # trip the long-sentence rule. If `^`-anchor were absent, the two bullets
    # plus their surrounding text might join into one >10-word run.
    assert report["gates"]["immersion"]["long_ukrainian_sentences"] == [], (
        f"start-of-string bullets joined into a long sentence: "
        f"{report['gates']['immersion']['long_ukrainian_sentences']}"
    )


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
    """Smoke test: the baseline `_passing_qg_fixture` produces a green report.

    Acts as the canary for run_python_qg. If a future change breaks the basic
    happy-path module shape, this test surfaces it before any of the targeted
    bugfix tests run.
    """
    module_dir, plan_path, fake_verify = _passing_qg_fixture(tmp_path)

    report = linear_pipeline.run_python_qg(
        module_dir, plan_path, verify_words_fn=fake_verify
    )

    assert report["gates"]["passed"] is True
    assert report["gates"]["russianisms_clean"]["passed"] is True
    assert report["gates"]["surzhyk_clean"]["passed"] is True
    assert report["gates"]["calques_clean"]["passed"] is True
    assert report["gates"]["paronym_clean"]["passed"] is True


# ---------------------------------------------------------------------------
# Round 3.5 prompt-tighten regression tests (#1602)
# ---------------------------------------------------------------------------


def test_render_component_props_schema_lists_required_and_optional() -> None:
    """A1's allowed types must each get a `required:` and `optional:` line.

    Round-3 (#1577) failed because the writer guessed `passage:` for `fill-in`
    and omitted `correct_order` on `order`. Surfacing the lesson-schema prop
    contract in the writer prompt is the cheapest fix.
    """
    allowed = "fill-in, order, match-up, quiz"
    rendered = linear_pipeline._render_component_props_schema(allowed)

    # Each allowed type must produce its own bullet block.
    for activity_type in ("fill-in", "order", "match-up", "quiz"):
        assert f"- {activity_type}:" in rendered, (
            f"Missing bullet for activity type {activity_type!r} in:\n{rendered}"
        )

    # Required-prop names must appear verbatim — these are the exact keys the
    # `_component_prop_gate` validator looks up.
    assert "items" in rendered, "FillIn / Order / MatchUp `items` prop missing"
    assert "correct_order" in rendered, (
        "Order `correct_order` prop missing — was the original round-3 failure"
    )

    # Required and optional must be on different lines so the writer can tell
    # them apart.
    assert "    required:" in rendered
    assert "    optional:" in rendered


def test_render_component_props_schema_filters_to_allowed_types() -> None:
    """The schema renderer must NOT leak forbidden activity types.

    Forbidden types (e.g. `cloze`, `essay-response`, `paleography-analysis`)
    have their own component-prop schemas in `lesson-schema.yaml`. If the
    renderer doesn't filter, the writer would see them as 'available' and
    reach for them. The filter mirrors `ALLOWED_ACTIVITY_TYPES` exactly.
    """
    rendered = linear_pipeline._render_component_props_schema("fill-in, quiz")

    # Allowed types appear.
    assert "- fill-in:" in rendered
    assert "- quiz:" in rendered
    # Forbidden / unmentioned types must NOT appear.
    assert "- cloze:" not in rendered
    assert "- essay-response:" not in rendered
    assert "- paleography-analysis:" not in rendered


def test_render_component_props_schema_resolves_nested_item_fields() -> None:
    """Nested array item types like `FillInItem[]` must show their fields.

    The writer needs to know that a `FillInItem` has `sentence`, `answer`,
    `options` — not just that the prop is `items: FillInItem[]`. Otherwise
    the prop shape is still ambiguous and we end up where round 3 ended.
    """
    rendered = linear_pipeline._render_component_props_schema("fill-in")

    # The nested-type expansion must list the FillInItem fields after the
    # array type annotation.
    fill_in_block = rendered.split("- fill-in:")[1].split("- ")[0]
    for field in ("sentence", "answer", "options"):
        assert field in fill_in_block, (
            f"FillInItem field {field!r} missing from rendered fill-in block:\n{fill_in_block}"
        )


def test_writer_context_populates_component_props_schema() -> None:
    """`writer_context` must surface `COMPONENT_PROPS_SCHEMA` for `.format()`.

    Without this, `render_phase_prompt` would raise `Unknown downstream
    prompt context keys` (forbid-extras) or leave `{COMPONENT_PROPS_SCHEMA}`
    unresolved in the prompt sent to the writer.
    """
    plan_path = linear_pipeline.plan_path_for("a1", "my-morning")
    plan = linear_pipeline.plan_check(plan_path)
    context = linear_pipeline.writer_context(
        plan,
        plan_path.read_text(encoding="utf-8"),
        "Knowledge packet excerpt.",
    )

    assert "COMPONENT_PROPS_SCHEMA" in context
    schema_text = context["COMPONENT_PROPS_SCHEMA"]
    assert "- fill-in:" in schema_text
    assert "    required:" in schema_text


def test_render_phase_prompt_resolves_component_props_schema() -> None:
    """The placeholder `{COMPONENT_PROPS_SCHEMA}` must be substituted.

    Asserts the full rendering path: token registered in `DOWNSTREAM_TOKENS`,
    populated by `writer_context`, substituted by `render_phase_prompt`, and
    no `{...}` placeholder left in the rendered output for the writer.
    """
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

    assert "{COMPONENT_PROPS_SCHEMA}" not in rendered
    # Concrete schema body landed in the prompt where the placeholder was.
    assert "- fill-in:" in rendered
    assert "    required:" in rendered


def test_linear_write_prompt_carries_anti_meta_narration_directive() -> None:
    """The writer prompt must explicitly forbid English meta-narration.

    Round-3 diagnostic (#1577) showed Gemini wrote chatty English intros
    ("Welcome to...", "Now that you have seen..."), blowing past
    `plan_sections` budgets and dropping immersion below the 15% floor.
    The fix is a direct prohibition in the prompt; this test guards
    against the directive being silently removed.
    """
    prompt_text = (
        linear_pipeline.PROJECT_ROOT / "scripts/build/phases/linear-write.md"
    ).read_text(encoding="utf-8")

    assert "No English meta-narration" in prompt_text, (
        "linear-write.md is missing the explicit anti-meta-narration directive"
    )
    # The directive references concrete forbidden phrases so the writer can
    # pattern-match. A future agent that wants to soften this should bring
    # data showing the chatty-intro failure mode is gone, not just delete it.
    for forbidden_phrase in ("Welcome to", "In this section we will learn"):
        assert forbidden_phrase in prompt_text, (
            f"Anti-meta-narration directive must name {forbidden_phrase!r} as a "
            f"forbidden phrase"
        )


def test_linear_write_prompt_references_component_props_schema_token() -> None:
    """The writer prompt must consume `{COMPONENT_PROPS_SCHEMA}` somewhere.

    If the token is registered in `DOWNSTREAM_TOKENS` and populated by
    `writer_context` but never referenced in the prompt, the writer never
    sees the schema and the bug recurs. Prevents a refactor from silently
    de-wiring the schema.
    """
    prompt_text = (
        linear_pipeline.PROJECT_ROOT / "scripts/build/phases/linear-write.md"
    ).read_text(encoding="utf-8")

    assert "{COMPONENT_PROPS_SCHEMA}" in prompt_text


def test_proper_name_whitelist_includes_round_3_5_additions() -> None:
    """`Караман`, `Ліна`, `Настя` (+ declined forms) must be whitelisted.

    A1/20 plan cites `Караман Grade 10, p.176` and the dialogue uses
    `Ліна` and `Настя` as speakers. Without the whitelist entries the
    `vesum_verified` gate fails on names VESUM was never going to know.
    Adversarial review (Gemini + Codex on PR #1603) flagged that exact
    surface forms only weren't enough — the writer may use vocative
    (`Лін!`, `Настю!`) or oblique cases (`Караманом`) freely. Common
    declined forms are included.
    """
    from scripts.audit.config import PROPER_NAME_WHITELIST

    for name in ("Караман", "Ліна", "Настя"):
        assert name in PROPER_NAME_WHITELIST, (
            f"Proper name {name!r} expected in PROPER_NAME_WHITELIST after #1602"
        )
    # Spot-check that the most common declined forms landed too.
    for declined in ("Ліну", "Ліно", "Настю", "Карамана", "Караманом"):
        assert declined in PROPER_NAME_WHITELIST, (
            f"Declined form {declined!r} expected in PROPER_NAME_WHITELIST "
            f"after Gemini/Codex review on PR #1603"
        )


def test_proper_name_whitelist_lc_observes_runtime_mutation() -> None:
    """`_proper_name_whitelist_lc` must NOT cache across mutations.

    Adversarial review (Gemini, 2026-04-26, PR #1603) flagged that an
    earlier `@functools.cache` decorator on this function created a silent
    test-isolation hazard — any test that mutated `PROPER_NAME_WHITELIST`
    (via monkeypatch / set.add) would not be observed by pipeline code.
    The decorator is gone; this test guards against it being reintroduced.
    """
    from scripts.audit.config import PROPER_NAME_WHITELIST

    sentinel = "ZZZ_TEST_SENTINEL_NOT_A_REAL_NAME_ZZZ"
    assert sentinel not in PROPER_NAME_WHITELIST  # paranoia
    baseline = linear_pipeline._proper_name_whitelist_lc()
    assert sentinel.lower() not in baseline

    PROPER_NAME_WHITELIST.add(sentinel)
    try:
        after_add = linear_pipeline._proper_name_whitelist_lc()
        assert sentinel.lower() in after_add, (
            "Mutation to PROPER_NAME_WHITELIST was not observed — has "
            "@functools.cache been reintroduced on _proper_name_whitelist_lc?"
        )
    finally:
        PROPER_NAME_WHITELIST.discard(sentinel)


def test_render_component_props_schema_warns_on_unresolved_allowed_type() -> None:
    """Allowed types with no schema entry must produce a `# WARNING:` line.

    Adversarial review (Codex, 2026-04-26, PR #1603) flagged that
    `phrase-table` is in `INLINE_ALLOWED_TYPES` for A1 but has
    `activity_type: null` in `docs/lesson-schema.yaml` (schema-generator
    drift, tracked separately as #1604). Earlier the renderer silently
    omitted such types — the writer wouldn't know NOT to use them, then
    `_component_prop_gate` would reject the activity with a cryptic error.
    The renderer now emits an explicit warning bullet so the writer is
    told off the type, and the build doesn't fail-fast on the unrelated
    drift bug.
    """
    rendered = linear_pipeline._render_component_props_schema(
        "fill-in, phrase-table, banana-rama-not-a-real-type"
    )

    assert "- fill-in:" in rendered
    # Each unresolved type gets its own WARNING bullet.
    for unresolved in ("phrase-table", "banana-rama-not-a-real-type"):
        assert f"- {unresolved}:" in rendered
        assert "# WARNING: no schema entry" in rendered, (
            f"Unresolved type {unresolved!r} did not produce a WARNING line; "
            f"rendered output was:\n{rendered}"
        )
    assert "DO NOT USE" in rendered
    # And the rendered output references the follow-up issue so future
    # readers can find context without grepping commit history.
    assert "#1604" in rendered


def test_render_component_props_schema_strips_tsdoc_from_raw_types() -> None:
    """Embedded `/** ... */` blocks must be stripped from raw type strings.

    Adversarial review (Gemini + Codex on PR #1603): `odd-one-out`'s
    `items` field has type `{ /** ... */ words: string[]; ... }[]` —
    the JSDoc comments leak into the rendered prompt verbatim, burning
    tokens and confusing the writer with TypeScript syntax. The renderer
    runs `_strip_tsdoc` on every raw type before formatting.
    """
    rendered = linear_pipeline._render_component_props_schema("odd-one-out")

    odd_block = rendered.split("- odd-one-out:")[1].split("- ")[0]
    # No raw TSDoc syntax should leak through.
    assert "/**" not in odd_block, (
        f"TSDoc block leaked into rendered odd-one-out output:\n{odd_block}"
    )
    assert "*/" not in odd_block
    assert "@schemaDescription" not in odd_block
    assert "@ukrainianText" not in odd_block
    # The cleaned type signature should still mention the inner field names
    # so the writer knows what to emit.
    for field in ("words", "correct", "explanation"):
        assert field in odd_block, (
            f"Field {field!r} disappeared from cleaned odd-one-out type:\n{odd_block}"
        )


def test_strip_tsdoc_collapses_whitespace() -> None:
    """`_strip_tsdoc` is the single point that handles raw-type cleanup."""
    raw = "{ /** * @schemaDescription Foo. */ name: string; /** Bar */ age: number; }[]"

    assert linear_pipeline._strip_tsdoc(raw) == "{ name: string; age: number; }[]"
    # No-op on already-clean strings.
    assert linear_pipeline._strip_tsdoc("string[]") == "string[]"
    # Empty-string safety.
    assert linear_pipeline._strip_tsdoc("") == ""


def test_linear_write_prompt_skeleton_example_matches_schema() -> None:
    """The literal `fill-in` example in `linear-write.md` must be valid.

    Adversarial review (Codex, 2026-04-26, PR #1603 BLOCKER #1) flagged
    that the original example showed `id/type/title` only, contradicting
    the new "Activity Component Props" section that says `fill-in`
    requires `items: FillInItem[]`. Self-contradicting prompts are worse
    than no prompt — the model resolves the conflict by picking whichever
    feels closer to its prior, and we lose control of the contract.

    This test reads `linear-write.md`, finds the `activities.yaml` JSON
    fenced block, parses it, and confirms each example object satisfies
    its declared `type`'s required props per `lesson-schema.yaml`. The
    same `_component_prop_gate` logic that catches writer outputs at
    runtime is reused here — drift between example and gate fails loud.
    """
    prompt_text = (
        linear_pipeline.PROJECT_ROOT / "scripts/build/phases/linear-write.md"
    ).read_text(encoding="utf-8")

    # Pull the JSON code block fenced as ```json file=activities.yaml.
    match = re.search(
        r"```json file=activities\.yaml\n(.*?)\n```",
        prompt_text,
        re.DOTALL,
    )
    assert match is not None, (
        "linear-write.md no longer contains a ```json file=activities.yaml ``` "
        "fenced example — did the example block get refactored away?"
    )
    activities = json.loads(match.group(1))
    assert isinstance(activities, list) and activities, (
        "Example activities list is empty"
    )

    report = linear_pipeline._component_prop_gate(activities)
    assert report["passed"], (
        f"Example activities in linear-write.md fail the component-prop gate "
        f"that runs against real writer output. Errors: {report['errors']}"
    )

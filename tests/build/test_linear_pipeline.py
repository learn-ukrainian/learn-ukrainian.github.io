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
        "word_target": 89,
        "content_outline": [
            {
                "section": "Діалоги",
                "words": 89,
                "points": ["Introduce a morning dialogue."],
            }
        ],
        "references": [{"title": "Караман Grade 10, p.176", "verbatim_required": False}],
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


def test_jsx_text_values_extracts_uk_attribute() -> None:
    result = linear_pipeline._jsx_text_values(
        '<DialogueBox uk="привіт" en="hi" />'
    )

    assert result == ["привіт"]


def test_jsx_text_values_extracts_legacy_text_attribute() -> None:
    result = linear_pipeline._jsx_text_values('<DialogueBox text="привіт" />')

    assert result == ["привіт"]


def test_jsx_text_values_extracts_both_when_present() -> None:
    result = linear_pipeline._jsx_text_values(
        '<DialogueBox text="доброго ранку" /><DialogueBox uk="як справи?" en="how are you?" />'
    )

    assert result == ["доброго ранку", "як справи?"]


def test_component_language_text_dialoguebox_uk_prop() -> None:
    result = linear_pipeline._component_language_text(
        "DialogueBox",
        '<DialogueBox uk="привіт" en="hi" />',
    )

    assert result == "привіт"


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
    assert "STRUCTURAL TARGETS (Phase A placeholders; Phase B calibrates):" in rendered


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
    tool_config = calls[0][2]["tool_config"]
    assert tool_config["output_format"] == "stream-json"
    if writer == "claude-tools":
        assert tool_config["mcp_config_path"].endswith(".mcp.json")
        assert tool_config["allowed_tools"] == "mcp__sources__*"


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
    "role": "textbook",
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


def test_parse_writer_output_accepts_4backtick_outer_with_inner_3backtick_content() -> None:
    """Pin CommonMark fence-counting for the module.md OUTER fence.

    The writer prompt now instructs writers to use a 4-backtick OUTER fence
    for module.md so they can include 3-backtick code blocks (verb-conjugation
    tables, code-style examples, etc.) inside the prose without breaking
    artifact parsing. Before this change the parser treated every triple-
    backtick line as a structural fence-toggle, which produced "unnamed
    fenced block" HARD-FAILs whenever a writer emitted any nested ```
    inside module.md (observed 2026-05-19 a2/aspect-concept build).

    Per CommonMark: an opening N-backtick fence is closed by a bare fence of
    at least N backticks. So a 4-backtick OUTER fence lets all 3-backtick
    inner content fences pass through as content.

    Triangulated via parallel ``ask-codex`` + delegate-dispatch ``deepseek``
    consults 2026-05-20: both independently picked this protocol.
    """
    output = """````markdown file=module.md
# Мій ранок

Verb conjugations in a code block:

```
Я читаю
Ти читаєш
Він читає
```

End of section.
````

```json file=activities.yaml
[{"id": "act-1", "type": "fill-in", "title": "Додайте -ся"}]
```

```json file=vocabulary.yaml
[{"lemma": "ранок", "translation": "morning", "pos": "noun", "usage": "Мій ранок простий."}]
```

```json file=resources.yaml
[{"title": "Караман Grade 10, p.176", "role": "textbook", "notes": "Зворотні дієслова."}]
```
"""

    artifacts = linear_pipeline.parse_writer_output_strict_json(output)

    assert tuple(artifacts) == linear_pipeline.WRITER_ARTIFACTS
    # Inner 3-backtick fences MUST be preserved as content, not stripped or
    # interpreted as the artifact close.
    module_md = artifacts["module.md"]
    assert "```" in module_md, (
        "Inner 3-backtick code fence was stripped — parser swallowed it "
        "instead of treating it as content"
    )
    assert "Я читаю" in module_md
    assert "End of section." in module_md
    assert yaml.safe_load(artifacts["activities.yaml"])[0]["id"] == "act-1"


def test_parse_writer_output_3backtick_outer_still_works_no_inner_fences() -> None:
    """3-backtick OUTER fences still parse correctly (backward compat).

    Writers who don't need inner code fences can keep using 3-backtick outer
    fences. The new run-length-aware close logic preserves this — an open=3
    fence closes on a close=3 (no info) line. Critical for incremental
    migration of the writer-prompt templates.
    """
    output = """```markdown file=module.md
# Мій ранок

Plain prose without any code fences.
```

```json file=activities.yaml
[{"id": "act-1", "type": "fill-in", "title": "Додайте -ся"}]
```

```json file=vocabulary.yaml
[{"lemma": "ранок", "translation": "morning", "pos": "noun", "usage": "test."}]
```

```json file=resources.yaml
[{"title": "Караман Grade 10, p.176", "role": "textbook", "notes": "test."}]
```
"""

    artifacts = linear_pipeline.parse_writer_output_strict_json(output)
    assert tuple(artifacts) == linear_pipeline.WRITER_ARTIFACTS
    assert "Plain prose" in artifacts["module.md"]


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


def test_parse_writer_output_rejects_quiz_component_prop_questions() -> None:
    """Writer artifacts must use authoring shape: quiz uses `items`.

    The M20 POC failure came from a prompt contradiction: the writer saw React
    component props and emitted `questions`, but the authoring parser consumes
    `items`.
    """
    output = """```markdown file=module.md
# Мій ранок
```

```json file=activities.yaml
[
  {
    "id": "act-1",
    "type": "quiz",
    "instruction": "Оберіть правильну відповідь.",
    "questions": [
      {"question": "Я ____ о сьомій.", "options": ["прокидаюся", "йдеш"]}
    ]
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
        match=r"activities\.yaml schema validation failed.*unexpected fields.*questions",
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


def test_parse_writer_output_accepts_plan_reasoning_with_artifact_mentions() -> None:
    """Regression for #1956: CoT artifact mentions are not label headers."""
    output = '''<plan_reasoning section="Діалоги">
<implementation_map>
- act-5 (match-up verb-pairs) | activities.yaml | INJECT_ACTIVITY end of §Діалоги | inline match-up
- step-2 | module.md | §Діалоги paragraphs 2-3 | prose with я/ти reflexive forms
</implementation_map>
</plan_reasoning>

```markdown file=module.md
# Module body
Some prose.
```

```json file=activities.yaml
[
  {
    "id": "act-1",
    "title": "Match-up",
    "type": "match-up",
    "instruction": "Match these.",
    "pairs": [
      {"left": "вмивати", "right": "вмиватися"},
      {"left": "одягати", "right": "одягатися"}
    ]
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
  {"title": "Караман Grade 10, p.176", "role": "textbook"}
]
```
'''
    artifacts = linear_pipeline.parse_writer_output_strict_json(output)
    assert set(artifacts) == {
        "module.md",
        "activities.yaml",
        "vocabulary.yaml",
        "resources.yaml",
    }
    assert "Module body" in artifacts["module.md"]
    assert yaml.safe_load(artifacts["activities.yaml"])[0]["id"] == "act-1"


def test_parse_writer_output_handles_real_m20_plan_reasoning_prefix() -> None:
    """Replay the 2026-05-13 m20 prefix that triggered #1956."""
    repo_root = Path(__file__).resolve().parents[2]
    raw_path = (
        repo_root
        / ".worktrees/builds/a1-my-morning-20260513-122043/"
        "curriculum/l2-uk-en/a1/my-morning/writer_output.raw.md"
    )
    if not raw_path.exists():
        worktrees_root = next(
            (parent for parent in repo_root.parents if parent.name == ".worktrees"),
            None,
        )
        if worktrees_root is not None:
            raw_path = (
                worktrees_root
                / "builds/a1-my-morning-20260513-122043/"
                "curriculum/l2-uk-en/a1/my-morning/writer_output.raw.md"
            )
    if not raw_path.exists():
        pytest.skip(
            "Failed m20 build worktree not present; this optional replay "
            "fixture preserves the real-world repro for #1956"
        )

    raw = raw_path.read_text(encoding="utf-8")
    module_start = raw.find("```markdown file=module.md")
    module_end = raw.find("\n```\n", module_start)
    if module_start == -1 or module_end == -1:
        pytest.skip("Real m20 artifact shape changed; refresh fixture")
    prefix = raw[: module_end + len("\n```\n")]
    completion = (
        '\n```json file=activities.yaml\n'
        '[{"id":"a","title":"x","type":"match-up",'
        '"instruction":"x","pairs":[{"left":"x","right":"y"}]}]\n'
        '```\n\n'
        '```json file=vocabulary.yaml\n'
        '[{"lemma":"ранок","translation":"morning","pos":"noun","usage":"x"}]\n'
        '```\n\n'
        '```json file=resources.yaml\n'
        '[{"title":"x","role":"textbook"}]\n'
        '```\n'
    )

    artifacts = linear_pipeline.parse_writer_output_strict_json(prefix + completion)
    assert set(artifacts) == {
        "module.md",
        "activities.yaml",
        "vocabulary.yaml",
        "resources.yaml",
    }


def test_activity_type_field_whitelist_uses_authoring_shape() -> None:
    """The per-type whitelist holds **authoring YAML** field names (what
    the writer emits, what `ActivityParser._parse_*` reads), NOT React
    component prop names from `docs/lesson-schema.yaml`.

    The two diverge for adapter-style activities — quiz authoring `items`
    becomes component prop `questions`; authorial-intent authoring
    `text_excerpt` becomes dataclass `excerpt`; many seminar types use
    snake_case YAML and camelCase props (`model_answer` vs `modelAnswer`).
    The pre-#1627 loader sourced from `lesson-schema.yaml` — that file
    describes the COMPONENT side, so the validator was rejecting valid
    authoring YAML and accepting component-prop typos.
    """
    whitelist = linear_pipeline._activity_type_field_whitelist()

    # `groups` is required for group-sort and must be in its whitelist;
    # this is the literal regression #1624 fixes (Phase 4 round-3.5 #1620).
    assert "groups" in whitelist["group-sort"]
    # ...but must NOT leak into fill-in's whitelist (the wrong fix would
    # have been to add `groups` globally; see Codex-reviewer finding 4 on
    # PR #1621).
    assert "groups" not in whitelist["fill-in"]
    assert "items" in whitelist["fill-in"]
    assert "items" in whitelist["error-correction"]
    assert "items" in whitelist["order"]
    assert "correct_order" in whitelist["order"]

    # Adapter-rename activities: the AUTHORING-side field name belongs in
    # the whitelist, NOT the React component prop name. See
    # `_quiz_to_mdx` / `_authorial_intent_to_mdx` in
    # scripts/yaml_activities.py for the rename adapters.
    assert "items" in whitelist["quiz"]  # authoring shape
    assert "questions" not in whitelist["quiz"]  # component-prop shape
    assert "items" in whitelist["select"]
    assert "questions" not in whitelist["select"]
    assert "items" in whitelist["translate"]
    assert "questions" not in whitelist["translate"]
    assert "text_excerpt" in whitelist["authorial-intent"]
    assert "excerpt" not in whitelist["authorial-intent"]
    assert "model_answer" in whitelist["essay-response"]  # snake_case
    assert "modelAnswer" not in whitelist["essay-response"]  # camelCase prop
    assert "debate_question" in whitelist["debate"]
    assert "debateQuestion" not in whitelist["debate"]
    assert "image_url" in whitelist["paleography-analysis"]
    assert "imageUrl" not in whitelist["paleography-analysis"]

    # `title` and `instruction` are valid authoring fields on every type;
    # `id` is the universal activity identifier read by the parser.
    for activity_type in ("group-sort", "fill-in", "quiz", "error-correction"):
        assert "title" in whitelist[activity_type]
        assert "instruction" in whitelist[activity_type]
        assert "id" in whitelist[activity_type]


def test_activity_type_field_whitelist_rejects_react_only_props() -> None:
    """React component-only props (`children`, `isUkrainian`) appear in
    `docs/lesson-schema.yaml` because they're rendered by `<Quiz>` etc.,
    but the writer must NEVER emit them in authoring YAML — the MDX
    assembler synthesizes them. The pre-#1627 loader accepted them.
    """
    whitelist = linear_pipeline._activity_type_field_whitelist()
    for activity_type in whitelist:
        assert "children" not in whitelist[activity_type], (
            f"{activity_type}: `children` is a JSX-only prop, never authored"
        )
        assert "isUkrainian" not in whitelist[activity_type], (
            f"{activity_type}: `isUkrainian` is synthesized by the MDX "
            "assembler, never authored"
        )


def test_activity_type_field_whitelist_covers_parser_dispatch() -> None:
    """Drift guard: every activity type the parser dispatches on
    (`scripts/yaml_activities.py:ActivityParser._parse_activity`) must
    appear in `_ACTIVITY_AUTHORING_FIELDS`, AND every key in the map
    must be a type the parser handles OR a type declared in
    `docs/lesson-schema.yaml` (so the writer is told it's emittable).

    Catches: a new activity type added to the parser without updating
    the validator (writers would emit it and get rejected with the
    `unknown activity type` message), and the reverse — a stale map
    entry that the parser no longer dispatches.
    """
    import inspect

    from scripts.yaml_activities import ActivityParser

    whitelist = linear_pipeline._activity_type_field_whitelist()

    # Extract parser dispatch type strings from the literal `parsers = {...}`
    # dict in `_parse_activity`. Keys look like `'foo-bar': self._parse_foo`
    # (string, then arrow, then bound-method ref).
    parser_src = inspect.getsource(ActivityParser._parse_activity)
    parser_types = set(re.findall(r"^\s*'([a-z][a-z0-9-]*)':\s*self\.", parser_src, re.MULTILINE))
    assert parser_types, "Failed to extract parser dispatch types — has _parse_activity been refactored?"

    # Every parser-dispatched type has a whitelist entry.
    missing_in_map = parser_types - set(whitelist)
    assert not missing_in_map, (
        f"Activity types parsed but not whitelisted (writers would be "
        f"rejected with 'unknown activity type'): {sorted(missing_in_map)}"
    )

    # Every whitelist entry is either a parser-known type OR declared in
    # `docs/lesson-schema.yaml` (parser silently drops it but writer is
    # told it's emittable — preserves pre-#1624 behavior of the
    # lesson-schema-sourced loader, while remaining strict about the
    # AUTHORING field names per type).
    schema = yaml.safe_load(
        (linear_pipeline.PROJECT_ROOT / "docs" / "lesson-schema.yaml").read_text()
    )
    schema_types = {
        data.get("activity_type")
        for data in (schema.get("components") or {}).values()
        if isinstance(data, dict) and data.get("activity_type")
    }
    stale_in_map = set(whitelist) - parser_types - schema_types
    assert not stale_in_map, (
        f"Whitelist entries with no parser dispatch AND no lesson-schema "
        f"declaration (likely stale): {sorted(stale_in_map)}"
    )


def test_validate_writer_json_artifact_accepts_groups_for_group_sort() -> None:
    """`group-sort` activities legitimately carry a top-level `groups` field
    per `docs/lesson-schema.yaml` (`required: [{name: groups, ...}]`). The
    pre-#1624 global whitelist rejected this as a hallucinated field.
    """
    linear_pipeline._validate_writer_json_artifact(
        "activities.yaml",
        [
            {
                "id": "act-1",
                "type": "group-sort",
                "instruction": "Розсортуйте слова за групами.",
                "groups": [
                    {"name": "Фрукти", "items": ["яблуко", "груша"]},
                    {"name": "Овочі", "items": ["морква", "буряк"]},
                ],
            }
        ],
    )


def test_validate_writer_json_artifact_rejects_groups_on_fill_in() -> None:
    """`groups` is per-type valid for `group-sort` but NOT for `fill-in`.
    A simple global whitelist of `groups` would have allowed it on every
    activity type — that was the wrong fix (Codex-reviewer finding 4 on
    PR #1621).
    """
    with pytest.raises(
        linear_pipeline.LinearPipelineError,
        match=r"activities\.yaml schema validation failed: item 1 has "
        r"unexpected fields \['groups'\]; allowed: ",
    ):
        linear_pipeline._validate_writer_json_artifact(
            "activities.yaml",
            [
                {
                    "id": "act-1",
                    "type": "fill-in",
                    "items": [{"sentence": "x", "answer": "y", "options": ["y"]}],
                    "groups": [{"name": "Hi", "items": ["x"]}],
                }
            ],
        )


def test_validate_writer_json_artifact_accepts_items_for_fill_in() -> None:
    """`fill-in` activities use `items` as their top-level required prop
    per `docs/lesson-schema.yaml`. Standard shape, must always pass.
    """
    linear_pipeline._validate_writer_json_artifact(
        "activities.yaml",
        [
            {
                "id": "act-1",
                "type": "fill-in",
                "instruction": "Закінчіть речення.",
                "items": [
                    {
                        "sentence": "Я ____ о сьомій.",
                        "answer": "прокидаюся",
                        "options": ["прокидаюся", "сплю"],
                    }
                ],
            }
        ],
    )


def test_validate_writer_json_artifact_accepts_error_correction_items() -> None:
    """Boundary case for #1623 `_component_prop_gate` work: an
    `error-correction` activity with the standard items array passes
    top-level extra-field validation.

    The nested `errorWord`/`correctForm` per item are not visible to this
    layer (which only checks top-level activity keys); they are governed
    by `_component_prop_gate` and the lesson-schema's `nested_types`.
    """
    linear_pipeline._validate_writer_json_artifact(
        "activities.yaml",
        [
            {
                "id": "act-9",
                "type": "error-correction",
                "instruction": "Виправте помилку.",
                "items": [
                    {
                        "sentence": "Він вмиваєця.",
                        "errorWord": "вмиваєця",
                        "correctForm": "вмивається",
                        "explanation": "Закінчення -ться.",
                    }
                ],
            }
        ],
    )


def test_validate_writer_json_artifact_accepts_quiz_items_authoring_shape() -> None:
    """`quiz` authoring YAML uses `items: [...]` (per
    `claude_extensions/quick-ref/ACTIVITY-SCHEMAS.md`). The MDX adapter
    `_quiz_to_mdx` renames this to the React component's `questions=`
    prop. The strict-JSON validator must accept the AUTHORING shape.
    """
    linear_pipeline._validate_writer_json_artifact(
        "activities.yaml",
        [
            {
                "id": "act-1",
                "type": "quiz",
                "title": "Питання",
                "items": [
                    {
                        "question": "Як справи?",
                        "options": [
                            {"text": "Добре", "correct": True},
                            {"text": "Погано", "correct": False},
                        ],
                    }
                ],
            }
        ],
    )


def test_validate_writer_json_artifact_rejects_quiz_questions_component_prop() -> None:
    """A writer that emits `quiz: {questions: [...]}` is using the
    React component PROP NAME, not the authoring field name. Pre-#1627
    the validator (sourced from `lesson-schema.yaml`) silently accepted
    this AND silently rejected the canonical `items` — producing empty
    quizzes at render time because `_quiz_to_mdx` reads `activity.items`,
    not `activity.questions`.
    """
    with pytest.raises(
        linear_pipeline.LinearPipelineError,
        match=r"activities\.yaml schema validation failed: item 1 has "
        r"unexpected fields \['questions'\]; allowed: ",
    ):
        linear_pipeline._validate_writer_json_artifact(
            "activities.yaml",
            [
                {
                    "id": "act-1",
                    "type": "quiz",
                    "questions": [{"question": "x", "options": []}],
                }
            ],
        )


def test_validate_writer_json_artifact_rejects_authorial_intent_excerpt_dataclass_name() -> None:
    """`authorial-intent` authoring YAML uses `text_excerpt:` and
    `prompt:` per `ACTIVITY-SCHEMAS.md` and the activities-base JSON
    Schema. `_parse_authorial_intent` renames these to the dataclass's
    `excerpt`/`questions` fields post-parse — so the post-parse name
    `excerpt` is NOT a valid authoring field. Catches Codex-flagged
    drift between the parser-output dataclass and the YAML wire format.
    """
    with pytest.raises(
        linear_pipeline.LinearPipelineError,
        match=r"unexpected fields \['excerpt'\]",
    ):
        linear_pipeline._validate_writer_json_artifact(
            "activities.yaml",
            [
                {
                    "id": "act-7",
                    "type": "authorial-intent",
                    "title": "Авторський задум",
                    "excerpt": "...",  # WRONG — dataclass field name
                    "prompt": "Чому автор обрав таку структуру?",
                    "model_answer": "...",
                }
            ],
        )


def test_validate_writer_json_artifact_accepts_authorial_intent_text_excerpt_authoring() -> None:
    """Counterpart to the rejects-excerpt test: the canonical authoring
    field `text_excerpt` is what the writer is told to emit, and what
    `_parse_authorial_intent` reads via `data.get('text_excerpt', '')`.
    """
    linear_pipeline._validate_writer_json_artifact(
        "activities.yaml",
        [
            {
                "id": "act-7",
                "type": "authorial-intent",
                "title": "Авторський задум",
                "text_excerpt": "...",
                "prompt": "Чому автор обрав таку структуру?",
                "model_answer": "...",
            }
        ],
    )


def test_validate_writer_json_artifact_rejects_camelcase_component_prop_names() -> None:
    """Many seminar/HIST activities use snake_case authoring fields that
    `_*_to_mdx` adapters rename to camelCase component props. The
    pre-#1627 lesson-schema-sourced loader accepted the camelCase names
    (e.g. `modelAnswer`, `debateQuestion`, `imageUrl`), masking writer
    errors. This batches a few canonical examples.
    """
    cases = [
        ("essay-response", "modelAnswer"),
        ("debate", "debateQuestion"),
        ("paleography-analysis", "imageUrl"),
    ]
    for activity_type, bad_field in cases:
        with pytest.raises(
            linear_pipeline.LinearPipelineError,
            match=rf"unexpected fields \['{bad_field}'\]",
        ):
            linear_pipeline._validate_writer_json_artifact(
                "activities.yaml",
                [{"id": "act-1", "type": activity_type, bad_field: "x"}],
            )


def test_validate_writer_json_artifact_rejects_nonsense_field() -> None:
    """A field that exists in NO activity type's schema must fail with
    a per-type-aware error message naming the activity type's allowed
    fields, not the union of every type's fields.
    """
    with pytest.raises(
        linear_pipeline.LinearPipelineError,
        match=r"activities\.yaml schema validation failed: item 1 has "
        r"unexpected fields \['kek'\]; allowed: ",
    ) as exc_info:
        linear_pipeline._validate_writer_json_artifact(
            "activities.yaml",
            [{"id": "act-1", "type": "fill-in", "kek": "bogus"}],
        )
    # The message must list fill-in's allowed fields specifically — not
    # the union of every activity type's fields.
    msg = str(exc_info.value)
    assert "items" in msg  # fill-in's required prop name
    assert "groups" not in msg  # group-sort's prop, must not leak in


def test_validate_writer_json_artifact_rejects_unknown_activity_type() -> None:
    """A `type` field that isn't declared in `docs/lesson-schema.yaml`
    fails with a targeted "unknown activity type" message — earlier and
    more useful than a noisy `unexpected fields [<everything>]` report
    against an empty allowed-set.
    """
    with pytest.raises(
        linear_pipeline.LinearPipelineError,
        match=r"activities\.yaml schema validation failed: item 1 has "
        r"unknown activity type 'mystery-type'",
    ):
        linear_pipeline._validate_writer_json_artifact(
            "activities.yaml",
            [{"id": "act-1", "type": "mystery-type"}],
        )


def test_validate_writer_json_artifact_requires_type_for_polymorphic() -> None:
    """A polymorphic schema cannot resolve allowed fields without `type`;
    fail with a clear required-field error before extras-checking.
    """
    with pytest.raises(
        linear_pipeline.LinearPipelineError,
        match=r"requires type as a non-empty string",
    ):
        linear_pipeline._validate_writer_json_artifact(
            "activities.yaml",
            [{"id": "act-1", "type": "   "}],
        )


def test_validate_writer_json_artifact_allows_workbook_activity_without_id() -> None:
    """V7 writer prompt design (linear-write.md L700-701, PR #2214) — WORKBOOK
    activities deliberately omit `id`; only INLINE activities (those targeted
    by `<!-- INJECT_ACTIVITY: act-N -->` markers in prose) need a string id.
    The required-fields schema MUST allow id-less workbook entries through;
    the bidirectional check lives in the `inject_activity_ids` content gate.

    Regression for 2026-05-22 a1/my-morning build failure where the writer
    correctly produced 4 inline + 6 workbook activities, schema rejected it
    with `item 5 requires id as str, got NoneType (None)`.
    """
    activities = [
        # Inline activities — id present per spec.
        {"id": "act-1", "type": "match-up", "title": "Inline 1",
         "pairs": [{"left": "a", "right": "b"}]},
        {"id": "act-2", "type": "quiz", "title": "Inline 2",
         "items": [{"question": "q?", "answer": "a", "options": ["a", "b"]}]},
        # Workbook activities — id omitted per spec.
        {"type": "fill-in", "title": "Workbook 1",
         "items": [{"sentence": "I ___ here.", "answer": "live"}]},
        {"type": "translate", "title": "Workbook 2",
         "items": [{"source": "I wake up.", "target": "Я прокидаюся."}]},
    ]
    # MUST NOT raise — schema accepts the mixed inline+workbook payload.
    linear_pipeline._validate_writer_json_artifact("activities.yaml", activities)


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
                "<DialogueBox",
                "  lines={[",
                '    { speaker: "Ліна", text: "Я прокидаюся рано." },',
                '    { speaker: "Марко", text: "Я снідаю вдома." },',
                "  ]}",
                "/>",
                "",
                "| Українською | English |",
                "|---|---|",
                "| прокидаюся | I wake up |",
                "| вмиваюся | I wash up |",
                "| одягаюся | I get dressed |",
                "| снідаю | I eat breakfast |",
                "| вдома | at home |",
                "",
                "- **Я прокидаюся рано.** — I wake up early.",
                "- **Я вмиваюся швидко.** — I wash up quickly.",
                "- **Я одягаюся вдома.** — I get dressed at home.",
                "- **Я снідаю вдома.** — I eat breakfast at home.",
                "",
                ":::tip",
                "Зворотні дієслова на **-ся** описують дію, спрямовану на",
                "себе: **прокидаюся**, **вмиваюся**, **одягаюся**.",
                ":::",
                "",
                "> [!myth-buster]",
                "> The suffix **-ся** is NOT a passive marker — it is a short",
                "> accusative form of **себе** (\"oneself\"). The verb is doing",
                "> something TO the speaker, not BY the speaker.",
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
        [
            {
                "title": "Караман Grade 10, p.176",
                "role": "textbook",
                "source_ref": "Караман Grade 10, p.176",
            }
        ],
    )
    (module_dir / "writer_tool_calls.json").write_text(
        json.dumps([{"tool": "search_images", "args": {"query": "ранок"}}]) + "\n",
        encoding="utf-8",
    )

    def fake_verify(words: list[str]) -> dict[str, list[dict]]:
        return {word: [{"lemma": word, "pos": "x", "tags": ""}] for word in words}

    return module_dir, plan_path, fake_verify


def _build_fake_verify_words(
    known: dict[str, bool],
) -> Callable[[list[str]], dict[str, list[dict]]]:
    def fake_verify(words: list[str]) -> dict[str, list[dict]]:
        return {
            word: [{"lemma": word, "pos": "x", "tags": ""}]
            if known.get(word, False)
            else []
            for word in words
        }

    return fake_verify


def test_inject_activity_gate_fails_when_activities_unused() -> None:
    activities = [{"id": "act-1"}, {"id": "act-2"}, {"id": "act-3"}]
    report = linear_pipeline._inject_activity_gate("## Діалоги\n\nБез маркерів.", activities)

    assert report["passed"] is False
    assert report["unused"] == ["act-1", "act-2", "act-3"]
    assert "unused_activities" in report["reason"]


def test_inject_activity_gate_passes_when_all_activities_injected() -> None:
    activities = [{"id": "act-1"}, {"id": "act-2"}, {"id": "act-3"}]
    text = "\n".join(
        [
            "## Діалоги",
            "",
            "<!-- INJECT_ACTIVITY: act-1 -->",
            "<!-- INJECT_ACTIVITY: act-2 -->",
            "<!-- INJECT_ACTIVITY: act-3 -->",
        ]
    )

    report = linear_pipeline._inject_activity_gate(text, activities)

    assert report["passed"] is True
    assert report["unused"] == []


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


def test_vesum_gate_skips_error_field_of_error_correction_items_shape(
    tmp_path: Path,
) -> None:
    """`error:` in the `items:` shape stores a deliberate typo and must not fail VESUM.

    Companion to `test_vesum_gate_skips_error_field_of_error_correction_activity`
    (which covers the `sentences:` shape). Post-PR #2031, the canonical fields
    for `error-correction` items are `error:` (the misspelled form) and
    `correction:` (the corrected form). Legacy aliases `errorWord` / `error_word`
    / `correctForm` trip the new `_activity_schema_gate` before this gate runs.
    """
    module_dir, plan_path, _ = _passing_qg_fixture(tmp_path)
    _write_yaml(
        module_dir / "activities.yaml",
        [
            {
                "id": "act-1",
                "type": "error-correction",
                "title": "Знайдіть помилку",
                "items": [
                    {
                        "sentence": "Він ____ щодня.",
                        "error": "вмиваєця",
                        "correction": "вмивається",
                        "explanation": "Потрібна форма -ться.",
                    },
                    {
                        "sentence": "Ти ____ швидко.",
                        "error": "одягаєся",
                        "correction": "одягаєшся",
                        "explanation": "Потрібна форма -шся.",
                    }
                ],
            }
        ],
    )

    received: list[list[str]] = []

    def fake_verify(words: list[str]) -> dict[str, list[dict]]:
        received.append(list(words))
        deliberate_errors = {"вмиваєця", "одягаєся"}
        return {
            word: []
            if word in deliberate_errors
            else [{"lemma": word, "pos": "x", "tags": ""}]
            for word in words
        }

    report = linear_pipeline.run_python_qg(
        module_dir, plan_path, verify_words_fn=fake_verify
    )

    assert report["gates"]["vesum_verified"]["passed"] is True
    forwarded = received[0]
    assert "вмиваєця" not in forwarded
    assert "одягаєся" not in forwarded
    assert "вмивається" in forwarded
    assert "одягаєшся" in forwarded


@pytest.mark.parametrize("answer_key", ["correctAnswer", "answer"])
def test_activity_vesum_text_filters_quiz_distractors_by_answer_spelling(
    answer_key: str,
) -> None:
    activity = {
        "id": "act-1",
        "type": "quiz",
        "title": "Оберіть правильну форму",
        "items": [
            {
                "question": "Яка форма правильна для «я»?",
                "options": ["користуювася", "користуюся"],
                answer_key: "користуюся",
            }
        ],
    }

    vesum_text = linear_pipeline._activity_vesum_text(activity)

    assert "користуювася" not in vesum_text
    assert "користуюся" in vesum_text


def test_activity_vesum_text_skips_false_true_false_statements() -> None:
    activity = {
        "id": "act-7",
        "type": "true-false",
        "title": "Перевірте твердження",
        "items": [
            {
                "statement": "The verb «дивитися» has «я дивюся» in the 1st person singular.",
                "answer": False,
            },
            {
                "statement": "Форма «я дивлюся» правильна.",
                "answer": True,
            },
        ],
    }

    vesum_text = linear_pipeline._activity_vesum_text(activity)

    assert "дивюся" not in vesum_text
    assert "дивлюся" in vesum_text
    assert "правильна" in vesum_text


def test_vesum_gate_skips_fill_in_answer_suffix_without_options_field(
    tmp_path: Path,
) -> None:
    """Fill-in `answer:` fragments must be skipped even when `options:` absent.

    Regression for #1967: build #4 of m20 (`a1/my-morning`) emitted fill-in
    activities with item shape `{sentence, answer}` (no `options:` list — the
    student types the suffix). #1963's logic at `_activity_vesum_text` skipped
    the `answer` field only when its value appeared in a sibling `options:`
    list; with no `options:` present, the suffix fragments (-юся, -ються,
    -єшся, etc.) fell through to VESUM and were reported missing, halting the
    build. The fix makes the skip unconditional for fill-in activities since
    the pedagogical rationale (answer IS a morphological fragment) doesn't
    depend on whether an options list is present.
    """
    module_dir, plan_path, _ = _passing_qg_fixture(tmp_path)
    _write_yaml(
        module_dir / "activities.yaml",
        [
            {
                "id": "act-1",
                "type": "fill-in",
                "title": "Додайте -ся",
                "items": [
                    {"sentence": "Я вмива____ о сьомій.", "answer": "юся"},
                    {"sentence": "Ти одяга____ швидко.", "answer": "єшся"},
                    {"sentence": "Він прокида____ пізно.", "answer": "ється"},
                    {"sentence": "Ми збира____ на роботу.", "answer": "ємося"},
                    {"sentence": "Ви поверта____ додому?", "answer": "єтеся"},
                    {"sentence": "Вони навча____ вранці.", "answer": "ються"},
                ],
            }
        ],
    )

    received: list[list[str]] = []

    def fake_verify(words: list[str]) -> dict[str, list[dict]]:
        received.append(list(words))
        # Sentence fragments (whole UK words) verify fine; suffixes do not.
        # But the fix should mean the suffixes never reach this function.
        return {
            word: [{"lemma": word, "pos": "x", "tags": ""}] for word in words
        }

    report = linear_pipeline.run_python_qg(
        module_dir, plan_path, verify_words_fn=fake_verify
    )

    forwarded = received[0]
    # None of the bare reflexive suffix fragments should be in the VESUM scope.
    suffix_fragments = {"юся", "єшся", "ється", "ємося", "єтеся", "ються"}
    leaked = suffix_fragments & set(forwarded)
    assert not leaked, (
        f"fill-in `answer` suffix fragments leaked into VESUM scope: {leaked}"
    )
    # And the sentence-shell tokens around the blank still get verified
    # (sanity: we didn't accidentally skip too much).
    assert "вмива" in forwarded or "сьомій" in forwarded
    assert report["gates"]["vesum_verified"]["passed"] is True


def test_vesum_gate_still_checks_correction_in_error_correction_activity(
    tmp_path: Path,
) -> None:
    """`correction:` is the learner's answer and must stay VESUM-verified.

    Post-PR #2031, the canonical fields are `error:` + `correction:` —
    legacy `errorWord` / `correctForm` trip the activity_schema gate.
    """
    module_dir, plan_path, _ = _passing_qg_fixture(tmp_path)
    _write_yaml(
        module_dir / "activities.yaml",
        [
            {
                "id": "act-1",
                "type": "error-correction",
                "title": "Знайдіть помилку",
                "items": [
                    {
                        "sentence": "Він ____ щодня.",
                        "error": "вмиваєця",
                        "correction": "вмиваєцявигадка",
                        "explanation": "Потрібна форма -ться.",
                    }
                ],
            }
        ],
    )

    def fake_verify(words: list[str]) -> dict[str, list[dict]]:
        return {
            word: []
            if word == "вмиваєцявигадка"
            else [{"lemma": word, "pos": "x", "tags": ""}]
            for word in words
        }

    report = linear_pipeline.run_python_qg(
        module_dir, plan_path, verify_words_fn=fake_verify
    )

    gate = report["gates"]["vesum_verified"]
    assert gate["passed"] is False
    assert gate["missing"] == ["вмиваєцявигадка"]


def test_vesum_gate_checks_error_word_outside_error_correction_activity(
    tmp_path: Path,
) -> None:
    """The deliberate-error skip is scoped to error-correction activities."""
    module_dir, plan_path, _ = _passing_qg_fixture(tmp_path)
    _write_yaml(
        module_dir / "activities.yaml",
        [
            {
                "id": "act-1",
                "type": "fill-in",
                "title": "Додайте -ся",
                "items": [
                    {
                        "sentence": "Він вмивається щодня.",
                        "answer": "ся",
                        "errorWord": "вмиваєця",
                    }
                ],
            }
        ],
    )

    def fake_verify(words: list[str]) -> dict[str, list[dict]]:
        return {
            word: [] if word == "вмиваєця" else [{"lemma": word, "pos": "x", "tags": ""}]
            for word in words
        }

    report = linear_pipeline.run_python_qg(
        module_dir, plan_path, verify_words_fn=fake_verify
    )

    gate = report["gates"]["vesum_verified"]
    assert gate["passed"] is False
    assert gate["missing"] == ["вмиваєця"]


def test_reviewer_unmatched_anchor_not_in_vesum_missing_list(
    tmp_path: Path,
) -> None:
    """Failed reviewer fix anchors are not learner-facing VESUM evidence."""
    with linear_pipeline.telemetry_event_sink(tmp_path / "events.jsonl"):
        apply_result = linear_pipeline._apply_reviewer_fixes(
            "## Діалоги\n\nЦе вже двоколонна вправа.",
            [{"find": "двоколонкова", "replace": "двоколонна"}],
            gate="vesum_verified",
        )

    def fake_verify(words: list[str]) -> dict[str, list[dict]]:
        return {
            word: []
            if word == "двоколонкова"
            else [{"lemma": word, "pos": "x", "tags": ""}]
            for word in words
        }

    baseline = linear_pipeline._vesum_gate(
        module_text="## Діалоги\n\nдвоколонкова",
        activities=[],
        vocabulary=[],
        resources=[],
        verify_words_fn=fake_verify,
    )
    report = linear_pipeline._vesum_gate(
        module_text="## Діалоги\n\nдвоколонкова",
        activities=[],
        vocabulary=[],
        resources=[],
        verify_words_fn=fake_verify,
        ignored_missing_surfaces=apply_result.unmatched_anchors,
    )

    assert apply_result.unmatched_anchors == frozenset({"двоколонкова"})
    assert baseline["missing"] == ["двоколонкова"]
    assert "двоколонкова" not in report["missing"]
    assert report["passed"] is True


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


def test_vesum_gate_skips_fillin_options_bare_list() -> None:
    """Regression for #1962 gate 1 leak 1. fill-in options are fragments."""
    activities = [
        {
            "id": "act-2",
            "type": "fill-in",
            "items": [
                {
                    "sentence": "Я вмива___ о сьомій.",
                    "answer": "юся",
                    "options": ["юся", "єшся", "ється"],
                }
            ],
        }
    ]
    fake_verify = _build_fake_verify_words(known={"вмива": True, "сьомій": True})
    report = linear_pipeline._vesum_gate(
        module_text="",
        activities=activities,
        vocabulary=[],
        resources=[],
        verify_words_fn=fake_verify,
    )
    assert "юся" not in report["missing"]
    assert "єшся" not in report["missing"]
    assert "ється" not in report["missing"]
    assert report["passed"] is True


def test_vesum_gate_skips_quiz_options_distractors() -> None:
    """Regression for #1962 gate 1 leak 2. quiz non-answer options are distractors."""
    activities = [
        {
            "id": "act-1",
            "type": "quiz",
            "items": [
                {
                    "question": "Я ___ каву.",
                    "options": ["п'юся", "п'ю"],
                    "answer": "п'ю",
                }
            ],
        }
    ]
    fake_verify = _build_fake_verify_words(known={"каву": True, "п'ю": True})
    report = linear_pipeline._vesum_gate(
        module_text="",
        activities=activities,
        vocabulary=[],
        resources=[],
        verify_words_fn=fake_verify,
    )
    assert "п'юся" not in report["missing"]
    assert report["passed"] is True


def test_vesum_gate_skips_error_correction_explanation() -> None:
    """Regression for #1962 gate 1 leak 3. explanations cite wrong forms."""
    activities = [
        {
            "id": "act-8",
            "type": "error-correction",
            "items": [
                {
                    "sentence": "На сніданок я завжди їм завтрак.",
                    "error": "завтрак",
                    "correction": "сніданок",
                    "explanation": (
                        "«Завтрак» is a Russianism. Standard Ukrainian: сніданок."
                    ),
                }
            ],
        }
    ]
    fake_verify = _build_fake_verify_words(known={"сніданок": True})
    report = linear_pipeline._vesum_gate(
        module_text="",
        activities=activities,
        vocabulary=[],
        resources=[],
        verify_words_fn=fake_verify,
    )
    assert "Завтрак" not in report["missing"]
    assert "завтрак" not in report["missing"]
    assert report["passed"] is True


def test_vesum_gate_strips_vocabulary_usage_parentheticals() -> None:
    """Regression for #1962 gate 1 leak 4. usage parentheticals can be meta."""
    vocabulary = [
        {
            "lemma": "дивлюся",
            "pos": "verb",
            "usage": "Я дивлюся у дзеркало (стем + -л- у 1-й особі однини).",
        }
    ]
    fake_verify = _build_fake_verify_words(
        known={"дивлюся": True, "дзеркало": True}
    )
    report = linear_pipeline._vesum_gate(
        module_text="",
        activities=[],
        vocabulary=vocabulary,
        resources=[],
        verify_words_fn=fake_verify,
    )
    assert "стем" not in report["missing"]
    assert report["passed"] is True


def test_vesum_gate_passes_m20_build_3_artifacts() -> None:
    """Replay m20 build #3 leak forms without requiring the build worktree."""
    build_dir = (
        Path(__file__).resolve().parents[2]
        / ".worktrees/builds/a1-my-morning-20260513-164953"
        / "curriculum/l2-uk-en/a1/my-morning"
    )
    if build_dir.exists():
        module_text = (build_dir / "module.md").read_text(encoding="utf-8")
        activities = yaml.safe_load(
            (build_dir / "activities.yaml").read_text(encoding="utf-8")
        )
        vocabulary = yaml.safe_load(
            (build_dir / "vocabulary.yaml").read_text(encoding="utf-8")
        )
        resources = yaml.safe_load(
            (build_dir / "resources.yaml").read_text(encoding="utf-8")
        )
    else:
        module_text = ""
        activities = [
            {
                "id": "act-1",
                "type": "quiz",
                "items": [
                    {
                        "question": "Я ___ каву о восьмій.",
                        "options": ["п'юся", "п'ю"],
                        "answer": "п'ю",
                    }
                ],
            },
            {
                "id": "act-2",
                "type": "fill-in",
                "items": [
                    {
                        "sentence": "Я вмива___ о сьомій.",
                        "answer": "юся",
                        "options": ["юся", "єшся", "ється"],
                    },
                    {
                        "sentence": "Ми збира___ швидко.",
                        "answer": "ємося",
                        "options": ["теся", "ємося", "єтеся", "ються"],
                    },
                ],
            },
            {
                "id": "act-8",
                "type": "error-correction",
                "items": [
                    {
                        "sentence": "На сніданок я завжди їм завтрак.",
                        "error": "завтрак",
                        "correction": "сніданок",
                        "explanation": (
                            "«Завтрак» is a Russianism; do not use користу- here."
                        ),
                    }
                ],
            },
        ]
        vocabulary = [
            {
                "lemma": "дивлюся",
                "pos": "verb",
                "usage": "Я дивлюся у дзеркало (стем + -л- у 1-й особі однини).",
            }
        ]
        resources = []

    leaked_forms = {
        "Завтрак",
        "користу",
        "п'юся",
        "стем",
        "теся",
        "юся",
        "ються",
        "ємося",
        "єтеся",
        "ється",
        "єшся",
    }
    known = {
        "восьмій": True,
        "вмива": True,
        "дзеркало": True,
        "дивлюся": True,
        "збира": True,
        "каву": True,
        "о": True,
        "п'ю": True,
        "сніданок": True,
        "сьомій": True,
        "швидко": True,
    }
    report = linear_pipeline._vesum_gate(
        module_text=module_text,
        activities=activities,
        vocabulary=vocabulary,
        resources=resources,
        verify_words_fn=_build_fake_verify_words(known=known),
    )

    assert leaked_forms.isdisjoint(report["missing"])
    if not build_dir.exists():
        assert report["passed"] is True


def test_vesum_gate_skips_resource_notes_field() -> None:
    """Regression for #2098: resources notes field excluded, title kept."""
    resources = [
        {
            "title": "Текст Фабрикація",
            "notes": "за Ларисою Ніцою",
            "lemma": "слово",
            "usage": "вживання",
        }
    ]
    fake_verify = _build_fake_verify_words(
        known={"текст": True, "слово": True, "вживання": True, "за": True, "ларисою": True}
    )
    report = linear_pipeline._vesum_gate(
        module_text="",
        activities=[],
        vocabulary=[],
        resources=resources,
        verify_words_fn=fake_verify,
    )
    # Notes field skipped, so "Ніцою" should not be missing
    assert "ніцою" not in report["missing"]
    assert "Ніцою" not in report["missing"]
    # Title field included, so "Фабрикація" should be missing
    assert "фабрикація" in report["missing"] or "Фабрикація" in report["missing"]


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
    assert report["gates"]["long_uk_ceiling"]["offending_runs"] == [], (
        f"Ukrainian ellipsis was not treated as sentence boundary: "
        f"{report['gates']['long_uk_ceiling']['offending_runs']}"
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

    pct = report["gates"]["immersion_advisory"]["pct"]
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

    assert report["gates"]["long_uk_ceiling"]["offending_runs"] == [], (
        "JSX with `>` in a prop expression broke the regex strip and the "
        "DialogueBox lines were re-read as one giant sentence: "
        f"{report['gates']['long_uk_ceiling']['offending_runs']}"
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
    assert report["gates"]["long_uk_ceiling"]["offending_runs"] == [], (
        f"start-of-string bullets joined into a long sentence: "
        f"{report['gates']['long_uk_ceiling']['offending_runs']}"
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

    long_uk_ceiling = report["gates"]["long_uk_ceiling"]
    # The dialogue text inside JSX still counts toward the percent (Ukrainian
    # tokens were tokenized from the raw body), but the JSX block is no longer
    # treated as one giant sentence.
    assert long_uk_ceiling["offending_runs"] == [], (
        f"JSX block was incorrectly read as a long sentence: "
        f"{long_uk_ceiling['offending_runs']}"
    )


def test_long_uk_ceiling_exempts_citation_grounded_source_blockquote() -> None:
    """#1962: source blockquotes cited by textbook_grounding are exempt."""
    text = (
        "## Дієслова на -ся\n\n"
        "> **Караман, 10 клас, с. 176:** *Дієслова із суфіксом -ся(-сь), "
        "які виражають зворотну дію, називаються зворотними: навчатися, "
        "закохатися. Сучасний дієслівний суфікс -ся(-сь) — це давня "
        "коротка форма зворотного займенника себе в Зн. в. однини: "
        "Я не боюся. — Я ся не бою (діал.). Уживається -ся(-сь) після "
        "інфінітивного суфікса.*\n\n"
        "## Мій ранок\n\n"
        "> Спочатку прокидаюся, потім вмиваюся і одягаюся, після цього "
        "снідаю і п'ю каву, нарешті йду на роботу — це мій типовий "
        "ранковий розпорядок без жодних відхилень.\n"
    )
    grounding_evidence = {
        "matched": ["Караман Grade 10, p.176"],
        "blockquotes_checked": 2,
    }
    plan = {"level": "a1", "sequence": 20, "word_target": 1200}

    report = linear_pipeline._long_uk_ceiling_gate(
        text,
        plan,
        grounding_evidence=grounding_evidence,
    )

    assert not any("Караман" in run for run in report.get("offending_runs", [])), (
        f"Karaman source blockquote should be exempt; got {report['offending_runs']}"
    )


def test_long_uk_ceiling_still_flags_uncited_learner_blockquote() -> None:
    """Without citation grounding, learner practice blockquotes stay in
    scope. Fixture extended 2026-05-17 to exceed the m15-24 ceiling
    bumped 50 → 80 by PR #2079 (the original 33-word fixture became a
    no-op once the ceiling rose above its length).
    """
    text = (
        "## Мій ранок\n\n"
        "> Спочатку прокидаюся о сьомій ранку коли ще темно за вікном "
        "потім швидко вмиваюся холодною водою бо нагрівач зламався і "
        "одягаюся в найтепліший одяг щоб не змерзнути коли поспішаю "
        "до автобуса о восьмій тридцять п'ять і дорогою купую гарячу "
        "каву в маленькій кав'ярні біля метро де баристу звати Олена "
        "і вона завжди питає чи я хочу скоринку до кави або один "
        "круасан з шоколадом який пече її молодший брат рано-вранці "
        "перед тим як він іде до університету де навчається інженерії "
        "програмного забезпечення і мріє переїхати працювати у "
        "Київ через два роки після завершення магістерської програми.\n"
    )
    plan = {"level": "a1", "sequence": 20, "word_target": 1200}

    report = linear_pipeline._long_uk_ceiling_gate(
        text,
        plan,
        grounding_evidence={"matched": [], "blockquotes_checked": 1},
    )

    assert report.get("offending_runs") or report.get("passed") is False


def test_citation_matcher_allows_small_page_drift_same_author_grade() -> None:
    """#1962: same author + grade may drift by a few pages."""
    result = linear_pipeline._citation_gate(
        [{"source_ref": "Кравцова, Українська мова, 4 клас, с. 112"}],
        {"references": [{"title": "Кравцова Grade 4, p.113"}]},
    )

    assert result["passed"] is True
    assert result["unknown"] == []


def test_citation_matcher_rejects_different_grade_even_small_page() -> None:
    """Different grade means a different lesson, even with nearby pages."""
    result = linear_pipeline._citation_gate(
        [{"source_ref": "Аврамченко, Українська мова, 6 клас, с. 112"}],
        {"references": [{"title": "Аврамченко Grade 4, p.113"}]},
    )

    assert result["passed"] is False
    assert result["unknown"] == ["Аврамченко, Українська мова, 6 клас, с. 112"]


def test_run_python_qg_passes_structural_fixture(tmp_path: Path) -> None:
    """Smoke test: the baseline `_passing_qg_fixture` produces a green report.

    Acts as the canary for run_python_qg. If a future change breaks the basic
    happy-path module shape, this test surfaces it before any of the targeted
    bugfix tests run.

    `l2_exposure_floor` is excluded from the aggregate assertion: Phase B
    (2026-05-13) calibrated its floors against deployed-corpus-scale content
    (~14 dialogue lines for a1-m15-24), which a 30-line synthetic fixture
    intentionally does not satisfy. That gate has dedicated coverage in
    `tests/test_immersion_gates.py`; the canary's job is the other 17 gates.
    """
    module_dir, plan_path, fake_verify = _passing_qg_fixture(tmp_path)

    report = linear_pipeline.run_python_qg(
        module_dir, plan_path, verify_words_fn=fake_verify
    )

    gates = report["gates"]
    failures = [
        name
        for name, g in gates.items()
        if isinstance(g, dict)
        and g.get("passed") is False
        and name != "l2_exposure_floor"
    ]
    assert failures == [], f"Unexpected gate failures: {failures}"
    assert gates["russianisms_clean"]["passed"] is True
    assert gates["surzhyk_clean"]["passed"] is True
    assert gates["calques_clean"]["passed"] is True
    assert gates["paronym_clean"]["passed"] is True


# ---------------------------------------------------------------------------
# Round 3.5 prompt-tighten regression tests (#1602)
# ---------------------------------------------------------------------------


def test_render_component_props_schema_lists_required_and_optional() -> None:
    """A1's allowed types must each get authoring required/optional lines.

    Round-3 (#1577) failed because the writer guessed `passage:` for `fill-in`
    and omitted `correct_order` on `order`. The POC M20 failure then showed
    that surfacing React component props misled Gemini into writing
    `quiz.questions`. The prompt must show authoring fields instead.
    """
    allowed = "fill-in, order, match-up, quiz"
    rendered = linear_pipeline._render_component_props_schema(allowed)

    # Each allowed type must produce its own bullet block.
    for activity_type in ("fill-in", "order", "match-up", "quiz"):
        assert f"- {activity_type}:" in rendered, (
            f"Missing bullet for activity type {activity_type!r} in:\n{rendered}"
        )

    # Required authoring field names must appear verbatim — these are the exact
    # keys the writer parser accepts.
    assert "items" in rendered, "FillIn / Order / MatchUp `items` prop missing"
    assert "correct_order" in rendered, (
        "Order `correct_order` prop missing — was the original round-3 failure"
    )
    quiz_block = rendered.split("- quiz:")[1].split("- ")[0]
    assert "items" in quiz_block
    assert "questions" not in quiz_block

    # Required and optional must be on different lines so the writer can tell
    # them apart.
    assert "    required authoring fields:" in rendered
    assert "    optional authoring fields:" in rendered


def test_render_component_props_schema_filters_to_allowed_types() -> None:
    """The schema renderer must NOT leak forbidden activity types.

    Forbidden types (e.g. `cloze`, `essay-response`, `paleography-analysis`)
    have their own authoring schemas. If the
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
    assert "    required authoring fields:" in schema_text


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
    assert "    required authoring fields:" in rendered
    assert "quiz`, `select`, and `translate`, use the authoring" in rendered


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


def test_linear_write_prompt_documents_non_textbook_role_url_requirement() -> None:
    """Regression for #1959: non-textbook resource entries require url:.

    The writer prompt lists valid roles, but the deterministic schema only
    allows `role: textbook` without a URL. This guards the direct instruction
    that unverifiable non-textbook entries should be omitted, not emitted with
    missing or placeholder URLs.
    """
    prompt_text = (
        linear_pipeline.PROJECT_ROOT / "scripts/build/phases/linear-write.md"
    ).read_text(encoding="utf-8")

    assert "role: textbook" in prompt_text, (
        "Template should reference role: textbook in the schema-rule explanation"
    )
    assert "OMIT THE ENTRY" in prompt_text, (
        "Template should instruct the writer to omit entries without verifiable URL"
    )
    normalized_prompt = prompt_text.lower()
    assert (
        "requires url" in normalized_prompt
        or "require a non-empty `url:`" in normalized_prompt
    ), "Template should explicitly state non-textbook roles require url"


def test_linear_write_prompt_mandates_dialoguebox_or_blockquote_for_dialogues() -> None:
    """#1962: writer must emit dialogues in gate-countable form."""
    template = (
        linear_pipeline.PROJECT_ROOT / "scripts/build/phases/linear-write.md"
    ).read_text(encoding="utf-8")

    assert "DialogueBox" in template
    assert "blockquote" in template.lower() or "`> `" in template
    assert "em-dash" in template.lower() or "anti-pattern" in template.lower()


def test_linear_write_prompt_requires_inline_gloss_within_8_tokens() -> None:
    """#1962: each dialogue line needs inline English gloss."""
    template = (
        linear_pipeline.PROJECT_ROOT / "scripts/build/phases/linear-write.md"
    ).read_text(encoding="utf-8")
    lower_template = template.lower()

    assert "inline gloss" in lower_template or "inline english" in lower_template
    assert "8 tokens" in template or "8 words" in template or "within 8" in template
    assert "block-bottom" in lower_template or "block bottom" in lower_template


def test_linear_write_prompt_restricts_non_plan_citations() -> None:
    """#1962: writer must not invent out-of-plan citations."""
    template = (
        linear_pipeline.PROJECT_ROOT / "scripts/build/phases/linear-write.md"
    ).read_text(encoding="utf-8")

    assert "plan_references" in template
    assert "Knowledge Packet" in template or "writer_tool_calls" in template
    assert "citations_resolve" in template


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
        assert "# WARNING: no authoring schema entry" in rendered, (
            f"Unresolved type {unresolved!r} did not produce a WARNING line; "
            f"rendered output was:\n{rendered}"
        )
    assert "DO NOT USE" in rendered
    # And the rendered output references the follow-up issue so future
    # readers can find context without grepping commit history.
    assert "#1604" in rendered


def test_render_component_props_schema_uses_authoring_shape_not_ts_types() -> None:
    """The writer prompt must expose authoring fields, not TypeScript props.

    The prompt used to render component prop types from lesson-schema.yaml.
    That leaked TypeScript/JSDoc details and, worse, component-side names like
    `questions` that are not valid authoring JSON. It now renders the compact
    authoring whitelist.
    """
    rendered = linear_pipeline._render_component_props_schema("odd-one-out")

    odd_block = rendered.split("- odd-one-out:")[1].split("- ")[0]
    assert "/**" not in odd_block, (
        f"TSDoc block leaked into rendered odd-one-out output:\n{odd_block}"
    )
    assert "*/" not in odd_block
    assert "@schemaDescription" not in odd_block
    assert "@ukrainianText" not in odd_block
    assert "required authoring fields: id, type, items" in odd_block


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


# ---------------------------------------------------------------------------
# #1624 round-3: _component_prop_gate must validate AUTHORING shape, not
# raw component-prop names. Surfaced by Codex re-review of PR #1627.
# ---------------------------------------------------------------------------


def test_component_prop_gate_accepts_authorial_intent_authoring_shape() -> None:
    """`authorial-intent` requires component props (excerpt, questions,
    modelAnswer) but the writer emits authoring fields (text_excerpt,
    prompt, model_answer). The gate must translate via the rename map."""
    activities = [
        {
            "id": "act-1",
            "type": "authorial-intent",
            "title": "Розкрити задум автора",
            "text_excerpt": "У темну нічну годину...",
            "prompt": "Що автор хоче передати?",
            "model_answer": "Автор передає тривогу через...",
        }
    ]
    report = linear_pipeline._component_prop_gate(activities)
    assert report["passed"], f"Expected canonical authoring shape to pass: {report['errors']}"


def test_component_prop_gate_rejects_authorial_intent_component_prop_names() -> None:
    """Mis-authored YAML using component-prop names (`excerpt:`, `questions:`,
    `modelAnswer:`) instead of authoring fields (`text_excerpt:`, `prompt:`,
    `model_answer:`) MUST fail the gate. If we accepted both, the parser
    at `_parse_authorial_intent` would silently produce an empty activity
    because it reads `text_excerpt:` not `excerpt:`."""
    activities = [
        {
            "id": "act-1",
            "type": "authorial-intent",
            "title": "Розкрити задум автора",
            "excerpt": "...",  # WRONG: dataclass-name, not authoring-name
            "questions": [{"q": "?"}],  # WRONG: component-prop name
            "modelAnswer": "...",  # WRONG: camelCase
        }
    ]
    report = linear_pipeline._component_prop_gate(activities)
    assert not report["passed"]
    assert any("text_excerpt" in err for err in report["errors"])
    assert any("prompt" in err for err in report["errors"])
    assert any("model_answer" in err for err in report["errors"])


def test_component_prop_gate_accepts_debate_snake_case_authoring() -> None:
    """`debate` requires camelCase `debateQuestion`; authoring uses snake_case."""
    activities = [
        {
            "id": "act-1",
            "type": "debate",
            "title": "Debate",
            "debate_question": "Чи був Хмельницький героєм?",
            "positions": [{"label": "За", "arguments": ["..."]}],
        }
    ]
    report = linear_pipeline._component_prop_gate(activities)
    assert report["passed"], f"Expected snake_case authoring to pass: {report['errors']}"


def test_component_prop_gate_accepts_paleography_imageurl_authoring() -> None:
    """`paleography-analysis` requires camelCase `imageUrl`; authoring uses
    snake_case `image_url`."""
    activities = [
        {
            "id": "act-1",
            "type": "paleography-analysis",
            "title": "Палеографія",
            "image_url": "https://example.com/manuscript.jpg",
            "hotspots": [{"x": 10, "y": 20, "label": "..."}],
        }
    ]
    report = linear_pipeline._component_prop_gate(activities)
    assert report["passed"], f"Expected snake_case authoring to pass: {report['errors']}"


def test_component_prop_gate_accepts_dialect_comparison_snake_case_authoring() -> None:
    """`dialect-comparison` requires camelCase `textA`/`textB`; authoring
    uses snake_case `text_a`/`text_b`."""
    activities = [
        {
            "id": "act-1",
            "type": "dialect-comparison",
            "title": "Compare",
            "text_a": "Sample A...",
            "text_b": "Sample B...",
            "features": [{"name": "f", "a": "...", "b": "..."}],
        }
    ]
    report = linear_pipeline._component_prop_gate(activities)
    assert report["passed"], f"Expected snake_case authoring to pass: {report['errors']}"


def test_component_prop_gate_accepts_source_evaluation_snake_case_authoring() -> None:
    """`source-evaluation` requires camelCase `sourceText`; authoring uses
    snake_case `source_text`."""
    activities = [
        {
            "id": "act-1",
            "type": "source-evaluation",
            "title": "Evaluate",
            "source_text": "Source text content...",
        }
    ]
    report = linear_pipeline._component_prop_gate(activities)
    assert report["passed"], f"Expected snake_case authoring to pass: {report['errors']}"


def test_component_prop_gate_skips_jsx_only_children_prop() -> None:
    """`mark-the-words` and `highlight-morphemes` require `children` in the
    React component, but authoring YAML doesn't have a top-level `children:`
    field — the JSX is rendered from inner content. The gate must skip
    `children` rather than reporting it as missing."""
    activities = [
        {
            "id": "act-1",
            "type": "mark-the-words",
            "title": "Mark",
            "text": "Sample text",
            "answers": ["word1", "word2"],
        },
        {
            "id": "act-2",
            "type": "highlight-morphemes",
        },
    ]
    report = linear_pipeline._component_prop_gate(activities)
    assert report["passed"], f"Expected JSX-only `children` to be skipped: {report['errors']}"


def test_component_prop_gate_still_reports_genuinely_missing_props() -> None:
    """The rename translation must NOT mask genuinely missing fields. An
    `authorial-intent` activity missing `text_excerpt` should fail."""
    activities = [
        {
            "id": "act-1",
            "type": "authorial-intent",
            "title": "Розкрити задум",
            # text_excerpt INTENTIONALLY omitted
            "prompt": "Що автор хоче передати?",
            "model_answer": "...",
        }
    ]
    report = linear_pipeline._component_prop_gate(activities)
    assert not report["passed"]
    assert any("text_excerpt" in err for err in report["errors"])


def test_component_to_authoring_renames_cover_known_renames() -> None:
    """Drift guard: every type in the rename map must also be in the
    authoring whitelist (so a rename can't reference a type the parser
    doesn't know about) AND every renamed AUTHORING field name must be in
    that type's authoring whitelist (so the renamed field can pass strict
    JSON validation)."""
    for activity_type, rename_map in linear_pipeline._COMPONENT_TO_AUTHORING_RENAMES.items():
        assert activity_type in linear_pipeline._ACTIVITY_AUTHORING_FIELDS, (
            f"_COMPONENT_TO_AUTHORING_RENAMES has type {activity_type!r} "
            f"that is not in _ACTIVITY_AUTHORING_FIELDS"
        )
        allowed = linear_pipeline._ACTIVITY_AUTHORING_FIELDS[activity_type]
        for component_prop, authoring_field in rename_map.items():
            assert authoring_field in allowed, (
                f"Type {activity_type!r}: rename {component_prop!r} -> "
                f"{authoring_field!r}, but {authoring_field!r} is not in "
                f"the authoring whitelist for that type"
            )


def test_component_prop_gate_consistent_with_strict_json_parser_for_a1_20() -> None:
    """End-to-end: an A1/20-shaped activity list (covers the rename-affected
    types we care about) passes the strict-JSON parser AND the
    component-prop gate without contradiction."""
    activities = [
        {"id": "act-1", "type": "match-up", "title": "Match",
         "pairs": [{"left": "a", "right": "b"}]},
        {"id": "act-2", "type": "quiz", "title": "Quiz",
         "items": [{"question": "?", "options": [{"text": "A", "correct": True}]}]},
        {"id": "act-3", "type": "fill-in", "title": "Fill",
         "items": [{"sentence": "Я ____ о сьомій.", "answer": "прокидаюся"}]},
        {"id": "act-4", "type": "translate", "title": "Translate",
         "items": [{"source": "I wake up.", "target": "Я прокидаюся."}]},
        {"id": "act-5", "type": "true-false", "title": "TF",
         "items": [{"statement": "...", "isCorrect": True}]},
        {"id": "act-6", "type": "unjumble", "title": "Order words",
         "items": [{"sentence": "...", "answer": "..."}]},
        {"id": "act-7", "type": "odd-one-out", "title": "Odd",
         "items": [{"options": ["a", "b", "c"], "correctAnswer": "c"}]},
        {"id": "act-8", "type": "order", "title": "Order steps",
         "items": ["a", "b", "c"], "correct_order": [0, 1, 2]},
        {"id": "act-9", "type": "error-correction", "title": "Find err",
         "items": [{"sentence": "Він вмиваєця.", "errorWord": "вмиваєця",
                    "correctForm": "вмивається", "explanation": "..."}]},
    ]
    # First gate: strict-JSON parser
    linear_pipeline._validate_writer_json_artifact("activities.yaml", activities)
    # Second gate: component-prop gate
    report = linear_pipeline._component_prop_gate(activities)
    assert report["passed"], (
        f"A1/20 activity list must pass BOTH gates without contradiction. "
        f"Errors: {report['errors']}"
    )


def test_strip_metalinguistic_removes_avoid_markers() -> None:
    """`<!-- bad -->X<!-- /bad -->` callouts get stripped before VESUM lookup.

    Russianism / surzhyk / calque pedagogical callouts in prose (e.g.,
    "stick to сніданок, not the Russian-borrowed завтрак") deliberately
    show a non-VESUM form for learner contrast. The HTML-comment marker
    keeps the bad form visible in rendered MDX (comments don't render)
    while preventing the `vesum_verified` gate from flagging it as a
    false positive.
    """
    text = (
        "Stick to сніданок (not the Russian-borrowed "
        "<!-- bad -->завтрак<!-- /bad -->), рушник "
        "(not <!-- bad -->полотенце<!-- /bad -->)."
    )
    stripped = linear_pipeline._strip_metalinguistic(text)
    assert "завтрак" not in stripped
    assert "полотенце" not in stripped
    # The Ukrainian-preferred forms must survive.
    assert "сніданок" in stripped
    assert "рушник" in stripped


def test_strip_metalinguistic_avoid_marker_handles_multiline_and_spacing() -> None:
    """The marker tolerates surrounding whitespace and a multi-line span."""
    text = (
        "Avoid the surzhyk form <!--   bad   -->\nодіватися\n<!--   /bad   -->\n"
        "and use одягатися instead."
    )
    stripped = linear_pipeline._strip_metalinguistic(text)
    assert "одіватися" not in stripped
    assert "одягатися" in stripped


def test_strip_metalinguistic_avoid_marker_keeps_adjacent_callouts_separate() -> None:
    """Two adjacent `<!-- bad -->` spans don't fuse via greedy matching."""
    text = "<!-- bad -->завтрак<!-- /bad --> та <!-- bad -->полотенце<!-- /bad -->"
    stripped = linear_pipeline._strip_metalinguistic(text)
    assert "завтрак" not in stripped
    assert "полотенце" not in stripped
    # The Ukrainian connector word "та" survives between the two stripped spans.
    assert "та" in stripped


def test_strip_metalinguistic_warning_quote_pattern() -> None:
    """Negative examples after `not` / `не` are warning prose, not VESUM claims.

    Three surface forms must all strip the negative example:
      1. Straight quotes:  `not "X"` / `не "X"`
      2. Guillemets:       `not «X»` / `не «X»`
      3. Markdown italics: `not *X*` / `не *X*`

    The italic variant was added 2026-05-17 after a1/m20 rebuild #2 surfaced
    `*дивюся*` from the writer's `*я дивлюся*, not *дивюся*` contrast
    pattern. Bold (`**X**`) is INTENTIONALLY not matched — writers reserve
    bold for the CORRECT form (e.g. the epenthetic `**л**` being taught).
    """
    ascii_quote = linear_pipeline._strip_metalinguistic('я дивлюся, not "дивюся"')
    guillemet_quote = linear_pipeline._strip_metalinguistic("кажуть, not «дивюся»")
    italic_en_quote = linear_pipeline._strip_metalinguistic(
        "Group II first-person inserts **л**: *я дивлюся*, not *дивюся*."
    )
    italic_uk_quote = linear_pipeline._strip_metalinguistic(
        "Use *сніданок*, не *завтрак*."
    )
    legitimate_quote = linear_pipeline._strip_metalinguistic(
        'the word "ранок" means morning'
    )
    bold_correct_form = linear_pipeline._strip_metalinguistic(
        "Bold **дивлюся** is the correct form."
    )

    assert "дивюся" not in ascii_quote
    assert "дивюся" not in guillemet_quote
    assert "дивюся" not in italic_en_quote
    assert "завтрак" not in italic_uk_quote
    # The CORRECT form in italics must survive (it's not after a negator).
    assert "дивлюся" in italic_en_quote
    assert "сніданок" in italic_uk_quote
    assert "ранок" in legitimate_quote
    # Bold-wrapped correct forms are not negated; must reach VESUM intact.
    assert "дивлюся" in bold_correct_form


def test_collapse_syllable_break_strips_textbook_hyphens() -> None:
    """Textbook syllable-break notation (`за-пи-са-ний`, `у-весь`) collapses
    to the canonical lemma, while real compound nouns survive.

    Surfaced 2026-05-17 by a1/m20 rebuild #5: the writer quoted the
    Захарійчук Grade 1 p.24 Frog & Toad excerpt verbatim including the
    textbook's own syllable-break hyphens, and VESUM failed on the
    hyphenated forms.

    Heuristic: 2+ hyphen-separated parts where ALL parts are ≤4 chars
    (Ukrainian syllable width). Real compounds always have at least one
    side >4 chars.
    """
    collapse = linear_pipeline._collapse_syllable_break
    # Textbook syllable breaks (the m20 triggers + close siblings).
    assert collapse("за-пи-са-ний") == "записаний"
    assert collapse("у-весь") == "увесь"
    assert collapse("ад-же") == "адже"
    # Real compound nouns / linguistic terminology MUST survive.
    assert collapse("темно-синій") == "темно-синій"
    assert collapse("Івано-Франківськ") == "Івано-Франківськ"
    assert collapse("я-форма") == "я-форма"  # `форма` is 5 chars
    assert collapse("англо-український") == "англо-український"
    # Edge cases.
    assert collapse("noдашь") == "noдашь"  # no hyphen → unchanged
    assert collapse("a") == "a"  # single char → unchanged


def test_textbook_match_tokens_strips_syllable_breaks_symmetrically() -> None:
    """`_textbook_match_tokens` applies `_collapse_syllable_break` so the
    matcher normalizes the writer-side and chunk-side identically.

    Surfaced 2026-05-17 during m20 Path A: the writer-prompt now instructs
    "strip pedagogical syllable hyphens before pasting" (writer-prompt §2
    Textbook syllable-break notation). The textbook chunk text usually
    KEEPS those hyphens. Without symmetric stripping, a writer who follows
    the instruction would produce a clean quote (`записаний увесь мій
    день`) that fails to match the hyphenated chunk (`за-пи-са-ний у-весь
    мій день`).

    Both sides must normalize to the SAME stripped token list so the
    sliding-window containment check in `_contains_textbook_quote`
    succeeds regardless of whether the writer stripped at write time or
    copied verbatim.
    """
    tokens = linear_pipeline._textbook_match_tokens
    # `_normalize_match_text` does NFD decomposition + strips combining
    # marks before tokenization, so й→и and ї→і in the final tokens
    # (diacritic-insensitive matching by design).
    # Hyphenated textbook display form and clean canonical form must
    # produce IDENTICAL token sequences after symmetric normalization.
    hyphenated = tokens("За-пи-са-ний у-весь мій день.")
    canonical = tokens("Записаний увесь мій день.")
    assert hyphenated == canonical, (
        f"Symmetric normalization broken: {hyphenated!r} != {canonical!r}"
    )
    # `й` decomposes to `и` + combining breve → stripped to `и`.
    # `і` is pre-composed without combining marks → preserved as `і`.
    # `ї` decomposes to `і` + combining diaeresis → stripped to `і`.
    assert hyphenated == ["записании", "увесь", "міи", "день"]
    # Real compounds and linguistic terminology stay hyphenated on BOTH
    # sides — `_collapse_syllable_break` rejects parts >4 chars.
    compounds = tokens("Івано-Франківськ темно-синій я-форма")
    assert compounds == ["івано-франківськ", "темно-синіи", "я-форма"]


def test_textbook_grounding_matches_punctuation_different_attribution(
    tmp_path: Path,
) -> None:
    quote = (
        "Ранковий план Євгена простий і послідовний. Уранці він устав із "
        "ліжка сам, прибрав ліжко сам, зробив зарядку сам, на кухні "
        "поставив чашку, після сніданку помив посуд, а тато усміхався "
        "й уважно дивився на сина."
    )
    module_text = "\n".join(
        [
            "## Ранковий план",
            "",
            f"> {quote}",
            "",
            "*— Захарійчук, Grade 1, p.24*",
            "",
        ]
    )
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    (module_dir / "writer_tool_calls.json").write_text(
        json.dumps(
            [
                {
                    "name": "mcp__sources__search_text",
                    "result": [{"source_type": "textbook", "text": quote}],
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    plan = {"level": "a1", "references": [{"title": "Захарійчук Grade 1, p.24"}]}
    wrong_page_plan = {
        "level": "a1",
        "references": [{"title": "Захарійчук Grade 1, p.52"}],
    }

    assert linear_pipeline._citation_ref_text_contains(
        "Захарійчук Grade 1, p.24",
        "— Захарійчук, Grade 1, p.24",
    )
    assert not linear_pipeline._citation_ref_text_contains(
        "Захарійчук Grade 1, p.52",
        "— Захарійчук, Grade 1, p.24",
    )
    report = linear_pipeline._textbook_grounding_gate(module_text, plan, module_dir)
    wrong_page_report = linear_pipeline._textbook_grounding_gate(
        module_text,
        wrong_page_plan,
        module_dir,
    )

    assert report["passed"] is True
    assert report["matched"] == ["Захарійчук Grade 1, p.24"]
    assert wrong_page_report["passed"] is False
    assert wrong_page_report["matched"] == []
    assert wrong_page_report["missing"] == ["Захарійчук Grade 1, p.52"]


def test_count_uk_example_bullets_includes_table_rows() -> None:
    """`_count_uk_example_bullets` counts both bullet-list lines AND
    markdown table data rows containing UK content.

    Surfaced 2026-05-17 by a1/m20 Path A rebuild: writer produced
    13 bullet UK examples + 8 table-row UK examples (5 contrast pairs
    + 3 pronunciation rows) but the counter only saw bullets, failing
    `l2_exposure_floor` by one despite pedagogical density well over
    the floor of 14.

    Tables are a valid pedagogical surface for UK example sentences:
    contrast tables (Wrong / Right pairs), paradigm tables, IPA tables,
    and pronunciation reference tables all expose UK forms in context.
    Counting only bullets under-counts modules that prefer tabular
    presentation, which were precisely what m20 used.
    """
    count = linear_pipeline._count_uk_example_bullets
    # Bullets alone — baseline (the pre-fix behavior).
    assert count("- я прокидаюся о сьомій\n- я вмиваюся холодною водою\n") == 2
    # Table rows alone — new behavior.
    table_only = (
        "| ❌ Wrong | ✅ Right | Why |\n"
        "|---|---|---|\n"
        "| Я прокидаєшся | Я прокидаюся | Person changes |\n"
        "| Я мию себе | Я миюся | -ся carries 'myself' |\n"
    )
    assert count(table_only) == 2  # 2 data rows, header + separator excluded
    # Mixed bullets + table — both counted.
    mixed = (
        "- я прокидаюся о сьомій\n"
        "- я вмиваюся холодною водою\n"
        "\n"
        "| Written | Spoken | Example |\n"
        "|---|---|---|\n"
        "| **-шся** | [с':а] | ти прокидаєшся → [прокидайес':а] |\n"
        "| **-ться** | [ц':а] | він прокидається → [прокидайец':а] |\n"
    )
    assert count(mixed) == 4
    # Separator-only / empty-cell rows are excluded; English-only rows
    # are excluded (no UK word in any cell).
    no_uk = (
        "| Hello | World | Greeting |\n"
        "|---|---|---|\n"
        "| Apple | Banana | Cherry |\n"
    )
    assert count(no_uk) == 0


def test_warning_quote_unclosed_italic_terminated_by_punctuation() -> None:
    """`not *X.` / `не *X,` / `not *X<EOS>` — unclosed italics terminated by
    sentence punctuation or end-of-string also strip the anti-example.

    PR #2076 added closed-italic handling (`not *X*`). a1/m20 rebuild #4
    (2026-05-17) surfaced the unclosed variant: the writer typed
    `In II-conjugation: дивлюся, not *дивюся.` inside a JSON
    `"explanation"` field, where the sentence-ending period implicitly
    closes the italic span. The closed-italic-only regex missed it; the
    bare token `*дивюся` (with the opening asterisk attached) reached
    VESUM and tripped the gate.
    """
    cases = [
        # Unclosed italic + period (the m20 trigger)
        ("In II-conjugation: дивлюся, not *дивюся.", ["*дивюся"]),
        # Unclosed italic + comma
        ("кажуть, не *завтрак, а сніданок", ["завтрак"]),
        # Unclosed italic + end-of-string
        ("finally, not *X", ["*X"]),
        # Closed italic still works (regression)
        ("Use *сніданок*, не *завтрак*.", ["завтрак"]),
        # Quote still works (regression)
        ('Say not "X" but Y.', ['"X"']),
    ]
    for text, must_be_gone in cases:
        stripped = linear_pipeline._strip_metalinguistic(text)
        for fragment in must_be_gone:
            assert fragment not in stripped, (
                f"anti-example {fragment!r} should be stripped from {text!r}, "
                f"got {stripped!r}"
            )

    # Bold-wrapped CORRECT form must survive.
    bold = linear_pipeline._strip_metalinguistic("Bold **дивлюся** stays.")
    assert "дивлюся" in bold, (
        f"bold-wrapped correct form should survive, got {bold!r}"
    )


def test_proper_name_whitelist_covers_ya_forma() -> None:
    """`я-форма` and its declined forms are pedagogical Ukrainian
    linguistics terminology, not a VESUM lemma. Whitelist must cover
    the surface forms a writer can realistically emit so the m20
    `Інфінітив ↔ я-форма` activity title doesn't trip the gate."""
    from scripts.audit.config import PROPER_NAME_WHITELIST

    whitelist_lc = {name.lower() for name in PROPER_NAME_WHITELIST}
    for surface in (
        "я-форма",  # nom
        "я-форми",  # gen / nom-pl
        "я-формі",  # dat / loc
        "я-форму",  # acc
        "я-формою",  # instr
    ):
        assert surface in whitelist_lc, (
            f"linguistic term {surface!r} must be in PROPER_NAME_WHITELIST "
            f"(VESUM does not contain hyphenated pronoun-forma compounds)"
        )


def test_iter_vesum_word_surfaces_skips_mixed_script_typos() -> None:
    """Mixed-script Cyrillic-abutting-Latin tokens are writer typos, not words.

    a1/m20 rebuild #3 (2026-05-17) surfaced this: the writer typed
    ``Buкварь`` in resources.yaml notes — Latin "Bu" + Cyrillic "кварь"
    with no boundary — and VESUM dutifully extracted the Cyrillic
    substring `кварь` and failed it. The token is a transcription typo
    of "Буквар" (the textbook title), not a real Ukrainian lemma. The
    correct behavior is to skip mixed-script tokens entirely so VESUM
    doesn't false-flag the orchestrator into chasing whitelists for
    writer fat-fingers.

    Real script transitions (Latin word followed by Cyrillic word across
    whitespace or punctuation) must NOT be affected — only direct
    letter-to-letter abutment fires the skip.
    """
    extract = linear_pipeline._iter_vesum_word_surfaces

    # Mixed-script typo: Cyrillic suffix abutting Latin prefix.
    assert extract("Buкварь, 2025") == [], (
        "mixed-script `Buкварь` should not yield `кварь` for VESUM check"
    )
    assert extract("Buкварь, частина перша") == ["частина", "перша"], (
        "mixed-script skip must not swallow adjacent clean Cyrillic words"
    )
    # Reverse: Cyrillic prefix abutting Latin suffix.
    assert extract("кварьs") == [], (
        "mixed-script `кварьs` (Cyrillic+Latin suffix) should be skipped"
    )

    # Clean Cyrillic of the same form passes through (so the skip is
    # specifically about the script boundary, not a content blacklist).
    assert "кварь" in extract("Я кварь."), (
        "the SAME token in a clean Cyrillic-only context must still reach VESUM"
    )

    # Latin and Cyrillic words separated by whitespace are independent.
    assert extract("English і Українська") == ["і", "Українська"]
    # ... and by punctuation.
    assert extract("English, Українська") == ["Українська"]


def test_normalize_for_vesum_morpheme_hyphen_conditional() -> None:
    """Hyphen inside emphasis collapses only for short morpheme fragments.

    PR #2068 introduced unconditional hyphen-strip-inside-emphasis to fix
    m20's reflexive morpheme pattern `прокида**ю-ся**`. That broke
    `**темно-синій**` (a real compound word). PR #2074 restored the
    distinction via a length heuristic: strip the hyphen only when at
    least one side is ≤3 chars (morpheme-fragment width). This test pins
    both arms of the heuristic so neither regresses.
    """
    # Morpheme breaks: at least one side is a short suffix fragment.
    # Both arms must collapse to the canonical lemma. All real-world m20
    # writer output uses a single hyphen per emphasis span; multi-hyphen
    # tokens are intentionally NOT collapsed (the heuristic is conservative
    # — see `_strip_morpheme_hyphen` for the rationale).
    morpheme_cases = {
        "прокида**ю-ся**": "прокидаюся",
        "прокида**ють-ся**": "прокидаються",
        "прокида**ємо-ся**": "прокидаємося",
        "прокида**єте-ся**": "прокидаєтеся",
        "прокида**єть-ся**": "прокидається",
        "прокида**єш-ся**": "прокидаєшся",
    }
    for emphasized, expected in morpheme_cases.items():
        normalized = linear_pipeline._normalize_for_vesum(emphasized)
        assert normalized == expected, (
            f"morpheme break {emphasized!r} should normalize to {expected!r}, "
            f"got {normalized!r}"
        )

    # Real compound words: both halves are full lexemes — hyphen survives.
    compound_cases = {
        "**темно-синій**": "темно-синій",
        "*жовто-блакитний*": "жовто-блакитний",
        "**Івано-Франківськ**": "Івано-Франківськ",
        "_південно-східний_": "південно-східний",
    }
    for emphasized, expected in compound_cases.items():
        normalized = linear_pipeline._normalize_for_vesum(emphasized)
        assert normalized == expected, (
            f"compound word {emphasized!r} must preserve its hyphen, "
            f"got {normalized!r}"
        )


def test_strip_metalinguistic_collapses_bold_wrapped_morpheme_labels() -> None:
    """`-**юся**` collapses to `-юся` so the morpheme regex can strip it.

    Conjugation-table rows like `| -**юся** | -**єшся** | -**ється** |`
    pair a hyphen with a bold-wrapped morpheme suffix. The morpheme regex
    requires the hyphen to sit directly next to a Cyrillic letter, so the
    `**` between them previously blocked the strip and the suffix
    surfaced as a non-VESUM token (`юся` is not a lemma).
    """
    text = "| -**юся** | -**єшся** | -**ється** | -ємося | -єтеся | -ються |"
    stripped = linear_pipeline._strip_metalinguistic(text)
    # All six morpheme suffix forms should be gone after stripping.
    for fragment in ("юся", "єшся", "ється", "ємося", "єтеся", "ються"):
        assert fragment not in stripped, (
            f"morpheme fragment '{fragment}' should be stripped from the gate "
            f"text but survived: {stripped!r}"
        )


def test_strip_metalinguistic_preserves_bold_lemmas_in_running_prose() -> None:
    """Plain bold-emphasized Ukrainian lemmas still reach VESUM lookup intact.

    Bold-unwrap in `_strip_metalinguistic` is for the morpheme-regex
    pass-through. After the regex runs, the unwrapped lemma must still
    appear in the gate text so a real misspelling inside `**...**`
    (e.g. `**прокидаюсь**`) is still verified.
    """
    text = "Stick to **сніданок** and **рушник**, not **полотенце**."
    stripped = linear_pipeline._strip_metalinguistic(text)
    for lemma in ("сніданок", "рушник", "полотенце"):
        assert lemma in stripped, f"bold-unwrapped lemma '{lemma}' should survive"


def test_contract_yaml_handles_dict_shape_vocabulary_hints() -> None:
    """CORE plans express vocabulary_hints as `{required: [...], optional: [...]}`."""
    plan = {
        "content_outline": [{"section": "S", "words": 100, "points": ["p1"]}],
        "activity_hints": [],
        "references": [{"title": "Ref"}],
        "vocabulary_hints": {
            "required": [{"word": "сніданок", "pos": "ч.", "definition": "ранкова їжа"}],
            "optional": [],
        },
    }
    out = linear_pipeline._contract_yaml(plan)
    assert "vocabulary_required" in out
    assert "сніданок" in out


def test_contract_yaml_handles_list_shape_vocabulary_hints() -> None:
    """Seminar plans (most LIT + BIO) express vocabulary_hints as a bare list.

    Regression for the 2026-05-20 seminar smoke build that crashed on
    `'list' object has no attribute 'get'` while rendering the writer
    prompt for `lit/natalka-poltavka`. `_vocabulary_lemmas` (line ~895)
    already handled both shapes; `_contract_yaml` lagged.
    """
    plan = {
        "content_outline": [{"section": "S", "words": 100, "points": ["p1"]}],
        "activity_hints": [],
        "references": [{"title": "Ref"}],
        "vocabulary_hints": [
            {"word": "сентименталізм", "pos": "ч.", "definition": "літ. напрям"},
            {"word": "ремарка", "pos": "ж.", "definition": "авторська вказівка"},
        ],
    }
    out = linear_pipeline._contract_yaml(plan)
    assert "vocabulary_required" in out
    assert "сентименталізм" in out
    assert "ремарка" in out


def test_contract_yaml_tolerates_missing_vocabulary_hints() -> None:
    """Plans without vocabulary_hints render an empty required list."""
    plan = {
        "content_outline": [{"section": "S", "words": 100, "points": ["p1"]}],
        "activity_hints": [],
        "references": [{"title": "Ref"}],
    }
    out = linear_pipeline._contract_yaml(plan)
    assert "vocabulary_required: []" in out


# ---------------------------------------------------------------------------
# Gate relaxations (2026-05-23) — user-direction enforcement
# ---------------------------------------------------------------------------
#
# Two surgical relaxations were applied to the `plan_sections` and
# `vesum_verified` gates after the 2026-05-21 a1/my-morning build #13
# terminal cascade exposed two structural false-positive patterns:
#
# 1. `plan_sections` failed on per-section min/max bounds when the writer's
#    word_count correction rebalanced total but left one section ~5% short.
#    User direction: "the section wordcount is a guidance for the writer,
#    it is not a reason to drop an error. The important is that the whole
#    content is a whole and not less than the planned word count."
#
# 2. `vesum_verified` failed on legitimate hyphenated multi-word
#    constructions like `літера-в-літеру` ("letter by letter") which VESUM
#    only indexes by single lemma. User direction: "there are many of these
#    kind of constructions in the Ukrainian language, do not drop [an]
#    error if VESUM is not supporting it but we need to be able to check
#    if they are correct with another tool."
#
# The tests below pin those relaxations against regression.


def test_section_gate_passes_when_section_below_min_but_present() -> None:
    """Per-section under-min does NOT fail the gate (advisory only).

    Reflects user direction 2026-05-23: per-section word counts are
    GUIDANCE for the writer, not a build-fail trigger. The gate-level
    `passed` reflects only missing headings. Per-section budgets are
    retained as diagnostics so the writer correction prompt can use them
    for targeting guidance, but they do NOT halt the build.

    The 2026-05-21 a1/my-morning build #13 cascade — where the writer's
    word_count r1 correction landed total at 1200 but left Діалоги
    (257/270 = 95%) and Мій ранок (265/270 = 98%) under their per-section
    min while Підсумок overshot, triggering terminal halt — is the
    canonical failure pattern this relaxation prevents.
    """
    plan = {
        "content_outline": [
            {"section": "Діалоги", "words": 300, "points": ["p1"]},
            {"section": "Підсумок", "words": 300, "points": ["p2"]},
        ]
    }
    # Діалоги only has ~50 words (well below min=270). Підсумок has plenty.
    # Both sections are PRESENT as headings.
    text = (
        "## Діалоги\n\n"
        + ("слово " * 50)
        + "\n\n## Підсумок\n\n"
        + ("слово " * 500)
        + "\n"
    )
    report = linear_pipeline._section_gate(text, plan)
    assert report["passed"] is True, (
        "Per-section under-min must not fail the gate per user direction "
        "2026-05-23"
    )
    # Diagnostic budgets still reflect the per-section state.
    budgets = {item["section"]: item for item in report["word_budgets"]}
    assert budgets["Діалоги"]["under_min"] is True
    assert budgets["Діалоги"]["passed"] is False  # per-section advisory marker
    assert budgets["Підсумок"]["over_max"] is True
    assert budgets["Підсумок"]["under_min"] is False


def test_section_gate_fails_on_missing_heading() -> None:
    """A contracted section absent from module.md still fails the gate.

    Missing headings remain a hard fail — the writer must emit every
    section the plan contracted for. Only per-section word counts were
    relaxed by the 2026-05-23 change.
    """
    plan = {
        "content_outline": [
            {"section": "Діалоги", "words": 300, "points": ["p1"]},
            {"section": "Підсумок", "words": 300, "points": ["p2"]},
        ]
    }
    text = "## Діалоги\n\n" + ("слово " * 320) + "\n"  # Підсумок absent
    report = linear_pipeline._section_gate(text, plan)
    assert report["passed"] is False
    assert "Підсумок" in report["missing_headings"]


def test_section_gate_passes_when_sections_overshoot_max() -> None:
    """Section overshoot (count > max) does not fail the gate either.

    Reaffirms the pre-existing rule that max_words is diagnostic-only
    ("more is always welcome" — user direction 2026-05-17 + 2026-05-23).
    """
    plan = {
        "content_outline": [
            {"section": "Підсумок", "words": 300, "points": ["p1"]},
        ]
    }
    # 600 words: well over max=330 but max is diagnostic.
    text = "## Підсумок\n\n" + ("слово " * 600) + "\n"
    report = linear_pipeline._section_gate(text, plan)
    assert report["passed"] is True
    budget = report["word_budgets"][0]
    assert budget["over_max"] is True
    assert budget["under_min"] is False


def test_vesum_gate_accepts_hyphenated_multi_word_compound_when_parts_verify() -> None:
    """Hyphenated multi-word constructions where all parts verify pass.

    Per user direction 2026-05-23: VESUM only indexes single lemmas, so
    legitimate hyphenated phrases like `літера-в-літеру` (`letter by
    letter`) need a fallback verification. The gate now splits on hyphens
    and verifies each constituent above the lookup threshold; if every
    part itself is a valid VESUM form, the compound is accepted.
    """
    # `літера-в-літеру`: every constituent (літера, в, літеру) verifies
    # in real VESUM. `в` is below VESUM_MIN_WORD_LENGTH=3 and is accepted
    # without lookup. The other two are listed as `known`. The surrounding
    # vocab (`слово`) is also declared so the test isolates compound-
    # handling from incidental missing-word false-positives.
    fake_verify = _build_fake_verify_words(
        known={"літера": True, "літеру": True, "слово": True},
    )
    report = linear_pipeline._vesum_gate(
        module_text="Слово літера-в-літеру.",
        activities=[],
        vocabulary=[],
        resources=[],
        verify_words_fn=fake_verify,
    )
    assert "літера-в-літеру" not in report["missing"]
    assert report["passed"] is True


def test_vesum_gate_still_fails_hyphenated_compound_when_part_is_russianism() -> None:
    """A hyphenated compound containing an unrecognized part still fails.

    The constituent fallback is conservative — it accepts compounds ONLY
    when every above-threshold part itself verifies. A hypothetical
    Russified compound like `буквенного-щось` (where `буквенного` is a
    real Russianism not in VESUM) MUST still fail the gate — otherwise
    the relaxation would create a Russianism-laundering loophole via
    hyphenation.
    """
    # `буквенного` is NOT in real VESUM (Russified form; standard is
    # `буквений`). `щось` is real Ukrainian (`something`). Compound fails.
    fake_verify = _build_fake_verify_words(
        known={"щось": True, "слово": True},
    )
    report = linear_pipeline._vesum_gate(
        module_text="Слово буквенного-щось.",
        activities=[],
        vocabulary=[],
        resources=[],
        verify_words_fn=fake_verify,
    )
    # The compound stays missing because `буквенного` constituent fails.
    assert "буквенного-щось" in report["missing"]
    assert report["passed"] is False


def test_vesum_gate_hyphenated_compound_accepted_when_only_short_parts() -> None:
    """Hyphenated compounds of only-short-tokens are accepted conservatively.

    Edge case: `і-і-і` or `у-у-у` — strings of short prepositions/
    conjunctions all below VESUM_MIN_WORD_LENGTH=3 — are not realistic
    Ukrainian forms but if they ever appear, the fallback accepts them
    conservatively (there are no constituents to verify, so no constituent
    fails). This prevents the gate from blocking on unverifiable noise.
    """
    fake_verify = _build_fake_verify_words(known={"слово": True})
    report = linear_pipeline._vesum_gate(
        # `і-і-і` (3-part compound of single-char tokens). All below
        # VESUM_MIN_WORD_LENGTH=3.
        module_text="Слово і-і-і.",
        activities=[],
        vocabulary=[],
        resources=[],
        verify_words_fn=fake_verify,
    )
    # 'і-і-і' wouldn't reach VESUM at all (below min length on the whole
    # compound). The test is structurally a smoke test that the fallback
    # doesn't crash on degenerate inputs.
    assert report.get("error") is None

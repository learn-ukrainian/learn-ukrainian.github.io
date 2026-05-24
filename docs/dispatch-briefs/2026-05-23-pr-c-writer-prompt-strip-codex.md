# Dispatch brief — PR-C: writer prompt strip + stale-constant fixes + per-rule firing telemetry

**Agent:** codex (judgment-heavy prompt restructure, codex has the deepest knowledge of how this prompt is consumed)
**Task ID:** `pr-c-writer-prompt-strip-2026-05-23`
**Worktree:** auto via `--worktree`
**Mode:** `danger`
**Effort:** `xhigh`
**Base SHA:** `c363726b44` (post-PR-B merge) or newer
**Authority:** session-state handoff `docs/session-state/2026-05-23-architectural-reset-strip-v7-llm-demote.md` decision row C; cross-model reviews from codex (msg #1076) + gemini (msg #1075) on 2026-05-23.

## #M-4 preamble — anti-fabrication requirements

Every verifiable claim MUST be tool-backed with command + cwd + raw output triple:

| Claim | Evidence |
|---|---|
| Prompt size measured | `wc -c scripts/build/phases/linear-write.md` raw |
| Rendered prompt size measured | `wc -c curriculum/l2-uk-en/a1/my-morning/writer_prompt.md` (or fresh render via `.venv/bin/python scripts/build/v7_build.py a1 my-morning --dry-run-prompt` if such flag exists; else render manually) |
| Tests pass | `.venv/bin/python -m pytest tests/test_writer_prompt_size.py tests/test_linear_pipeline_telemetry.py -v` + raw final line |
| Lint clean | `.venv/bin/ruff check scripts/build/phases/linear-write.md scripts/audit/check_writer_prompt_size.py tests/test_writer_prompt_size.py` + raw final line |
| Commit landed | `git log -1 --oneline` raw |
| PR opened | `gh pr view --json url --jq .url` raw URL |

---

## Context

V7 writer prompt at `scripts/build/phases/linear-write.md` is 67KB raw template, renders to 194KB for a1/my-morning. Empirically past everyone's reliable instruction-following ceiling — 4 weeks of V7 builds shipped 0 modules. Both adversarial reviews (codex msg #1076, gemini msg #1075) on the strip plan converged on the load-bearing keeps and surfaced critical changes.

**Strip plan source:** `audit/2026-05-23-writer-prompt-strip-plan/REPORT.html` (read first).

**Codex review (msg #1076 verdict REVISE):**
- 80KB rendered target is unreachable without per-module data restructure (PR-D scope)
- Realistic floor for codex-tools reliability: **115-140KB rendered for A1**
- Critical bugs in current prompt: stale `±5%` at line 18 (PR-B made gate `±8%`), stale `callout_min = 2` reference around line 578 (PR-B made it `1`)
- KEEP carve-outs: `{ALLOWED_ACTIVITY_TYPES}`, `{INLINE_ALLOWED_TYPES}`, `{WORKBOOK_ALLOWED_TYPES}`, `{COMPONENT_PROPS_SCHEMA}` MUST stay inline; appendix won't be reliably fetched mid-write
- When dropping `<bad_form_audit>` visible line, **KEEP the scan rule + examples at lines 145-167** (different from the visible audit line)
- NORTH_STAR anchors to KEEP verbatim: adult peer voice (north-star.md:61-64), B1+ no English outside Tab 2 (112-120, 253-268, 330-334), source grounding / no ghost authority (180-193), decolonized framing (195-203, 342-352), activities test language not trivia (353-356)

**Gemini review (msg #1075 verdict SHIP):**
- DEDUP `{KNOWLEDGE_PACKET}` confirmed safe (no writer logic depends on line 791 location)
- NEW compression: `phonetic_rules` manifest entries — move "how to format IPA" prose to single PHONETIC_REFERENCE block, strip manifest to raw `[form, target]` pairs
- NEW compression: Wiki Obligations Manifest prose to raw IDs + 1-sentence summaries (the "How" is in IMPLEMENTATION_MAP_CONTRACT)
- Telemetry design: **ONE ID per failure class**, NOT per rule statement (e.g. all 3 anti-meta-narration rules tag `#R-VOICE-META`)
- KEEP forbidden meta-prose list verbatim in Writer Charter (don't abstract — it's the #1 A1 regression source)
- KEEP Сибір case study reference (citation honesty enforcement)

## Revised target

**120KB rendered** (codex empirical estimate, not the original 80KB aspirational target). Raw template: ~30KB.

Enforcer: `scripts/audit/check_writer_prompt_size.py` fails CI if rendered prompt exceeds 130KB ceiling (10KB headroom for manifest variance across modules).

Below 120KB requires `{KNOWLEDGE_PACKET}` / `{WIKI_MANIFEST}` restructure (PR-D scope, NOT this PR).

---

## Steps — execute in order

### 1. Worktree setup

Auto-created at `.worktrees/dispatch/codex/pr-c-writer-prompt-strip-2026-05-23/`. Your cwd is there.

```bash
git status --short  # expect empty
git log -1 --oneline  # expect c363726b44 or newer
wc -c scripts/build/phases/linear-write.md  # baseline raw
```

### 2. CRITICAL — fix stale constants from PR-B FIRST

These bugs predate the strip work. They create writer-vs-gate contradictions that will fail validation even if the strip succeeds.

**File:** `scripts/build/phases/linear-write.md`

Line 18 (inside `<word_budget>` block):
```
<word_budget>Section word allocation and running total check against {WORD_TARGET}±5%.</word_budget>
```
Change to:
```
<word_budget>Section word allocation and running total check against {WORD_TARGET} (gate tolerates 8% lower band per scripts/build/linear_pipeline.py::_word_count_gate).</word_budget>
```

Line ~578 (inside `**Engagement floor (REQUIRED — engagement_floor gate counts these).**` paragraph):
```
Every module MUST emit at least 2 content-anchored callouts.
```
Change to:
```
Every module MUST emit at least 1 content-anchored callout (PR-B 2026-05-23: floor lowered from 2→1; modules with 0 callouts still fail).
```

Verify no other stale references:
```bash
grep -n '±5%\|callout_min\|minimum 2' scripts/build/phases/linear-write.md
```

### 3. Apply Win #1 — KNOWLEDGE_PACKET dedup

**File:** `scripts/build/phases/linear-write.md` line 791

Current section:
```
## Full Wiki Context (source of truth for citations)

{KNOWLEDGE_PACKET}
```

Replace with:
```
## Full Wiki Context (source of truth for citations)

See `## Knowledge Packet` above. This is the same content; the prior render duplicated it as a token tax.
```

Verify `{KNOWLEDGE_PACKET}` appears exactly ONCE in the file:
```bash
grep -c '{KNOWLEDGE_PACKET}' scripts/build/phases/linear-write.md  # expect 1
```

### 4. Apply Win #2 — LESSON_CONTRACT §3 to appendix

**File 1:** create `docs/best-practices/writer-prompt-appendix.md` (NEW) containing the full LESSON_CONTRACT §3 "Component inventory — 1:1 mapping" content. Add this header at top:

```markdown
# Writer prompt appendix

Fetched on demand from `scripts/build/phases/linear-write.md` via @-path reference. Contains heavy reference material that doesn't fit the main writer prompt budget but remains canonical for writer / reviewer escalations.

## Component inventory — 1:1 mapping
[Full content from LESSON_CONTRACT §3 — copy verbatim from the current template substitution at scripts/build/phases/linear-write.md after the {LESSON_CONTRACT} expansion, specifically the "## 3. Component inventory" section.]
```

**File 2:** `scripts/build/phases/linear-write.md` — does NOT change directly. The change goes into the source `docs/lesson-contract.md` so the `{LESSON_CONTRACT}` substitution renders shorter. Find the source file:

```bash
grep -rn 'lesson-contract\|LESSON_CONTRACT' scripts/build/ | head -10
```

Edit the SOURCE of `LESSON_CONTRACT` (likely `docs/lesson-contract.md` or `docs/north-star.md` — locate empirically). Replace §3 "Component inventory — 1:1 mapping" body with:

```markdown
## 3. Component inventory — 1:1 mapping

See `docs/best-practices/writer-prompt-appendix.md` § Component inventory for the full React component → MDX mapping. The writer prompt does NOT inline this — the authoring fields (consumed by scripts/yaml_activities.py) are surfaced via the {COMPONENT_PROPS_SCHEMA} substitution and the §Activity Authoring Fields section in linear-write.md, which is what the writer acts on. Reference the appendix only if you need to debug a downstream MDX-render issue.
```

**Codex's required carve-out:** verify that after this change, the writer prompt STILL renders the following substitutions inline (they must NOT move to appendix):
- `{ALLOWED_ACTIVITY_TYPES}`
- `{INLINE_ALLOWED_TYPES}`
- `{WORKBOOK_ALLOWED_TYPES}`
- `{COMPONENT_PROPS_SCHEMA}`

If any of these accidentally moved to the appendix, REVERT that part. These are write-time-required.

### 5. Apply Win #3 — NORTH_STAR compression with required anchors

**Source file:** locate via `grep -rn '## WHO — the learner\|NORTH_STAR' scripts/build/` — likely `docs/north-star.md`.

Replace the full NORTH_STAR doc with a compressed "Writer Charter" section. **MANDATORY include these anchors verbatim per codex review msg #1076 (find the matching lines in current `docs/north-star.md`):**

1. Adult peer voice, not childish gamification (north-star.md:61-64 current numbering)
2. B1+ no English outside Tab 2 (north-star.md:112-120, 253-268, 330-334)
3. Source grounding / no ghost authority (north-star.md:180-193)
4. Decolonized framing / Russian-imperial map (north-star.md:195-203, 342-352)
5. Activities test language not trivia (north-star.md:353-356)

**MANDATORY include verbatim per gemini review msg #1075:** the forbidden meta-prose list ("Welcome to…", "Let us…", "In this section…", "Now that you have seen…", etc.) — copy from the current `## Tone and immersion (mandatory)` section of linear-write.md verbatim.

Drop everything else from NORTH_STAR. Target charter size: ~5KB.

Add a reference line at the end of the Writer Charter:
```markdown
For the full north-star context, see `docs/north-star.md`. This charter is the write-time-actionable subset.
```

Then RESTORE the full content to `docs/north-star.md` (it remains the canonical doc; the charter is the writer-prompt-included excerpt).

### 6. Drop pre-emit `<bad_form_audit>` + `<activity_split_audit>` visible LINES

**File:** `scripts/build/phases/linear-write.md`

Delete the section `### Pre-emit bad-form audit (mandatory — #2095)` (lines 151-163 in current file). Specifically delete the paragraph that asks the writer to emit `<bad_form_audit>` and the 3-step scan instruction.

**CRITICAL per codex review:** the bad-form SCAN RULE itself (lines 145-167 in current — the `<!-- bad -->...<!-- /bad -->` marker convention + the FORBIDDEN PATTERNS enum) STAYS. The vesum_verified gate depends on this being in the writer's context. Only the visible audit-line emission ceremony is dropped.

After this delete, verify the bad-form marker convention paragraph + examples are intact:
```bash
grep -n 'bad form\|<!-- bad -->\|FORBIDDEN PATTERNS' scripts/build/phases/linear-write.md
```

Delete the section `### Pre-emit activity-split audit (MANDATORY — new gate...)` around lines 676-688. The activity-split deterministic gate (post-#2238) catches the same failures. Verify the INLINE/WORKBOOK split table and INJECT contract at lines 638-731 stay intact.

### 7. Apply gemini's NEW compressions

**Phonetic rules manifest compression:** locate the wiki manifest renderer:
```bash
grep -rn 'phonetic_rules\|WIKI_MANIFEST' scripts/build/ scripts/wiki/ | head -10
```

The current `phonetic_rules` entries in the manifest likely include prose like "format the IPA in single-character square brackets, place near the written form." Move that prose to a single block at the top of the manifest:

```markdown
## Phonetic format reference (applies to all phonetic_rules below)

- Spoken target in `[...]` single-character square brackets, not Unicode look-alikes
- Pair written and spoken form in close lexical proximity (same sentence or adjacent bullet)
- Copy ≥1 textbook example verbatim
```

Then each `phonetic_rules` entry compresses to `[form, target, optional_example]`. Estimated savings: 3-5KB per module.

**Wiki Obligations Manifest prose compression:** the manifest currently includes prose like "this obligation requires the writer to emit X at location Y with treatment Z." Most of that prose is now encoded in the IMPLEMENTATION_MAP_CONTRACT (deterministic, byte-stable). Strip manifest entries to:
- `obligation_id`
- 1-sentence summary
- Category (vocab / grammar / phonetics / culture / etc.)

The implementation map contract retains the full "where + how" detail. Estimated savings: 3-5KB per module.

### 8. Per-rule firing telemetry

Add stable IDs to writer-prompt rules. **Use gemini's design: ONE ID per FAILURE CLASS, not per rule statement.** Examples:

| Failure class | ID | Rules that contribute |
|---|---|---|
| Meta-narration leak | `#R-VOICE-META` | All forbidden phrase rules + abstract voice anchors |
| Italic bad-form leak | `#R-BAD-FORM-MARKER` | bad-form scan rule + examples + FORBIDDEN PATTERNS enum |
| VESUM all-words coverage | `#R-VESUM-ALL-WORDS` | verify_words coverage requirement + L2-trap -ся enum |
| Implementation-map silent-omission | `#R-IMPL-MAP-COMPLETE` | implementation_map_audit + HARD REJECT framing |
| Textbook 30-word floor | `#R-TEXTBOOK-30W` | mandatory word-count self-check rule |
| Citation honesty | `#R-CITE-HONEST` | source-citation discipline + Сибір case study + verify_source_attribution mandate |

Tag each rule in the prompt with `<!-- rule_id: #R-XXX -->` HTML comments (invisible in prompt rendering, parseable by telemetry).

In `scripts/build/linear_pipeline.py`, extend gate failure reporting to include `rule_id` when a known failure class fires. Specifically the gates that map to these IDs:
- `russianisms_strict` / `vesum_verified` → `#R-BAD-FORM-MARKER`, `#R-VESUM-ALL-WORDS`
- `engagement_floor` voice patterns → `#R-VOICE-META`
- `implementation_map_missing` → `#R-IMPL-MAP-COMPLETE`
- `textbook_grounding.long_blockquotes_checked` → `#R-TEXTBOOK-30W`
- `citations_resolve` / `tool_theatre` → `#R-CITE-HONEST`

Emit `writer_rule_fired` JSONL events from the pipeline when a gate fires for a known class. Example event:
```json
{"event": "writer_rule_fired", "rule_id": "#R-VOICE-META", "level": "a1", "slug": "my-morning", "gate": "engagement_floor", "evidence": "Welcome to..."}
```

This data feeds future strip cycles (PR-G + beyond).

### 9. Add size enforcer

**File:** `scripts/audit/check_writer_prompt_size.py` (NEW)

```python
"""Enforce writer prompt size ceiling.

Per architectural reset 2026-05-23 (docs/session-state/2026-05-23-architectural-reset-strip-v7-llm-demote.md
decision row C), strip cycle PR-C 2026-05-23): rendered writer prompt must
stay under WRITER_PROMPT_CEILING_BYTES for ALL level/module fixtures.

Empirical baseline (post-PR-C):
- a1/my-morning rendered: ~120KB target, 130KB ceiling (10KB headroom for
  manifest variance across modules)
- Below 120KB requires per-module data restructure (PR-D scope: knowledge-packet
  diet, manifest compression)

If a module's rendered prompt exceeds the ceiling, fail the build (CI) so the
strip cycle doesn't regress silently.
"""

from __future__ import annotations

from pathlib import Path

import pytest

WRITER_PROMPT_CEILING_BYTES = 130 * 1024  # 130KB
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Fixture modules to enforce against. Add more as the strip proves out on each
# level. Start with the A1 anchor and one B1 module (variance check).
FIXTURE_MODULES = [
    ("a1", "my-morning"),
]


@pytest.mark.parametrize("level,slug", FIXTURE_MODULES)
def test_writer_prompt_rendered_size_under_ceiling(level: str, slug: str) -> None:
    prompt_path = (
        PROJECT_ROOT
        / "curriculum"
        / "l2-uk-en"
        / level
        / slug
        / "writer_prompt.md"
    )
    if not prompt_path.exists():
        pytest.skip(f"No rendered prompt at {prompt_path} — render first via v7_build.py")
    size = prompt_path.stat().st_size
    assert size <= WRITER_PROMPT_CEILING_BYTES, (
        f"{level}/{slug} writer_prompt.md is {size} bytes, over the "
        f"{WRITER_PROMPT_CEILING_BYTES}-byte ceiling. Strip more or escalate "
        f"to per-module data restructure (PR-D scope)."
    )
```

### 10. Tests

**File:** `tests/test_writer_prompt_size.py` (NEW)

```python
"""Tests for writer-prompt-size enforcer (PR-C 2026-05-23)."""

from pathlib import Path

import pytest

from scripts.audit.check_writer_prompt_size import (
    WRITER_PROMPT_CEILING_BYTES,
    FIXTURE_MODULES,
)


def test_ceiling_is_130kb():
    """Per PR-C 2026-05-23, ceiling is 130KB (120KB target + 10KB headroom)."""
    assert WRITER_PROMPT_CEILING_BYTES == 130 * 1024


def test_fixture_modules_includes_a1_my_morning():
    """The A1 anchor module is the canonical fixture."""
    assert ("a1", "my-morning") in FIXTURE_MODULES


@pytest.mark.parametrize("level,slug", FIXTURE_MODULES)
def test_fixture_module_path_resolves(level: str, slug: str):
    project_root = Path(__file__).resolve().parents[1]
    expected = project_root / "curriculum" / "l2-uk-en" / level / slug
    assert expected.exists(), f"Fixture path {expected} should exist"
```

Add a telemetry test for the new `writer_rule_fired` event:

**File:** `tests/test_linear_pipeline_telemetry.py` — add:

```python
def test_writer_rule_fired_event_emitted_on_known_failure_class():
    """Per PR-C 2026-05-23: gates that map to a known rule ID emit
    writer_rule_fired telemetry events with the ID."""
    # Use existing test fixtures: trigger an engagement_floor failure with
    # a "Welcome to..." phrase; verify the emitted event includes
    # rule_id="#R-VOICE-META".
    # (Adapt to the project's existing event_sink test pattern.)
    ...
```

### 11. Render the prompt + measure size

```bash
# venv symlinked
.venv/bin/python scripts/build/v7_build.py a1 my-morning --no-resume --dry-run-prompt --out /tmp/pr-c-render 2>&1 | tail -10
wc -c /tmp/pr-c-render/writer_prompt.md
```

If `--dry-run-prompt` flag doesn't exist (check `--help`), render via a minimal Python script that calls `render_writer_prompt` directly with the existing a1/my-morning plan.

Verify the rendered size is between 100KB and 130KB. If above 130KB: strip more. If below 100KB: you may have cut load-bearing content — re-check the codex/gemini KEEP lists.

### 12. Tests + lint

```bash
# venv symlinked
.venv/bin/python -m pytest tests/test_writer_prompt_size.py tests/test_linear_pipeline_telemetry.py -v
.venv/bin/python -m pytest tests/ --timeout=120 -q 2>&1 | tail -30
.venv/bin/ruff check scripts/build/phases/linear-write.md scripts/audit/check_writer_prompt_size.py tests/test_writer_prompt_size.py
```

Note: `.md` files are not Python; ruff check on `linear-write.md` will skip (that's expected — included for completeness).

### 13. Commit + push + PR

```bash
git add scripts/build/phases/linear-write.md scripts/audit/check_writer_prompt_size.py tests/test_writer_prompt_size.py tests/test_linear_pipeline_telemetry.py docs/best-practices/writer-prompt-appendix.md docs/north-star.md docs/lesson-contract.md scripts/build/linear_pipeline.py
# (adjust file list based on which were actually edited)

git commit -m "$(cat <<'EOF'
feat(writer-prompt): strip + fix PR-B stale constants + per-rule firing telemetry (PR-C)

Strip cycle 1: reduce rendered writer prompt from ~194KB → ~120KB on A1.
Target informed by codex empirical estimate (115-140KB rendered for A1
reliability per cross-model review msg #1076). 80KB-rendered ambition
was unreachable without per-module data restructure (PR-D scope).

Changes:

1. Stale-constant bugs from PR-B (CRITICAL):
   - Line 18: ±5% → 8% lower-band tolerance reference
   - Line ~578: callout_min 2 → 1

2. Dedup {KNOWLEDGE_PACKET} (was rendered twice). -13KB rendered.

3. LESSON_CONTRACT §3 Component inventory → appendix doc
   docs/best-practices/writer-prompt-appendix.md. Authoring-field
   substitutions ({ALLOWED_ACTIVITY_TYPES}, {INLINE_ALLOWED_TYPES},
   {WORKBOOK_ALLOWED_TYPES}, {COMPONENT_PROPS_SCHEMA}) STAY INLINE per
   codex review carve-out. -11KB rendered.

4. NORTH_STAR philosophy → 5KB Writer Charter, keeping verbatim:
   - Adult peer voice anchor
   - B1+ no English outside Tab 2 anchor
   - Source grounding / no ghost authority anchor
   - Decolonized framing anchor
   - Activities test language not trivia anchor
   - Forbidden meta-prose list (#1 A1 regression source per gemini review)
   -10KB rendered.

5. Drop pre-emit <bad_form_audit> + <activity_split_audit> visible lines.
   Scan rules + examples + FORBIDDEN PATTERNS enum STAY (load-bearing
   for vesum_verified gate per codex review). Deterministic gates catch
   the same failures post-emission. -2KB rendered.

6. Compress phonetic_rules manifest entries (move IPA formatting prose
   to single PHONETIC_REFERENCE block). -3-5KB per module.

7. Compress Wiki Obligations Manifest entries (raw ID + 1-sentence
   summary; "How" lives in IMPLEMENTATION_MAP_CONTRACT). -3-5KB per
   module.

8. Per-rule firing telemetry (gemini design: ONE ID per failure class):
   - #R-VOICE-META (engagement_floor voice patterns)
   - #R-BAD-FORM-MARKER (russianisms / vesum bad-form leaks)
   - #R-VESUM-ALL-WORDS (vesum coverage)
   - #R-IMPL-MAP-COMPLETE (implementation_map_missing)
   - #R-TEXTBOOK-30W (textbook blockquote floor)
   - #R-CITE-HONEST (citation honesty)
   Emit writer_rule_fired JSONL events on gate firings. Data feeds PR-G
   per-dim agreement analysis after 20-30 promotes.

9. New enforcer: scripts/audit/check_writer_prompt_size.py — pytest
   fixture fails CI if rendered prompt exceeds 130KB ceiling (10KB
   headroom over 120KB target).

Cross-model reviews:
- Codex (gpt-5.5) msg #1076 verdict REVISE: surfaced the stale-constant
  bugs and the inline-required substitutions; 80KB unreachable
- Gemini (gemini-3-flash-preview) msg #1075 verdict SHIP: surfaced the
  manifest-compression opportunities and the failure-class telemetry
  design

Per architectural reset 2026-05-23
(docs/session-state/2026-05-23-architectural-reset-strip-v7-llm-demote.md
decision row C).

Co-Authored-By: Codex CLI <noreply@anthropic.com>
EOF
)"

git push -u origin HEAD
gh pr create --title "feat(writer-prompt): strip + fix PR-B stale constants + per-rule firing telemetry (PR-C)" --body "..."
```

Use the commit message body for the PR description.

### 14. Do NOT auto-merge

Surface PR URL. Orchestrator reviews + merges after CI confirms ceiling enforcer passes.

## Acceptance criteria

- All steps completed
- Rendered prompt size for a1/my-morning is 100-130KB (verified via wc -c)
- 6 critical KEEP items preserved (per codex+gemini reviews — see context section above)
- Telemetry events tagged with rule IDs
- Tests pass + ruff clean
- PR URL surfaced

## Stay in scope

DO NOT modify any file outside:
- `scripts/build/phases/linear-write.md` (or its template-substitution sources `docs/north-star.md` / `docs/lesson-contract.md`)
- `scripts/build/linear_pipeline.py` (for telemetry rule_id emissions only)
- `scripts/audit/check_writer_prompt_size.py` (new)
- `tests/test_writer_prompt_size.py` (new)
- `tests/test_linear_pipeline_telemetry.py` (extend only the writer_rule_fired test)
- `docs/best-practices/writer-prompt-appendix.md` (new)
- `scripts/wiki/` for phonetic_rules manifest compression (limited scope)

If something else seems broken: mention in PR body as a follow-up. Do NOT touch.

## Failure recovery

- If rendered size lands above 130KB: don't fudge. Strip more from the per-section budgets in linear-write.md (Module Context, Plan, Contract YAML are tighter targets) or escalate to PR-C2 with a specific cut list.
- If the size enforcer rejects on a module other than a1/my-morning: that's expected if WIKI_MANIFEST varies wildly. Add the failing module's slug to FIXTURE_MODULES and tighten the strip there.
- If `--dry-run-prompt` flag doesn't exist: build the prompt via a Python one-liner using `scripts.build.linear_pipeline.render_writer_prompt` directly. Don't fire a full v7_build to measure size.
- If codex CLI stalls again (PR-A pattern): salvage inline rather than re-dispatch. The brief is unambiguous enough that orchestrator can finish the steps if codex hangs.

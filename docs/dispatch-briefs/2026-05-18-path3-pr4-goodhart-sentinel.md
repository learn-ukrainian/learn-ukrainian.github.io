# Dispatch brief — Path 3 PR4: Goodhart sentinel for wiki_coverage_review

**Agent:** Codex gpt-5.5 xhigh
**Mode:** danger (commits + PR open; NO auto-merge)
**Worktree:** required (per #1952, enforced by `delegate.py dispatch`)
**Scope:** PR4 of 4 in Path 3 architecture per
`docs/decisions/2026-05-17-path3-per-obligation-review-loop.md` lines 82-92.
Refine the EXISTING `scripts/build/phases/linear-review-wiki-coverage.md`
prompt to act as the Phase 5 Goodhart sentinel — judging "is each
obligation WOVEN into substantive prose, or just KEYWORD-STUFFED to pass
the deterministic gate?" — and tighten `_run_wiki_coverage_review` in
`v7_build.py` to surface substance-missing failures with explicit
signal. Do NOT add a new pipeline phase; the wiki_coverage_review
phase already exists at v7_build.py:808-826 (cross-family Gemini
reviewer when writer is Claude). PR4 sharpens its rubric, not its
plumbing.

**Prerequisite:** PR3 must be merged. PR3 closes the deterministic gate
loop; PR4 is the semantic safety net AFTER PR3's correction passes
push coverage_pct ≥ threshold.

---

## Why

Decision Card lines 82-84:

> ### Phase 5 — Goodhart sentinel (Gemini + Grok merge)
>
> After Phase 3+4 converge on the deterministic gate, run a **secondary
> semantic reviewer** (cross-family — Codex if writer was Claude, etc.)
> that judges "is this obligation woven into the prose, or just
> keyword-stuffed?" If the gate passes but the semantic reviewer flags
> "substance missing," fail the build with explicit signal.

Today (post-PR3), the wiki_coverage_review prompt at
`scripts/build/phases/linear-review-wiki-coverage.md` checks "semantic
adequacy" but the rubric is permissive — PARTIAL verdicts are explicitly
called "a soft signal unless the pattern shows systematic
under-teaching" (line 58). After PR3 the correction loop will push
coverage_pct to PASS-threshold via surgical `<fixes>` edits. Those
surgical edits create exactly the Goodhart-shaped risk Decision Card
risk #3 names: the deterministic gate passes because the right strings
appear in the right artifacts, but the writer's prose may have devolved
into keyword stuffing.

PR4 makes the semantic reviewer the explicit Goodhart sentinel:
- KEYWORD_STUFFING verdict (NEW) fires when an obligation's substance
  is a bare mention without integrated explanation, dialogue use, or
  contextual scaffolding.
- Each verdict requires a verbatim quote from the cited artifact (the
  prompt already requires this; PR4 enforces the schema).
- The build aborts with `LinearPipelineError("Wiki coverage Goodhart
  sentinel failed")` when ANY verdict is `KEYWORD_STUFFING` OR when
  `overall_verdict == FAIL`.

---

## What you build

### 1. Refine `scripts/build/phases/linear-review-wiki-coverage.md`

Edit the existing template. KEEP all current variable placeholders
(`{LEVEL}`, `{MODULE_NUM}`, `{MODULE_SLUG}`, `{WORD_TARGET}`,
`{WIKI_MANIFEST}`, `{WIKI_COVERAGE_GATE}`, `{PLAN_CONTENT}`,
`{GENERATED_CONTENT}`).

Tighten the rubric in three places:

#### 1a. Add KEYWORD_STUFFING verdict

Replace the existing PASS/PARTIAL/FAIL enum (line 22-25 of the current
template) with:

```
4. Emit one verdict:
   - PASS: the cited evidence implements the obligation as substantive
     pedagogy — the manifest claim is woven into prose/dialogue/activity
     with explanation, example use, or integrated context.
   - KEYWORD_STUFFING: the cited evidence contains the required string
     verbatim but the surrounding prose does not actually teach,
     contrast, or apply it. Example failure: a contrast_pair where the
     "incorrect" and "correct" forms appear in a list with no learner
     activity around them; a phonetic_rule where the written→spoken
     mapping is named in a one-sentence aside with no example pair; a
     sequence_step where the section heading exists but the body skips
     to the next step. THIS VERDICT FAILS THE BUILD.
   - PARTIAL: evidence exists and shows some pedagogy, but is thin
     enough that the obligation is taught at a shallower level than the
     manifest target. Soft signal.
   - FAIL: missing, contradicted, or not in the claimed location.
```

#### 1b. Strengthen the treatment-specific checks

Replace lines 27-38 of the current template with a tighter rubric.
Each treatment now has a positive-substance check AND a
keyword-stuffing antipattern:

```
Treatment-specific checks:

- `contrast_pair`:
  * PASS: both forms appear in an activity body AND the learner must
    distinguish them (multiple-choice, fill-in, correction exercise).
  * KEYWORD_STUFFING: both forms appear in a static list without an
    activity that requires distinguishing them; or both forms appear in
    a single example sentence with no learner-facing task.
- `prose_explanation`:
  * PASS: module.md prose names the manifest's `incorrect` and
    `correct` strings AND explains why one is preferred, with at least
    one substantive sentence of explanation beyond the bare contrast.
  * KEYWORD_STUFFING: the strings appear in a list/table/footnote
    without explanation prose; or the explanation is a generic "this is
    correct" without engaging the manifest's `why` field.
- `explicit_explanation` (phonetic):
  * PASS: learner-facing pronunciation guidance with at least one
    written→spoken example pair AND a brief contextual note (when does
    this rule apply, common confusable, etc.).
  * KEYWORD_STUFFING: a one-line "smooth speech" or "soft pronunciation"
    reminder without the actual rule mapping; or the rule is stated but
    no example pair is provided.
- `sequence_step`:
  * PASS: the module prose teaches the step's canonical pedagogical
    claim in the appropriate order, with the heading or marker AND
    body text that advances the learner toward the step's goal.
  * KEYWORD_STUFFING: the heading exists but the body skips ahead
    without teaching the step; or the step is named in a metadiscourse
    sentence ("we will now learn X") without actually teaching X.
- `decolonization_ban`:
  * PASS: the generated content avoids the banned framing AND, if the
    contrast is naturally adjacent (e.g. "Kyiv not Kiev"), offers a
    Ukrainian-centered framing.
  * KEYWORD_STUFFING: the banned framing is technically absent but a
    near-paraphrase remains; or a meta-disclaimer about avoiding the
    ban replaces the substance of the lesson.
```

#### 1c. Enforce evidence quoting in the schema

The current JSON response shape (line 41-54) already requires
`evidence: "verbatim excerpt from the cited artifact location"`. Add
a sentence above the JSON block making this load-bearing:

```
Evidence MUST be a verbatim quote from the cited artifact location
(quote-marked). Paraphrase or summary evidence is invalid and forces
KEYWORD_STUFFING. Quotes must be at least 8 words long unless the
obligation is a single short word/phrase the manifest specifies — in
which case quote the full surrounding sentence containing it.

The new verdict enum: `PASS | KEYWORD_STUFFING | PARTIAL | FAIL`.
`overall_verdict` must be `FAIL` if any obligation verdict is `FAIL` OR
`KEYWORD_STUFFING`. `PARTIAL` is a soft signal — system aggregates,
build continues, but logs the pattern.
```

Update the example JSON in the prompt accordingly.

### 2. Update `parse_wiki_coverage_review_response` in `linear_pipeline.py`

Today (linear_pipeline.py:3389-3406) accepts `{PASS, PARTIAL, FAIL}`.
Extend to `{PASS, KEYWORD_STUFFING, PARTIAL, FAIL}`:

```python
ALLOWED_WIKI_COVERAGE_VERDICTS = {"PASS", "KEYWORD_STUFFING", "PARTIAL", "FAIL"}
WIKI_COVERAGE_OVERALL_FAIL_VERDICTS = {"FAIL", "KEYWORD_STUFFING"}
```

In the verdicts loop, accept the new value. In the overall_verdict
check, add: if any per-obligation `verdict in
WIKI_COVERAGE_OVERALL_FAIL_VERDICTS` then `overall_verdict` must be
`FAIL` (parser-side invariant — if model says all PASS but one
KEYWORD_STUFFING, the overall MUST be FAIL).

Add a new schema check: every `evidence` field must contain a quote
marker (`"`, `“`, `«`) AND be at least 8 characters long. Raise
`LinearPipelineError("Wiki coverage review evidence must be a quoted excerpt of ≥8 chars")` on violation.

### 3. v7_build.py wiring (minimal)

`_run_wiki_coverage_review` (lines 489-525) calls
`parse_wiki_coverage_review_response`. After this PR's parser update,
the FAIL on KEYWORD_STUFFING is automatic at the parser level
(invariant raise) AND at the caller level (line 825-826
`if wiki_coverage_review["overall_verdict"] == "FAIL": raise`).

Add ONE telemetry event in v7_build.py around line 824:

```python
# Phase 5 Goodhart sentinel telemetry (PR4)
stuffing_count = sum(
    1 for v in wiki_coverage_review.get("verdicts", [])
    if str(v.get("verdict", "")).upper() == "KEYWORD_STUFFING"
)
partial_count = sum(
    1 for v in wiki_coverage_review.get("verdicts", [])
    if str(v.get("verdict", "")).upper() == "PARTIAL"
)
tracker.emit(
    "wiki_coverage_goodhart_sentinel",
    level=level,
    slug=slug,
    overall_verdict=wiki_coverage_review["overall_verdict"],
    keyword_stuffing_count=stuffing_count,
    partial_count=partial_count,
    total_verdicts=len(wiki_coverage_review.get("verdicts", [])),
)
```

### 4. Tests

Add `tests/build/test_wiki_coverage_goodhart_sentinel.py`. Minimum 10
cases:

1. **PASS-only verdicts → overall PASS**: 5 obligations all PASS,
   overall PASS, parser accepts.
2. **One KEYWORD_STUFFING → overall must be FAIL**: parser raises if
   overall doesn't match.
3. **PARTIAL-only → soft signal, overall PASS allowed**: parser accepts
   any number of PARTIAL with overall PASS or PARTIAL.
4. **One FAIL → overall must be FAIL**: parser raises if mismatched.
5. **Evidence missing quote markers → parser raises**: e.g.
   `evidence: "just plain text no quote chars"` → fail.
6. **Evidence shorter than 8 chars → parser raises**.
7. **Curly quotes accepted**: evidence containing `"..."` or `«...»`
   passes the quote-marker check.
8. **v7_build telemetry emit**: simulate a wiki_coverage_review result
   with mixed verdicts → assert `wiki_coverage_goodhart_sentinel`
   event payload has correct counts.
9. **Build raises on KEYWORD_STUFFING overall=FAIL**: end-to-end
   simulation of v7_build's wiki_coverage_review phase with the new
   verdict → assert `LinearPipelineError("Wiki coverage review failed")`.
10. **Prompt template renders KEYWORD_STUFFING in instructions**:
    assert `render_wiki_coverage_review_prompt(...)` output contains
    the substring `"KEYWORD_STUFFING"` (regression guard against the
    template losing the new verdict).

Update any existing wiki_coverage_review tests that assume only 3
verdicts — extend their expected enums.

---

## Verifiable claims (per #M-4)

| Claim | Tool + raw output |
|---|---|
| Prompt template updated | `git diff origin/main -- scripts/build/phases/linear-review-wiki-coverage.md` showing the rubric expansion |
| Parser extended | `git diff origin/main -- scripts/build/linear_pipeline.py` showing the new verdict enum + evidence quote check |
| v7_build telemetry added | `git diff origin/main -- scripts/build/v7_build.py` showing the new emit |
| New tests pass | `.venv/bin/pytest tests/build/test_wiki_coverage_goodhart_sentinel.py -v` final summary raw |
| Existing wiki_coverage_review tests still pass | `.venv/bin/pytest tests/ -q -k wiki_coverage` final summary raw |
| Full audit + build green | `.venv/bin/pytest tests/audit/ tests/build/ -q` final summary raw (NO `-x`) |
| Ruff clean | `.venv/bin/ruff check scripts/build/linear_pipeline.py scripts/build/v7_build.py tests/build/test_wiki_coverage_goodhart_sentinel.py` raw |
| Pre-commit clean | `.venv/bin/python -m pre_commit run --files <changed>` raw |
| Commit + PR | `git log -1 --oneline` + `gh pr view --json url` raw |

**No claim allowed without its raw output line.** Per #M-4.

---

## Worktree setup

Branch: `feat/path3-pr4-goodhart-sentinel`. Path:
`.worktrees/dispatch/codex/path3-pr4-goodhart-sentinel-<timestamp>/`.

## Verification (must run all BEFORE pushing)

```bash
# venv symlinked from main; run from worktree root
.venv/bin/pytest tests/build/test_wiki_coverage_goodhart_sentinel.py -v
.venv/bin/pytest tests/ -q -k wiki_coverage
.venv/bin/pytest tests/audit/ tests/build/ -q
.venv/bin/ruff check scripts/build/linear_pipeline.py scripts/build/v7_build.py tests/build/test_wiki_coverage_goodhart_sentinel.py
.venv/bin/python -m pre_commit run --files scripts/build/phases/linear-review-wiki-coverage.md scripts/build/linear_pipeline.py scripts/build/v7_build.py tests/build/test_wiki_coverage_goodhart_sentinel.py
git diff --stat origin/main
```

## Commit + PR

Conventional commit. Title: `feat(build): Path 3 PR4 — Goodhart
sentinel on wiki_coverage_review (KEYWORD_STUFFING verdict)`. Body
covers the rubric change, the parser invariant, the telemetry event,
and quotes the verifiable-claims raw outputs.

NO `--auto-merge`.

## Out of scope

* Don't replace the wiki_coverage_review phase wholesale — refine its
  prompt + parser only.
* Don't change the reviewer's cross-family routing (Gemini reviews
  Claude-written modules, etc. — `_reviewer_for_writer` stays as is).
* Don't add new pipeline phases. v7_build's phase ordering stays:
  writer → python_qg → wiki_coverage_gate (now with PR3 corrections)
  → wiki_coverage_review (now Goodhart-strict per this PR) → llm_qg → mdx.
* Don't modify PR3's correction loop or PR2's gate output.

## Anti-fabrication

If `parse_wiki_coverage_review_response` shape differs from what's
described (e.g. it accepts a 5-verdict enum already, or it doesn't
validate evidence quote markers), STOP and quote the surprise verbatim
before patching.

If a test feels redundant, name the specific test and the specific
blocker.

## Notes for orchestrator (Claude, not Codex)

* PRECONDITION: PR3 must be merged before firing this brief. If
  PR3 is still open, hold this brief and check back.
* Dispatch CAP usage at fire time: depends on state when PR3 lands.
  PR4 is mechanically simpler than PR3; estimated 15-25 min.
* On finalize: verify the 9 verifiable-claims raw outputs are quoted
  in PR body, check CI rollup, merge if green, delete worktree.
* AFTER PR4 lands: fire m20 v7_build via Monitor tool. The
  build IS the proof of the architecture working.

# Dispatch brief — PR #2266 adjustment (split + content fixes + plumbing audit)

**Agent**: codex
**Mode**: danger (commits + push + PR)
**Effort**: high
**Worktree**: yes (default for `--mode danger`)
**Branch base**: `main` (`0014318188`)
**Source branch**: `codex/6877-b1-adjectives-comparative-e2e` (the existing PR #2266 branch — checked out at `/Users/krisztiankoos/.codex/worktrees/6877/learn-ukrainian/`)

---

## Why this brief exists

PR #2266 (feat(b1): publish adjectives comparative module) jammed three concerns into one PR:

1. **Content** — 2 starlight/* files (the B1 module MDX + landing card unlock).
2. **Pipeline plumbing** — 9 scripts/* files touching the writer prompt, reviewer prompts, `v7_build.py`, `wiki_coverage_gate.py`, `citation_matcher.py`, `activity_renderer.py`, `yaml_activities.py`, `tool_calls.py`.
3. **Tests** — 7 test files covering both concerns.

The user requested adjustment across all three categories: split the PR, fix content quality issues, and audit a specific plumbing bug. This brief is self-contained per AGENTS.md §pre-submit and MEMORY.md #M-4 (deterministic over hallucination).

---

## Verifiable-claims preamble (#M-4)

Every claim below was verified against the actual diff in the codex worktree at `/Users/krisztiankoos/.codex/worktrees/6877/learn-ukrainian/`. File paths + line numbers are real. Before doing any edit, codex MUST re-read each cited file/line to confirm. If a cited line has shifted, find the equivalent and report the shift in the PR body.

---

## Numbered steps (per `docs/best-practices/gitflow.md` + AGENTS.md §11-26)

### Step 1 — Split decision: PR-A (plumbing) and PR-B (content)

Open **TWO new PRs**, both branching off `main` at the same SHA as #2266's base (`0014318188`):

- **PR-A — plumbing + tests** (merges first, ungates PR-B):
  - All 9 `scripts/*` files from PR #2266's file list (see `gh pr view 2266 --json files`).
  - All 7 `tests/*` files from PR #2266's file list.
  - Title: `fix(v7): pre-emit audit tightening + reviewer-override + citation page-range + wiki_coverage compact-pipe parse`
- **PR-B — B1 module content** (depends on PR-A — wait for PR-A to merge first):
  - `starlight/src/content/docs/b1/adjectives-comparative.mdx` (with content fixes from Step 3 applied)
  - `starlight/src/content/docs/b1/index.mdx` (landing card unlock)
  - Title: `feat(b1): publish adjectives comparative module`

Sequence:
1. `git worktree add` two new branches off `main`.
2. Cherry-pick or copy the plumbing files to branch A, the content files to branch B.
3. Open PR-A first. Wait for blocking CI green.
4. Once PR-A merges, rebase PR-B onto new main, open PR-B with the content fixes from Step 3 applied.
5. **Close PR #2266 with a comment linking PR-A + PR-B as the replacement.** Do not merge #2266.

---

### Step 2 — Plumbing audit (PR-A scope)

Two specific concerns to investigate + resolve before opening PR-A:

#### 2a. `scripts/audit/wiki_coverage_gate.py` — hardcoded keyword bypass

The diff at line 567 adds a special case:

```python
location_cf in {"activities.yaml", "all", "any", "(any)", "(any activity)"} or (
    "workbook" in location_cf and "error-correction" in location_cf
)
```

**Question for codex to answer in the PR-A body:**

- Is this special case generalizable? Is there a reason workbook + error-correction specifically needs flat-fallback but other workbook+activity-type pairs do not?
- If yes (real contract): generalize — `location_cf` matching `r"^workbook\b.*\b(error-correction|fill-in|multiple-choice|...)"` → flat-fallback for ALL workbook-aggregate references, not just error-correction.
- If no (one-off for adjective-comparative): document why in a code comment AND add a regression test (`tests/audit/test_wiki_coverage_gate.py`) that pins the behavior so future writers don't regress.

Pick ONE path. State the chosen path in PR-A body with a 2-sentence rationale.

#### 2b. `scripts/build/phases/linear-write.md` — new mandatory audit lines

The diff adds two new mandatory pre-emit audit lines to the writer contract:

```
2. <bad_form_audit>italic_bad_form_patterns_found=N converted_to_marker=N remaining=0</bad_form_audit>
3. <activity_split_audit>level={LEVEL} inline_n=N workbook_n=N inline_range=[lo,hi] workbook_range=[lo,hi] split_valid=true|false</activity_split_audit>
```

This is a CONTRACT change affecting ALL writer families, not just codex-tools.

**Required action in PR-A:**

- Verify each writer family can emit these lines under its default model+effort:
  - `claude-tools` (claude-opus-4-7 xhigh) — NOT TESTED in this PR. Add a smoke test or document risk.
  - `codex-tools` (gpt-5.5 xhigh) — VALIDATED by PR #2266's empirical run.
  - `gemini-tools` (gemini-3.1-pro-preview high) — last-known passing 2026-05-21; verify the new audit lines work.
  - `deepseek-tools` (deepseek-v4-pro medium) — proven 2026-05-21; verify.
  - `grok-tools` (grok-4.3 medium) — under-target word count per #2039; out-of-scope to verify but flag risk.
- Add a parser-side regression test in `tests/test_v7_build_reviewer_assert.py` or a new file that:
  - Asserts `_writer_preemit_audit_context()` extracts all three audit tags correctly.
  - Asserts the function handles missing tags gracefully (returns empty string, does not crash).
  - Asserts the function handles malformed tags (no panic, no false-positive match).

#### 2c. `scripts/build/citation_matcher.py` — page-range support

The diff adds `page_end: int | None` to `CitationKey` and `citation_keys_match` now uses range bounds.

**Required edge-case tests** in `tests/test_citation_matcher.py`:

- `p.124-125` → `page=124, page_end=125` ✓
- `p.124-` (trailing hyphen, no end) → reject (currently goes via the second branch — verify)
- `p.124-125-127` (multi-hyphen, malformed) → first match wins? Or reject? Pick one and pin.
- `p.125-124` (reversed range) → currently returns `None` per the check `if page_end is not None and page_end < page`. Test this.
- `сторінка 124-125` (Ukrainian page word) → should work via the existing Ukrainian alternation.

State which behavior is intended for each in the PR-A body.

---

### Step 3 — Content fixes (PR-B scope)

Apply these fixes to `starlight/src/content/docs/b1/adjectives-comparative.mdx` **before** opening PR-B. These are not stylistic preferences; they are content-quality regressions that block promotion under the V7 verify-before-promote 10-check list (`docs/best-practices/v7-design-and-corpus.md` §4).

#### 3a. CRITICAL — Strip pipeline metadata from Tab 4 (Ресурси)

**Lines 593-603** currently read (verbatim — verify in `git show codex/6877-b1-adjectives-comparative-e2e:starlight/src/content/docs/b1/adjectives-comparative.mdx | sed -n '593,603p'`):

```
- 📚 **Litvinova Grade 6, p.198**
  Планове джерело: проста і складена форма; у плані chunk_id не подано, writer telemetry retrieved chunk_id: 6-klas-ukrmova-litvinova-2023_s0205.
- 📚 **Авраменко Grade 11, p.29**
  Планове джерело: стилістичне зауваження про жартівливі рекламні форми; у плані chunk_id не подано, writer telemetry retrieved chunk_id: 11-klas-ukrajinska-mova-avramenko-2019_s0041.
```

(repeated for all 6 sources)

**This is pipeline metadata leaking into learner-facing prose.** A B1 student does not need to read "writer telemetry" or "chunk_id". This is a content-quality regression. Replace each bullet with a clean Ukrainian-only description:

```
- 📚 **Litvinova Grade 6, p.198**
  Проста і складена форма вищого ступеня з прикладами тренувальних вправ.
- 📚 **Авраменко Grade 11, p.29**
  Стилістичне зауваження про жартівливі рекламні форми (приклад {/**/}найкрабовіші{/**/}).
```

(rewrite all 6; chunk_id and "writer telemetry" must NOT appear in any user-visible MDX file)

**Root cause investigation (do NOT fix here, but file a follow-up):**

This metadata leak indicates the MDX assembler or writer prompt is templating "writer telemetry retrieved chunk_id: ..." into Ресурси-tab output. **File a new GH issue** titled `mdx-assembler: writer telemetry / chunk_id strings leaking into Ресурси tab` referencing this PR; tag `bug area:pipeline`. The fix belongs in the assembler or in a Tab-4 sanitizer pass, not in per-module content rewrites.

#### 3b. Remove unrelated raw textbook chunks dumped into Tab 1 prose

**Line 282** (verify with `sed -n '282p'`):

> Прочитайте речення й виконайте завдання. Наші палички {/**/}найкрабовіші{/**/}! Українка Христина Стуй найпершою подолала стометрівку. Чи свідомо автори реклами утворили найвищий ступінь порівняння від відносного прикметника крабовий?

This raw-quotes a school-exercise instruction. Keep the linguistic point about "найкрабовіші" (already covered well in lines 279-289) but DELETE this stray blockquote — it's a textbook exercise instruction, not narrative content.

**Lines 300-302**:

> Спишіть речення, підкресліть прислівники як члени речення. Надпишіть над кожним прислівником розряд за значенням. Йде сон на озерне плесо, я мовчки іду за ним. Жила я на вуличці, котра ішла все вгору, і вгору, і вгору.

These are TWO unrelated quotes from different sources spliced together (a grammar exercise + a literary fragment about a street). DELETE both. The proverbs section (lines 295-310) should stand on its own with the proverb examples already in the table on lines 304-308.

**Line 302** also contains:

> У багатьох випадках написання не з прикметником і прислівником залежить від змісту речення. Якщо часткою не щось заперечуємо, то її пишемо окремо. Порівняймо: цей будинок не старий; цей будинок нестарий; краще недосолити, ніж пересолити.

This is about `не` (negation particle), NOT about comparative adjectives. Off-topic for this module. DELETE.

**Net effect**: Lines 280-303 collapse to clean proverbs-as-models section.

#### 3c. Consider DialogueBox for the 2 dialogues

Lines 151-161 (Орендар/Друг dialogue about Kyiv apartments) and lines 411-422 (Покупець/Продавець dialogue about a backpack) are rendered as `>` blockquotes with `Спікер:` prefixes. Per V7 design SSOT this is acceptable but `<DialogueBox>` is the stronger pedagogical container.

**Optional improvement** — convert both to `<DialogueBox>` components if straightforward. Skip if it requires importing new schema. State which path was taken.

#### 3d. Quick VESUM spot-check (#M-4 deterministic)

The orchestrator did not run a full VESUM sweep on this PR. PR-B body MUST include the result of:

```
.venv/bin/python -c "
from scripts.audit.check_russicisms import check_text
with open('starlight/src/content/docs/b1/adjectives-comparative.mdx') as f:
    text = f.read()
print(check_text(text))
"
```

If the russianisms check returns ANY hits, address each one in the PR-B body (false positive vs real fix) before merging. Do NOT silently merge with russianism hits.

---

### Step 4 — Verification (per AGENTS.md §pre-submit)

Both PRs MUST include in their bodies (raw command + cwd + raw output, per #M-4):

```
.venv/bin/ruff check scripts tests
.venv/bin/python -m pytest tests/ -q --no-header
cd starlight && npm run build
.venv/bin/python scripts/audit/lint_agent_trailer.py
```

PR-A scope must verify pytest specifically passes:
- `tests/test_v7_build_reviewer_assert.py`
- `tests/test_citation_matcher.py`
- `tests/audit/test_wiki_coverage_gate.py`
- `tests/test_yaml_activities_v7_types.py`
- `tests/test_activity_renderer.py`
- `tests/test_prompt_cot_tier1_scaffolding.py`
- `tests/test_runner_tool_calls.py`

PR-B scope must verify:
- `npm run build` in `starlight/` produces a valid `/b1/adjectives-comparative/` page.
- The Tab 4 metadata leak is gone (`grep -c "chunk_id\|writer telemetry" starlight/src/content/docs/b1/adjectives-comparative.mdx` returns `0`).

---

### Step 5 — Conventional commits

PR-A:
```
fix(v7): pre-emit audit tightening + reviewer-override + citation page-range + wiki_coverage compact-pipe parse

- linear-write.md: add bad_form_audit + activity_split_audit pre-emit lines
- v7_build.py: _writer_preemit_audit_context() pipes audit into reviewer; reviewer_override threaded
- citation_matcher.py: page_end optional, range-aware match
- wiki_coverage_gate.py: compact pipe parse; <decide 2a outcome>
- tests: cover all four changes incl. multi-writer pre-emit smoke

Co-Authored-By: ...
```

PR-B:
```
feat(b1): publish adjectives comparative module

- starlight b1/adjectives-comparative.mdx: 4-tab V7 shape, 41 vocab, 11 activities
- b1/index.mdx: module 44 landing card marked complete
- depends on #<PR-A>

Co-Authored-By: ...
```

---

### Step 6 — Do NOT auto-merge

Both PRs land as `MERGEABLE` with all blocking CI green, but the orchestrator (Claude) will merge them in sequence. Do not pass `--admin` or `--auto`. Do not skip the `review/review` advisory failure — it's the known-broken Gemini Dispatch lane and is advisory only per #M-0.5, but DO NOT bypass any other failing check.

---

## What success looks like

- PR #2266 closed with a comment linking PR-A + PR-B as the replacement.
- PR-A merged first, all blocking CI green, plumbing concerns from §2 resolved with documented rationale.
- PR-B merged second, content fixes from §3 applied, Tab 4 metadata leak gone, off-topic prose deleted, VESUM check clean.
- A new follow-up issue filed re §3a root cause (assembler-level Tab 4 sanitizer).
- Orchestrator inbox has zero PR-related deltas left.

## What failure looks like

- PR-A and PR-B opened but content fixes from §3 skipped — STOP and report.
- Plumbing concerns from §2 deferred with "will address later" — STOP and report.
- Tab 4 metadata still contains "chunk_id" or "writer telemetry" — STOP and report.
- VESUM check shows hits and they were silently merged — STOP and report.

If any STOP condition fires, codex writes a `GOAL_ABORT` style status to the dispatch log with `last_cmd`, `last_cwd`, `last_output`, `next_action`, and exits 1.

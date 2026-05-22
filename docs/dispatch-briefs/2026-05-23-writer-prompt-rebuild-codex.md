# Dispatch brief — V7 writer-prompt rebuild

**Agent**: Codex (gpt-5.5, xhigh)
**Mode**: `--worktree --danger`
**Date**: 2026-05-23
**Origin**: Item #2 of the 5 outstanding items + the per-level interview matrix locked in main session 2026-05-23.

## Context

The m20 (a1/my-morning) revert (`944f4200e4`) exposed that the V7 writer prompt does NOT make the writer corpus-aware in the way the design demands. Specifically: the writer reaches only ~6 of the 30+ MCP tools available, has no level-gated corpus access, doesn't explain the INLINE/WORKBOOK pedagogical split, and doesn't operationalize the student-aware learner state injection.

Main session ran an interview with the user and locked a per-level corpus-access matrix + posture decisions. This brief implements those decisions in `scripts/build/phases/linear-write.md`.

**Critical reframing (so the brief is not misread):** the existing INLINE 4-6 / WORKBOOK 6-9 split in `ACTIVITY_CONFIGS["a1"]` is **pedagogically intentional**, NOT a bug. Inline activities are LIGHT theory-time checks (quizzes, observe, simple fill-ins) for the teaching moment. Workbook activities are SUBSTANTIVE drill (match-ups, classify, longer cloze, translate, error-correction) for after-lesson practice. They are **different activities written for different contexts**, not the same activity dual-rendered. The bug m20 surfaced is that the writer put all 10 inline and 0 in workbook — violating the split. The assembler correctly emitted "No workbook activities" as the signal the contract was broken. **Do not change the assembler. Do not implement P2 dual-rendering. Do not change `lesson-contract.md`.** The fix is in the writer prompt — make the split obligation crystal clear with examples per level, add a pre-emit self-audit, and the existing assembler handles the rest.

## Files to modify

ONE file: `scripts/build/phases/linear-write.md` (currently 707 lines).

Do NOT touch:
- `scripts/generate_mdx/core.py` (assembler is correct)
- `scripts/build/linear_pipeline.py` (pipeline is correct; only the prompt template needs work)
- `scripts/build/phases/linear-review-dim.md` (reviewer rebuild is a separate dispatch — out of scope here)
- `lesson-contract.md` / `docs/best-practices/v7-design-and-corpus.md` (these are SSOT and don't need updating for this PR)
- Plans, vocabulary, schemas, etc.

## What to change

### 1. Per-level corpus-access matrix (NEW section)

Add a new top-level section between the "Knowledge Packet" section (line 439) and "Module Context" (line 443). Title: `## Corpus Access (level-gated)`. This section MUST be inserted ABOVE Module Context because the writer reads Module Context to know its level, and the level determines which tools below are in-scope.

The section MUST contain a per-level table that the writer reads to determine which MCP tools are in-scope for THIS module. The level comes from `{LEVEL}` in Module Context. Render the table once; the writer is responsible for self-gating based on `{LEVEL}`.

Use this exact content (verbatim — the directive language is load-bearing):

```markdown
## Corpus Access (level-gated)

Your `{LEVEL}` from Module Context determines which MCP tools are in-scope. Tools NOT in your level's row are OUT OF SCOPE — do not call them and do not cite them. This gating exists because lower-level modules need register discipline; an A1 module quoting Stus is a register break even if the quote is verified.

| {LEVEL} | Textbooks | Literary | External | Vocab-level check | Always-on |
|---|---|---|---|---|---|
| **a1** | `search_text` (Grades 1-4 only — prefer G1-2 when satisfying `plan_references`; G3-4 only when the topic explicitly requires it) | `search_literary` filtered to children's literature, folk songs, fairy-tale openings, iconic phrases — query with collection filter `tag:a1-curated` (see §1.1) | ULP only: `search_external(collections=["ulp_blogs","ulp_youtube","pohribnyi_pronunciation"])` | `query_cefr_level` → stacked: PULS A1 → ubertext-freq top-1000 → ULP S1-S2 (see §1.2) | VESUM tools, `verify_quote`, `verify_source_attribution`, `check_modern_form`, `check_russian_shadow`, `search_style_guide`, `search_ua_gec_errors`, `query_pravopys` |
| **a2** | `search_text` (Grades 1-5) | `search_literary` filtered to `tag:a2-curated` (widens to add simple Stefanyk passages, Hlibov full, simple Lesya for children) | ULP + Pohribnyi (same as a1) | `query_cefr_level` → PULS A1+A2 → top-2000 → ULP S1-S4 | (same) |
| **b1** | `search_text` (full Grades 1-11) | `search_literary` (FULL corpus — chronicles, poetry, prose, legal texts) | All 8 collections: `ulp_blogs`, `ulp_youtube`, `pohribnyi_pronunciation`, `istoria_movy`, `realna_istoria`, `komik_istoryk`, `imtgsh`, `other_blogs` | `query_cefr_level` → PULS A1-B1 → top-5000 → ULP S1-S6 | (same) |
| **b2** | (inherit b1) | (inherit b1) | (inherit b1) | (inherit b1, extend to PULS A1-B2) | (same) — content modes EXPAND (see §1.3) |
| **c1** | (inherit b1) | (inherit b1) | (inherit b1) + when ingested: peer-reviewed UA scholarship | (inherit b1, extend to PULS A1-C1) | (same) — posture shifts (see §1.4) |
| **c2** | (inherit c1) | (inherit c1) | (inherit c1) | (same as c1) | (same as c1) |
| **seminar (hist/oes/ruth/istorio)** | full | full + ingested OES manuscripts + Ruthenian Baroque corpus | full + ingested academic UA scholarship | (n/a — seminar is not vocab-driven) | strict-2-source citation rule (see §1.5) |
| **seminar (lit/bio + sub-tracks)** | full | full | full + ingested academic UA scholarship | (n/a) | hybrid posture (see §1.4) |

The bracketed `tag:` values in literary filtering (e.g. `tag:a1-curated`) refer to a follow-up filter layer (#F1 from the interview matrix) that is being built separately. **For this PR**, the writer should call `search_literary` with the level-appropriate intent in mind (children's lit at A1; widen at A2; full at B1+) and the gate will be enforced once the tag layer ships. Do NOT block on the tag layer; the directive language is the load-bearing contract.

### §1.1 Literary filter intent at A1/A2

A1/A2 literary scope means: short children's literary excerpts (`Глібов байки`, ditemai-poetry, simple folk songs, fairy-tale openings, iconic phrases like `Реве та стогне Дніпр широкий`). NOT chronicles, NOT dense modernist prose (Khvylovy, Pidmohylny, Zabuzhko), NOT Stus, NOT legal texts.

When you call `search_literary` at A1/A2 and a result returns an excerpt from outside this scope, DROP IT from your knowledge packet. Cite only level-appropriate excerpts. Register drift via "well-verified but wrong-register" literary quoting was the H1 prompt-bug failure mode (see `audit/2026-05-17-judge-calibration-h1/COMPARISON.md`).

### §1.2 Stacked vocab-level check

When introducing a new lemma BEYOND what `plan_references` mandates:

1. **First**: `query_cefr_level(lemma)`. If the result is your `{LEVEL}` or below (A1 ≤ A1; A2 ≤ A2; B1 ≤ B1; etc.), the lemma is in-scope.
2. **Else, fallback**: check `ubertext-freq` rank. If `rank ≤ 1000` at A1, `≤ 2000` at A2, `≤ 5000` at B1+, in-scope.
3. **Else, fallback**: check ULP cumulative coverage. If the lemma appears in `ulp_blogs` or `ulp_youtube` content for Season ≤ the level's season cap (A1: S1-S2, A2: S1-S4, B1+: S1-S6), in-scope.
4. **If none pass**: omit the lemma. Use plan-mandated vocabulary instead. Do NOT introduce a lemma that fails all three checks.

Record this gate in `<plan_reasoning>` under `<vocab_level_check>` for any non-plan lemma you intend to introduce.

### §1.3 Content modes at B2+

At B2 the writer's content surfaces EXPAND beyond A1-B1's "dialogue + rule explanation + prose":
- **Literary commentary** — 1-3 paragraph analysis of a Stefanyk / Franko / Lesya passage
- **Cultural-analysis prose** — e.g. "the кобзар tradition in 19th-c. Ukraine"
- **Historical narrative** — multi-paragraph chronological account
- Same evidence rule applies (every example traces to corpus); same VESUM + verify_quote + verify_source_attribution discipline.

### §1.4 Posture shifts at C1+ / seminars

- **C1**: HYBRID posture. Factual claims (dates, attributions, definitions, citations) MUST be tool-backed pre-emission. Prose flow connecting cited claims may be generated freely without per-sentence RAG. Still no fabrication paths: facts cited; transitions crafted.
- **C2**: same as C1; maxed sophistication.
- **Seminar history tracks (hist/oes/ruth/istorio)**: STRICT 2-source rule for every historical claim. Date + figure + event + attribution → ≥2 sources cited inline. `verify_quote` for primary-source quotes. Decolonization claims require evidence-pair (myth + truth from named sources).
- **Seminar lit/bio + sub-tracks**: HYBRID (same as C1).

### §1.5 Strict-2-source for seminar history claims

For HIST / OES / RUTH / ISTORIO modules, every historical CLAIM (a date, a figure's action, an event, an attribution) MUST cite ≥2 sources inline. Format: `«claim text» [Hrushevsky, Історія України-Руси, т. 3, p. 84; Plokhy, The Gates of Europe, p. 142]`. Where claim and counter-claim diverge (decolonization framing), name BOTH the imperial source (`Karamzin's История Государства Российского`) and the UA-grounded counter (Hrushevsky, Plokhy, etc.).
```

### 2. INLINE/WORKBOOK pedagogical clarification (REPLACE existing §)

Find the existing "## Activity Types" section (line 558-570). REPLACE the entire section with the following content, preserving the `{ALLOWED_ACTIVITY_TYPES}` / `{FORBIDDEN_ACTIVITY_TYPES}` / `{INLINE_ALLOWED_TYPES}` / `{WORKBOOK_ALLOWED_TYPES}` / `{ACTIVITY_COUNT_TARGET}` / `{VOCAB_COUNT_TARGET}` placeholders so the existing fill-template still works:

```markdown
## Activity Types and the INLINE / WORKBOOK split (mandatory)

Every module ships TWO complementary activity sets, NOT one. This is how textbooks work and how the curriculum is configured.

### Inline activities — LIGHT, theory-time
Inline activities are LIGHT checks emitted during the teaching prose. Their purpose is "did you just get this concept? — try one quick thing before we continue." They are anchored to a specific theory section via the `<!-- INJECT_ACTIVITY: act-N -->` marker placed inside the prose of that section. They should be FAST (≤30 seconds for the learner), simple, and NEVER overshadow the explanation.

Allowed inline types for `{LEVEL}`: {INLINE_ALLOWED_TYPES}

### Workbook activities — SUBSTANTIVE, after-lesson practice
Workbook activities are SUBSTANTIVE drill emitted with NO `<!-- INJECT_ACTIVITY -->` marker. They populate the lesson's Activities (`Вправи`) tab. Their purpose is "now you've seen the rule explained — apply it in volume until the pattern is automatic." They are LONGER (1-3 minutes for the learner), often multi-item, designed for review and self-assessment.

Allowed workbook types for `{LEVEL}`: {WORKBOOK_ALLOWED_TYPES}

### Split targets and overall budget

Activity count target for `{LEVEL}`: {ACTIVITY_COUNT_TARGET}
Vocabulary count target for `{LEVEL}`: {VOCAB_COUNT_TARGET}

For A1: 10 total activities = 4-6 INLINE + 6-9 WORKBOOK (the ranges overlap because writer judgement balances within the total).
For A2: 12 total = 4-6 INLINE + 8-11 WORKBOOK.
For B1-core / B2-core / C1-core: 16 total = 5-7 INLINE + 11-15 WORKBOOK.
For C2: 12 total = 4-5 INLINE + 8-10 WORKBOOK.

### Design principle (read before drafting)

When designing each activity, decide its CONTEXT first:
- Is this a quick "did the concept land?" check that belongs INSIDE the teaching prose? → INLINE (use an INJECT marker, keep the activity simple).
- Is this a comprehensive drill, integration, or extension? → WORKBOOK (no INJECT marker, longer item count, harder discrimination).

The same item TYPE can appear in both sets — a quiz can be a 2-question inline check OR an 8-question workbook drill — but they are DIFFERENT activity instances, written for different pedagogical contexts. Do NOT just duplicate inline activities into the workbook section. Do NOT shove everything into one set.

### Allowed types (global)

Allowed (any context): {ALLOWED_ACTIVITY_TYPES}
Forbidden at this level: {FORBIDDEN_ACTIVITY_TYPES}

### Pre-emit activity-split audit (MANDATORY — new gate, parallel to `<implementation_map_audit>` and `<bad_form_audit>`)

Before emitting the four artifact fences, you MUST self-audit your activity split.

1. Count activities in `activities.yaml` that have a matching `<!-- INJECT_ACTIVITY: act-X -->` marker in `module.md` → call this `INLINE_N`.
2. Count activities in `activities.yaml` that do NOT have a matching `<!-- INJECT_ACTIVITY: act-X -->` marker → call this `WORKBOOK_N`.
3. Verify both counts fall within the level's allowed ranges (see "Split targets" above). For A1: `INLINE_N ∈ [4, 6]` and `WORKBOOK_N ∈ [6, 9]`. If EITHER count is outside its range, STOP. Either move activities between sets (add/remove INJECT markers) or write additional workbook activities. Do not proceed until both ranges are satisfied.

Emit a single visible audit line BEFORE the artifact fences (after `<implementation_map_audit>` and `<bad_form_audit>` lines):

`<activity_split_audit>level={LEVEL} inline_n=N workbook_n=N inline_range=[lo,hi] workbook_range=[lo,hi] split_valid=true|false</activity_split_audit>`

If `split_valid=false`, the rebuild is wasted. The deterministic post-build gate will reject; do not try to ship past this audit.
```

### 3. Strengthen the student-aware framing directive

Find the "## Learner State" section (line 452). REPLACE the existing two-sentence directive with this content (keeping the `{LEARNER_STATE}` placeholder):

```markdown
## Learner State

This learner has completed modules 1..{MODULE_NUM}-1 in track `{LEVEL}`. The vocabulary they have been formally taught is listed below as "Cumulative vocabulary"; the grammar topics they've been exposed to are listed as "Grammar already taught." Treat both as the FLOOR of what this module's prose may assume.

Rules of engagement with prior learning (binding):

1. **Don't re-explain already-taught grammar.** If the learner has already seen the rule, refer back briefly (`як ти бачив у модулі N` / `as in module N`) and BUILD on it. Re-explaining is patronizing and wastes word budget.

2. **Don't introduce vocabulary that is neither in the cumulative list nor in this module's declared `vocabulary.yaml`.** From m04 onward this is a HARD audit failure (`unknown_vocab_in_prose`); for m01-m03 it's a WARN. Specifically: every Ukrainian content word in your `module.md` prose, dialogue lines, and example sentences MUST appear either (a) in the cumulative list, (b) in this module's `vocabulary.yaml`, OR (c) be a proper noun / Latin-character borrowing exempt from this rule.

3. **Soft scaffolding via foreshadowing.** When you introduce a new lemma BEFORE its formal vocabulary entry (e.g. you use a word in the lesson prose that gets defined later in `vocabulary.yaml`), provide an inline gloss — `**вмиватися** *(to wash oneself)*` — at first mention. This is the "show before you tell" pattern, not a violation.

4. **Frequency-and-CEFR awareness when introducing new vocab.** Before introducing any non-plan lemma, run the stacked check from §1.2 (Corpus Access). PULS-level → freq-rank → ULP-coverage. If none pass for your `{LEVEL}`, omit and choose differently.

5. **Build on cumulative grammar where natural.** If a previous module taught a case ending and your current module's topic touches that case, USE it without re-deriving. Repetition-in-context is how grammar consolidates; verbatim re-explanation isn't.

{LEARNER_STATE}
```

### 4. Surface the missing MCP tools in the verification discipline

Find the "## Tier-1 verification discipline (do this WHILE drafting — #1661)" section (line 77). Add the following sub-section AT THE END of that block (just before line 271's "Return the visible `<plan_reasoning>`..." instruction):

```markdown
### Additional MCP tools — surface and use

The verification discipline above covers the load-bearing checks. The pipeline also exposes these tools; use them when their evidence is relevant:

- `mcp__sources__search_literary` — primary literary sources (125K chunks: chronicles, poetry, prose, legal texts). Use at b1+ for full access; at a1/a2 use only the level-curated subset per §1.1 of the Corpus Access section.
- `mcp__sources__search_idioms` — Frazeolohichnyi (25K idioms). Use when prose needs a natural Ukrainian idiom rather than an English-calque construction.
- `mcp__sources__search_definitions` — СУМ-11 (127K entries; 7,152 flagged for Soviet ideological framing). **Use with caution**: every result row carries `sovietization_risk` (0/1/2). Risk ≥ 1 → do NOT reproduce the definition verbatim; paraphrase neutrally OR query `search_grinchenko_1907` / `search_heritage` for a pre-Soviet alternative. Issue #1659.
- `mcp__sources__search_grinchenko_1907` — Hrinchenko historical dictionary (67K entries, 1907). Pre-Soviet usage attestation. Use when you need to show that an "unusual-looking" UK form is authentic UK heritage, NOT a Russianism.
- `mcp__sources__search_esum` — ESUM etymological dictionary (vol. 1 indexed; vols. 2-6 in `data/processed/esum_vol{2..6}.jsonl`). Cognate maps, Proto-Slavic forms, borrowing chronology.
- `mcp__sources__search_synonyms` — Ukrajinet WordNet (122K synsets, auto-translated from English WordNet — caveat #1657). Use sparingly; cross-check with `search_style_guide` or native Ukrainian context before substituting.
- `mcp__sources__translate_en_uk` — Балла EN→UK (79K entries). Use when you have an English source and need the canonical UK translation, especially for vocabulary-yaml `translation:` fields.
- `mcp__sources__query_pravopys` — Правопис 2019 orthography rules. The authoritative reference for spelling (м'який знак, апостроф, capitalization, hyphenation). Cite when emitting any rule about Ukrainian orthography.
- `mcp__sources__query_cefr_level` — PULS CEFR vocabulary (5.9K words tagged A1-C1). The vocab-level check from §1.2.
```

### 5. Update Pre-emit verification checklist

Find the "## Pre-emit verification (run BEFORE you write any artifact)" section (line 670). REPLACE the existing 4-line checklist with this expanded checklist:

```markdown
## Pre-emit verification (run BEFORE you write any artifact)

Confirm you have made AT LEAST one of each of the following MCP tool calls. If any line below is FALSE for your current session, make the call now BEFORE emitting any artifact:

1. **Textbook grounding** — `mcp__sources__search_text` for each `plan_references` textbook entry (one call per entry; verify the citation page exists in the search hit). Level-gate per §1: A1 uses Grades 1-4; A2 uses 1-5; B1+ uses full.
2. **Multimedia obligation** — AT LEAST ONE of `mcp__sources__query_wikipedia`, `mcp__sources__search_external` (with level-appropriate collections per §1: A1/A2 = `ulp_blogs`+`ulp_youtube`+`pohribnyi_pronunciation`; B1+ = all 8), OR `mcp__sources__search_images`. Non-negotiable: the `resources_search_attempted` gate REJECTS modules with `multimedia_calls_total == 0`.
3. **VESUM verification** — `mcp__sources__verify_words` on EVERY Ukrainian form you intend to write that isn't trivially known (top-100 frequency). One batched call per dozen lemmas is fine.
4. **Russianism check** — `mcp__sources__search_style_guide` on at least one Russianism-candidate form when teaching contrast pairs.
5. **Literary grounding (when applicable)** — `mcp__sources__search_literary` for any literary quote or cultural attribution. Level-gate per §1.1: A1/A2 use the curated subset; B1+ use full.
6. **CEFR level check (when introducing non-plan lemmas)** — `mcp__sources__query_cefr_level` per §1.2's stacked check.
7. **Style guide / Antonenko grounding (when emitting bad-form contrast)** — `mcp__sources__search_style_guide` (structured) AND `mcp__sources__search_text source=antonenko-davydovych-yak-my-hovorymo` (full-book prose). Both are required; the H1 prompt bug failed when only structured was queried.

If any line above is FALSE and is in-scope for your `{LEVEL}` per §1 (Corpus Access), make the call now. Do not emit artifacts until the checklist is fully green for your level.
```

## Acceptance criteria (deterministic)

Codex MUST verify these BEFORE opening the PR. Quote raw output in PR body.

| # | Check | Expected |
|---|---|---|
| 1 | `grep -c "## Corpus Access (level-gated)" scripts/build/phases/linear-write.md` | `== 1` |
| 2 | `grep -c "INLINE / WORKBOOK split" scripts/build/phases/linear-write.md` | `>= 1` |
| 3 | `grep -c "activity_split_audit" scripts/build/phases/linear-write.md` | `>= 2` (one in the audit-rule prose; one in the format-line example) |
| 4 | `grep -c "search_literary" scripts/build/phases/linear-write.md` | `>= 3` (was 0 before; now in Corpus Access table + the new tools section + the Pre-emit checklist) |
| 5 | `grep -c "ulp_youtube\|ulp_blogs" scripts/build/phases/linear-write.md` | `>= 2` (named in the Corpus Access table A1 row + the Pre-emit checklist) |
| 6 | `grep -c "query_cefr_level" scripts/build/phases/linear-write.md` | `>= 2` |
| 7 | `grep -c "Don't re-explain already-taught" scripts/build/phases/linear-write.md` | `== 1` |
| 8 | `wc -l scripts/build/phases/linear-write.md` | grows by ~120-180 lines (current 707 → target ~830-880). Significantly larger files indicate scope creep |
| 9 | `python -c "import yaml; t = open('scripts/build/phases/linear-write.md').read(); assert '{LEVEL}' in t and '{MODULE_NUM}' in t and '{LEARNER_STATE}' in t and '{INLINE_ALLOWED_TYPES}' in t"` | passes (placeholder integrity intact) |

## Test additions

No automated test for prompt content. The pipeline-level test is: dispatch a build for `a1/my-morning` AFTER this change ships, observe that:
- Writer emits 4-6 inline activities + 6-9 workbook activities (not 10-0)
- Writer calls `search_literary` at least once at a1-curated scope
- Writer calls `query_cefr_level` at least once
- Writer's `<activity_split_audit>` line emits with `split_valid=true`

That validation will happen in a follow-up build, not in this PR. This PR ships the prompt text.

## Numbered steps (from project DISPATCH-BRIEF CHECKLIST)

1. `git worktree add .worktrees/dispatch/codex/writer-prompt-rebuild-2026-05-23 origin/main` (auto-created via `--worktree` flag)
2. Branch: `codex/writer-prompt-rebuild-2026-05-23`
3. Edit `scripts/build/phases/linear-write.md` per §1-§5 above. Preserve all existing placeholders (`{LEVEL}`, `{MODULE_NUM}`, `{LEARNER_STATE}`, `{INLINE_ALLOWED_TYPES}`, etc.).
4. Run all 9 acceptance criteria; quote raw output in PR body.
5. `git add scripts/build/phases/linear-write.md`
6. Conventional commit: `feat(writer-prompt): per-level corpus access + INLINE/WORKBOOK clarity + student-aware framing — locks 2026-05-23 interview matrix`
7. `git push -u origin codex/writer-prompt-rebuild-2026-05-23`
8. `gh pr create` with title matching commit subject. PR body MUST include:
   - Summary (3 bullets)
   - The locked interview matrix table (copy from §1 of this brief)
   - Acceptance criteria results (all 9, raw output)
   - Test plan: "Validate by firing one A1 build under the new prompt; verify inline ∈ [4,6] + workbook ∈ [6,9] + `search_literary` called + `query_cefr_level` called"
9. **DO NOT auto-merge.** Orchestrator reviews.

## NOT in scope

- Do NOT touch `scripts/generate_mdx/core.py`, `scripts/build/linear_pipeline.py`, `lesson-contract.md`, `docs/best-practices/v7-design-and-corpus.md`, plans, vocabulary files, schemas.
- Do NOT implement P2 dual-rendering. The interview clarified this was a misread — assembler is correct.
- Do NOT add deterministic gates for the activity-split. The pre-emit `<activity_split_audit>` is writer-self-audit; the deterministic gate is a follow-up.
- Do NOT build the curated literary tag layer (F1 from interview matrix). The prompt directive references it as future scope — that's correct for this PR.
- Do NOT ingest academic UA scholarship (F2-F5). Those are separate ingestion dispatches — referenced from this prompt but not gating it.
- Do NOT rewrite the reviewer prompt (`linear-review-dim.md`). That's a separate dispatch.

## #M-4 preamble — deterministic claims

Verifiable claims in this PR body, paired with tool grounding:

| Claim | Tool / evidence required |
|---|---|
| "acceptance criterion N pass" | The literal grep / wc / python command output, quoted raw |
| "commit landed" | `git log -1 --oneline` raw output |
| "PR opened" | `gh pr view --json url` raw URL |
| "placeholders preserved" | `grep '{LEVEL}\|{MODULE_NUM}\|{LEARNER_STATE}\|{INLINE_ALLOWED_TYPES}\|{WORKBOOK_ALLOWED_TYPES}' scripts/build/phases/linear-write.md` raw output

No claim in this PR body without the tool output quoted.

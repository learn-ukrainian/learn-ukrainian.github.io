# Dispatch brief — V7 reviewer-prompt rebuild (per-dim LLM judge)

**Agent**: Codex (gpt-5.5, xhigh)
**Mode**: `--worktree --danger`
**Date**: 2026-05-23
**Origin**: Item #3 (reviewer prompt corpus-awareness + activity-split awareness) closing out the 5 outstanding items from `docs/session-state/2026-05-23-m20-root-cause-fixed-corpus-matrix-locked.md`.

## Context

Companion to PR #2214 (writer-prompt rebuild, merged as `9178aea5c4`). The writer prompt now encodes the locked per-level corpus matrix (a1→c2 + seminars), the INLINE/WORKBOOK split, the stacked vocab-level check, and the strengthened student-aware framing. The reviewer must mirror those audits on the audit side — otherwise the writer can violate the new rules without the per-dim LLM judge catching it.

The reviewer rebuild is intentionally NARROWER than the writer rebuild. The writer needed substantial new content (~158 LOC added). The reviewer needs targeted audit hooks (~80-120 LOC added) — pointing the LLM judge at the writer's new self-audits and the new contracts.

## Files to modify

ONE file: `scripts/build/phases/linear-review-dim.md` (currently 138 lines).

Do NOT touch:
- `scripts/build/phases/linear-write.md` — writer prompt is the just-merged contract; reviewer audits against it
- `scripts/generate_mdx/core.py`, `scripts/build/linear_pipeline.py` — pipeline correct
- Plans, schemas, fixtures
- The per-dim reviewer-CALLING code; only the prompt template

## What to change

### 1. Extend the Tier-1 verification audit (REPLACE existing §A-E with §A-I)

Find the section "## Tier-1 verification audit (do this DURING evidence search — #1661)" (around line 74). The current section has audits A-E. **Keep A-E unchanged** (source attribution, quote verification, sovietization, heritage-defense, reinforce rule #6). **Add four new audits F-I** between current E and the JSON-output instructions (around line 107).

#### Audit F (NEW) — Activity split audit (dimensions: pedagogical, engagement)

```markdown
F. **Activity split audit (pedagogical, engagement).** The writer is contracted to emit two complementary activity sets per `ACTIVITY_CONFIGS[{LEVEL}]`: INLINE (light, theory-time checks anchored via `<!-- INJECT_ACTIVITY: act-N -->`) and WORKBOOK (substantive, after-lesson drill, no INJECT marker). For A1: INLINE 4-6 / WORKBOOK 6-9 (10 total). For A2: INLINE 4-6 / WORKBOOK 8-11 (12 total). For B1-core/B2-core/C1-core: INLINE 5-7 / WORKBOOK 11-15 (16 total). For C2: INLINE 4-5 / WORKBOOK 8-10 (12 total).

The writer is required to emit a self-audit line `<activity_split_audit>level={LEVEL} inline_n=N workbook_n=N inline_range=[lo,hi] workbook_range=[lo,hi] split_valid=true|false</activity_split_audit>` before the artifact fences. Locate this line and verify:

1. The line is PRESENT. Missing → FLAG `activity_split_audit_missing` (counts as evidence-against this dim).
2. The reported `inline_n` matches the actual count of `<!-- INJECT_ACTIVITY: act-N -->` markers in `module.md`.
3. The reported `workbook_n` matches `len(activities.yaml) - inline_n`.
4. Both counts fall within the level's allowed ranges per §"Corpus Access" of the writer prompt.

If the writer's self-audit reports `split_valid=true` BUT the actual counts violate the range, that is a worse failure than `split_valid=false` (a writer lying in its own audit). FLAG `activity_split_audit_lied`.

Pedagogical consequence to score against: INLINE activities that are too long/substantive (item count > 3, multi-paragraph rubrics) break their "fast theory check" purpose; WORKBOOK activities that are too trivial (single-item quizzes, no discrimination depth) break their drill purpose. Score the BALANCE-vs-PURPOSE not just the count.
```

#### Audit G (NEW) — Corpus-access audit (all dims)

```markdown
G. **Corpus-access audit (all dims).** The writer is gated to a level-specific corpus surface per the Corpus Access (level-gated) table in `linear-write.md`. Verify the writer did not cite out-of-level sources:

- **a1/a2 textbook scope**: only Grades 1-4 (a1) or 1-5 (a2) source files allowed in citations. A `Караман Grade 10` citation in an a1 module is OUT OF SCOPE. FLAG `out_of_level_textbook`.
- **a1/a2 literary scope**: only children's literature, folk songs, fairy-tale openings, iconic phrases. A Stus / Khvylovy / Zabuzhko / Pidmohylny quote in an a1/a2 module is a register break. FLAG `out_of_level_literary`. (The curated-tag filter — F1 — is not yet built; rely on author/work register judgment.)
- **a1/a2 external scope**: only `ulp_blogs`, `ulp_youtube`, `pohribnyi_pronunciation` from `search_external`. Citations from `istoria_movy`, `realna_istoria`, `komik_istoryk`, `imtgsh`, `other_blogs` at a1/a2 are out of scope. FLAG `out_of_level_external`.
- **b1+/seminars**: full corpus allowed; only flag if the writer claims a source NOT in our corpus at all (fabrication, separate failure class covered by audits A-B).

For ANY out-of-level citation, the quote may STILL be factually correct but the register/source choice is wrong for the learner level. Score this as PEDAGOGICAL evidence-against, not as a fabrication.
```

#### Audit H (NEW) — Student-aware audit (pedagogical, engagement, naturalness)

```markdown
H. **Student-aware audit (pedagogical, engagement, naturalness).** The writer is given a `{LEARNER_STATE}` block listing cumulative_vocabulary + known_grammar from prior modules. Verify the writer:

1. **Did not re-explain already-taught grammar.** If the learner-state lists "Genitive case endings -а/-я" as known_grammar and this module derives the rule from scratch in 200+ words, FLAG `re_explained_known_grammar`. Brief reference (`як ти бачив у модулі 7`) is fine; a full re-derivation is not.

2. **Did not introduce unknown vocabulary without inline gloss.** Scan `module.md` prose for Ukrainian content words. For any word that is (a) NOT in cumulative_vocabulary, (b) NOT in this module's `vocabulary.yaml`, (c) NOT a proper noun / Latin borrowing, and (d) NOT introduced with inline italic gloss `*(translation)*`, FLAG `unknown_vocab_unscaffolded`.

3. **Foreshadowing pattern visible.** If new lemmas appear in prose BEFORE their `vocabulary.yaml` entry, they should carry inline gloss at first mention. Absence of gloss on first mention = `missing_foreshadowing_gloss`.

4. **Stacked vocab-level check evidence.** For non-plan lemmas the writer introduced, check the `<plan_reasoning>` for `<vocab_level_check>` nodes. Missing for a non-plan lemma = `unverified_vocab_introduction`.

Pedagogical score: respecting the learner's prior knowledge is what makes the module BUILD instead of REPEAT. Naturalness score: scaffolded vocabulary introduction reads as a real teacher's voice; un-introduced vocab feels like a textbook dump.
```

#### Audit I (NEW) — Pre-emit audit-line integrity (all dims)

```markdown
I. **Pre-emit audit-line integrity (all dims).** The writer is required to emit three machine-readable audit lines BEFORE the artifact fences, in order:

1. `<implementation_map_audit>manifest_obligations=N covered_in_map=M missing=[...]</implementation_map_audit>` (per #2094)
2. `<bad_form_audit>italic_bad_form_patterns_found=N converted_to_marker=N remaining=0</bad_form_audit>` (per #2095)
3. `<activity_split_audit>level={LEVEL} inline_n=N workbook_n=N inline_range=[lo,hi] workbook_range=[lo,hi] split_valid=true|false</activity_split_audit>` (per the just-merged Activity Types section)

Verify ALL THREE lines are present, parseable, and report values consistent with the artifacts. Any missing line = the writer has failed the protocol; FLAG `audit_line_missing` with the missing line name. Any line whose claim doesn't match the artifacts = FLAG `audit_line_inconsistent`.

These audits exist BECAUSE the writer is doing self-grading; the reviewer's job here is to cross-check that the self-grading matches reality. A green audit line on broken content is a more serious failure than a red audit line on broken content (the writer is lying to its own audit).
```

### 2. Extend the dimension scope language (REPLACE existing § "Scope — JUDGMENT ONLY")

Find the section "## Scope — JUDGMENT ONLY, do NOT re-litigate deterministic gates" (around line 13). The current per-dim rubrics (engagement, pedagogical, naturalness, decolonization, tone) are correct — keep them. Add ONE new paragraph at the end of the section to acknowledge the new audits feed certain dims:

```markdown
The Tier-1 audits below (A through I, expanded in this rebuild) feed evidence into specific dims as labeled. Audit F (activity split) → pedagogical + engagement. Audit G (corpus access) → all dims, weighted strongest for pedagogical (out-of-level citations are mostly a pedagogical problem). Audit H (student-aware) → pedagogical + engagement + naturalness. Audit I (audit-line integrity) → all dims, as a meta-signal that the writer was honest with itself.

A dim scoring high while the audits surface FLAGs is a reviewer-protocol failure — the dim's rubric must absorb the audit evidence. A dim scoring low without any audit FLAGs is allowed, but evidence_quotes must justify the score from the residual rubric alone.
```

### 3. Extend the JSON output format

The current JSON output is:
```json
{"score": 0.0, "evidence_quotes": [...], "rubric_mapping": "...", "evidence": "...", "verdict": "REVISE"}
```

Extend it to include a `flags` array carrying any of the new FLAG names from §F-I above. Update the spec section near the bottom of the file:

```markdown
Return only JSON:

```json
{"score": 0.0, "evidence_quotes": ["verbatim quote 1", "verbatim quote 2", "verbatim quote 3"], "rubric_mapping": "Quote 1: ...; Quote 2: ...; Quote 3: ...", "evidence": "\"verbatim quote from evidence_quotes\"", "flags": ["activity_split_audit_missing", "out_of_level_literary", ...], "verdict": "REVISE"}
```

The `flags` array MUST contain any FLAG strings raised during audits A-I that apply to your assigned dim per the per-dim labeling in §"Scope". An empty array is fine when no flags fired. The pipeline aggregates flags across dims and surfaces them in the build telemetry; the writer's self-correction loop reads them to know what to fix on retry.
```

(Replace the existing "Return only JSON:" block and its example at lines 107-111 with this expanded version.)

## Acceptance criteria (deterministic)

Codex MUST verify these BEFORE opening the PR. Quote raw output in PR body.

| # | Check | Expected |
|---|---|---|
| 1 | `grep -c "^F\. \*\*Activity split audit" scripts/build/phases/linear-review-dim.md` | `== 1` |
| 2 | `grep -c "^G\. \*\*Corpus-access audit" scripts/build/phases/linear-review-dim.md` | `== 1` |
| 3 | `grep -c "^H\. \*\*Student-aware audit" scripts/build/phases/linear-review-dim.md` | `== 1` |
| 4 | `grep -c "^I\. \*\*Pre-emit audit-line integrity" scripts/build/phases/linear-review-dim.md` | `== 1` |
| 5 | `grep -c "activity_split_audit_missing\|activity_split_audit_lied" scripts/build/phases/linear-review-dim.md` | `>= 2` |
| 6 | `grep -c "out_of_level_textbook\|out_of_level_literary\|out_of_level_external" scripts/build/phases/linear-review-dim.md` | `>= 3` |
| 7 | `grep -c "unknown_vocab_unscaffolded\|missing_foreshadowing_gloss\|re_explained_known_grammar\|unverified_vocab_introduction" scripts/build/phases/linear-review-dim.md` | `>= 4` |
| 8 | `grep -c "\"flags\":" scripts/build/phases/linear-review-dim.md` | `>= 1` (the JSON example uses double-quotes per JSON spec) |
| 9 | `wc -l scripts/build/phases/linear-review-dim.md` | grows by ~80-130 lines (current 138 → target ~218-268) |
| 10 | placeholder integrity: `grep -c "{DIM}\|{LEVEL}\|{LEARNER_STATE}" scripts/build/phases/linear-review-dim.md` | `>= 4` (was 4 before — none removed) |

## Numbered steps (per project DISPATCH-BRIEF CHECKLIST)

1. `git worktree add` (auto via `--worktree` flag) from origin/main
2. Branch: `codex/reviewer-prompt-rebuild-2026-05-23`
3. Edit `scripts/build/phases/linear-review-dim.md` per §1-§3 above. Preserve all existing placeholders.
4. Run all 10 acceptance criteria. Quote raw output in PR body.
5. `git add scripts/build/phases/linear-review-dim.md`
6. Conventional commit: `feat(reviewer-prompt): activity-split + corpus-access + student-aware audits + flags array — mirrors writer-prompt rebuild from PR #2214`
7. `git push -u origin codex/reviewer-prompt-rebuild-2026-05-23`
8. `gh pr create` — body MUST include: summary (3 bullets), acceptance criteria results (raw), test plan (validate at next a1/my-morning build), reference to PR #2214 (writer side).
9. **DO NOT auto-merge.** Orchestrator reviews.

## NOT in scope

- Do NOT touch the writer prompt (`linear-write.md`) — that's PR #2214's contract, locked.
- Do NOT touch the pipeline code (`scripts/build/linear_pipeline.py`) — flag-aggregation is already wired (per existing `flags` handling).
- Do NOT add deterministic gates for these audit checks — they're reviewer-LLM judgment, intentional.
- Do NOT add NEW dims (engagement/pedagogical/naturalness/decolonization/tone is the locked set).
- Do NOT change the JSON schema beyond adding `flags` — `score`/`evidence_quotes`/`rubric_mapping`/`evidence`/`verdict` are downstream-parsed.

## #M-4 preamble — deterministic claims

| Claim in PR body | Tool / evidence required |
|---|---|
| "acceptance criterion N pass" | The literal grep / wc command output, quoted raw |
| "commit landed" | `git log -1 --oneline` raw output |
| "PR opened" | `gh pr view --json url` raw URL |
| "placeholders preserved" | `grep '{DIM}\|{LEVEL}\|{LEARNER_STATE}\|{IMMERSION_RULE}\|{CONTRACT_YAML}\|{PLAN_CONTENT}\|{MODULE_NUM}\|{MODULE_SLUG}\|{WORD_TARGET}\|{GENERATED_CONTENT}' scripts/build/phases/linear-review-dim.md` raw output

No claim without quoted tool output.

# Dispatch brief — A1 m20 anchor build (a1/my-morning)

**Agent**: codex
**Mode**: danger
**Effort**: xhigh
**Branch base**: `origin/main`
**Task ID**: `a1-m20-anchor-2026-05-26`
**Writer (inside v7_build.py)**: `claude-tools` (V7 default per 2026-05-12 decision)
**Reviewer**: pipeline default (linear-review-dim.md)

## Why this is on codex (one-shot ANCHOR delivery)

User routing decision 2026-05-24: codex handles a1/m20 as the **anchor** module — the reference build that future a1/a2 modules will pattern-match against. Claude takes m01-m19 + m21-m55 + all of A2 AFTER this lands. m20 was selected as the anchor because (a) it has the most prior build history + audit signal (#1948 mid-May runs), (b) reflexive verbs at A1.3 is a load-bearing grammar moment that surfaces both phonological and morphological challenges, and (c) the previous m20 ship (944f4200e4, reverted 2026-05-23) collapsed on Tab 4 metadata leak + empty Activities tab + 10-inline / 0-workbook split — all of which must NOT recur here.

This brief assumes the writer is claude-tools (V7 default). Codex is the dispatch driver — runs the build, performs the §4 ten-check verify-before-promote, opens the PR. Codex does NOT write content.

## Read first (do not paraphrase from memory)

- `gh issue view 2208` (workbook auto-inject contract) — landed as #2264, the writer prompt now states INLINE-only INJECT_ACTIVITY
- `gh issue view 2209` (mdx-assembler Tab 3 inline cross-ref) — landed as #2265
- `docs/best-practices/v7-design-and-corpus.md` §1.3, §3, §4 (10-check), §5 (known-broken list — items 1-3 closed by #2265+#2264; items 4-6 remain)
- `docs/best-practices/ulp-presentation-pattern.md` — Anna Ohoiko's 7 practices + S1→S6 progression
  - **m20 is mid-S1**, NOT a boundary case. Apply S1 BASELINE (em-dash gloss, EN-primary, short UK dialogues, stress marks throughout). Do NOT apply S2 step-change patterns.
  - For m20 specifically (grammar-focused, not phonics): the "X sounds like Y" anti-pattern is not the risk; the risk is **EN-first reflexive-verb explanation**. Ohoiko-style: present the UK form first (`Я вмива́юся`) then the EN gloss, then the rule. NOT "Reflexive verbs in Ukrainian add -ся to the end. For example, вмиватися."
- `curriculum/l2-uk-en/plans/a1/my-morning.yaml` v1.2.3 (target module plan — `targets.new_vocabulary` is present, learner-state plan-fallback per PR #2272 will consume it)
- `scripts/build/phases/linear-write.md` (writer prompt — the contract claude-tools will follow)
- `scripts/build/phases/linear-review-dim.md` (reviewer prompt — what the build will self-grade against)
- `scripts/build/v7_build.py --help` (CLI surface, --worktree behavior, exit codes)
- `docs/MONITOR-API.md` (how to query state without re-reading files)

## What landed since the last m20 attempt (2026-05-23 revert)

- **#2264** (writer prompt): `INJECT_ACTIVITY` is inline-only contract. Workbook activities have NO inject marker. m20's "all 10 inline / 0 workbook" failure mode is now blocked at the writer-prompt level.
- **#2265** (mdx-assembler): inline activities stay in Tab 3 with cross-ref to lesson location. The previous "Tab 3 empty because all inline" failure mode is closed.
- **#2272** (learner_state): plan-based fallback for not-yet-built modules. For m20, learner-state will read m01-m19 plans (NEW vocabulary targets) → derives a real cumulative_vocabulary for the immersion band. Verify on the smoke run that `{LEARNER_STATE}` resolves to a non-empty list.
- **#2263** (wiki): ext-article-N stub backfill — Tab 4 wiki resolution upstream improvements.
- **#2262** (runtime): codex dispatch stdin/probe/finalize unified — your dispatch should now have a clean stdin handshake.

## Verifiable claims preamble (#M-4)

Every claim in the PR description and finalize comment MUST be tool-backed. Quote raw output (command + cwd + final-line). Forbidden phrasings: "looks good", "ship-ready", "all checks pass" without the exact `pytest`/`ruff`/`gh pr checks` output.

| Claim | Required evidence |
|---|---|
| "Build succeeded" | `v7_build.py` exit code 0 + `module_done` event in monitor log |
| "10-check verify passes" | This brief's §4 checklist with PASS/FAIL per row, EACH FAIL having a fix or an explicit deferred-issue link |
| "Tab 4 has no metadata leak" | `grep -E 'chunk_id|retrieved chunk|writer telemetry' curriculum/l2-uk-en/a1/my-morning/my-morning.mdx` → empty |
| "INLINE 4-6 / WORKBOOK 6-9 respected" | `grep -c 'INJECT_ACTIVITY' curriculum/.../my-morning/my-morning.md` (inline count) + `wc -l curriculum/.../my-morning/activities.yaml` (workbook count) — quote raw |
| "Vocab in range" | `python -c "import yaml; print(len(yaml.safe_load(open('curriculum/.../my-morning/vocabulary.yaml'))))"` — 25-40 inclusive |
| "Lint clean" | `.venv/bin/ruff check scripts curriculum` final summary line |
| "Tests pass" | `.venv/bin/python -m pytest tests/test_yaml_activities_v7_types.py tests/test_v7_build_reviewer_assert.py -q` final summary line |
| "CI green on PR" | `gh pr checks <N> --watch --interval 10` final summary, plus `gh pr view <N> --json statusCheckRollup` parsed for `conclusion=="SUCCESS"` per check |

## Steps (numbered, do in order)

1. **Dispatch worktree setup** (delegate.py handles this; verify):
   - `pwd` → should be `.worktrees/dispatch/codex/a1-m20-anchor-2026-05-26/` or similar
   - `git rev-parse HEAD` → should match `origin/main` HEAD at brief read time (verify on first turn)
   - If `.venv` or `data/` symlinks are missing (see issue #2275), STOP and surface — do not work around.

2. **Pre-build read**:
   - `cat curriculum/l2-uk-en/plans/a1/my-morning.yaml` — confirm v1.2.3 + presence of `targets.new_vocabulary`
   - `cat docs/best-practices/v7-design-and-corpus.md | sed -n '180,260p'` — re-read §4 + §5 (known-broken list)
   - `cat docs/best-practices/ulp-presentation-pattern.md | sed -n '17,150p'` — re-read the 7 practices

3. **Fire the build** (writer = claude-tools default, build runs in its OWN worktree per PR #1952):
   ```bash
   # venv symlinked into the dispatch worktree by _provision_data_symlinks per #2275
   .venv/bin/python -u scripts/build/v7_build.py a1 my-morning --worktree 2>&1 | tee build.log
   ```
   - Exit code 0 required to proceed. If non-zero: capture last 50 lines, name the failure event (writer_correction_unparseable / reviewer_fixes_anchor_unmatched / phase_done with failed_dim / etc.), STOP and report.
   - Build wall-clock estimate: 15-25 min on claude-tools at A1.

4. **Run §4 ten-check verify-before-promote** (manual, MANDATORY):
   Render the MDX locally + cross-check each row. The exact rubric is in `docs/best-practices/v7-design-and-corpus.md` §4. The table format your finalize comment MUST include:

   | # | Check | Result | Evidence |
   |---|---|---|---|
   | 1 | All 4 tabs render | PASS/FAIL | `curl -s http://localhost:4321/a1/my-morning/ \| grep -c '<TabItem'` ≥ 4, or local astro-build output |
   | 2 | Tab 3 (Activities) has content or correct fallback | PASS/FAIL | `awk '/TabItem.*Activities/,/TabItem.*Resources/' my-morning.mdx \| wc -l` |
   | 3 | Tab 4 cites the corpus pulls — **NO metadata leak** | PASS/FAIL | `grep -E 'chunk_id\|retrieved chunk\|writer telemetry' my-morning.mdx` → empty |
   | 4 | Inline + aggregate cross-refs (P2) appear | PASS/FAIL | Each inline activity also rendered in Tab 3 with `(see lesson, §...)` |
   | 5 | Student-aware framing visible | PASS/FAIL | No unintroduced vocab; no "the student must learn..." abstraction; learner addressed as "ти/ви" or by named persona |
   | 6 | INLINE 4-6 / WORKBOOK 6-9 (A1 ten-total) | PASS/FAIL | `grep -c INJECT_ACTIVITY my-morning.md` for inline; activities.yaml count for workbook |
   | 7 | Activity types allowed at A1 | PASS/FAIL | Cross-check types against `linear-review-dim.md` placement matrix |
   | 8 | Tab 2 (Vocab) has FlashcardDeck + VocabCards | PASS/FAIL | `grep -E 'FlashcardDeck\|VocabCards' my-morning.mdx` |
   | 9 | Dialogues use `<DialogueBox>` or `> ` blockquotes | PASS/FAIL | `grep -c '<DialogueBox\|^>' my-morning.md` |
   | 10 | IPA where phonetic_rules require | PASS/FAIL | For m20 specifically: `[с'':а]` for `-шся`, `[ц'':а]` for `-ться` (per plan's grammar block) |

   **If any check fails → no promote.** Fix root cause (writer-prompt edit, mdx-assembler patch, plan correction) — do NOT lower the check. If the fix is outside m20's scope (touches shared pipeline code), file an issue, STOP the m20 ship, and report. Do NOT ship a half-fixed module.

5. **ULP 7-practices fidelity check** (extension of §4 check 5 — A1-specific):
   - Practice 1 (em-dash gloss): all UK terms in EN narration follow `UK — EN` pattern. Grep `the .* is .*` in MDX for EN-first violations.
   - Practice 2 (side-by-side bilingual for ≥3-sentence narrative): if Tab 1 has a "Мій ранок" review story ≥3 sentences, it should be side-by-side, NOT single-column.
   - Practice 3 (stress marks): every multi-syllable UK term marked. Use grep for unstressed multi-syllable Cyrillic outside code blocks. Spot-check ~20 terms.
   - Practice 4 (UK-only dialogues): Tab 1 dialogues have NO interleaved EN per turn. Translation table follows the dialogue if needed.
   - Practice 5 (UK-only Q&A): Tab 3 comprehension stems + answer options are Ukrainian-only. EN appears only in activity UI labels.
   - Practice 6 (translate→workbook): NO EN→UK translate prompts in Tab 1 prose. If present, those belong in Tab 3 workbook.
   - Practice 7 (named persona): Tab 1 narration is voiced from a named teacher persona or named dialogue characters (the plan names Ліна + Настя as the dialogue speakers — use them).

   Quote 2-3 verbatim MDX excerpts per practice as evidence. If any practice fails for a structural reason (writer prompt didn't surface it), root-cause and decide: fix root + rebuild, OR ship with explicit follow-up issue (NOT a justification, an issue with a fix plan).

6. **Tests + lint**:
   ```bash
   # venv symlinked per #2275 (Phase 2 prerequisite)
   .venv/bin/python -m pytest tests/test_yaml_activities_v7_types.py tests/test_v7_build_reviewer_assert.py tests/test_learner_state_v7_layout.py -q
   .venv/bin/ruff check scripts curriculum
   ```
   Quote final summary lines. ALL must be green to proceed.

7. **Smoke verify the learner_state plan-fallback worked** (#2272 consumer):
   ```bash
   # venv symlinked per #2275 (Phase 2 prerequisite)
   .venv/bin/python -c "from scripts.pipeline.learner_state import _load_vocab; print(len(_load_vocab('a1', 'happy-numbers')))"
   ```
   For m20 the pre-build state should reflect m01-m19 cumulative vocab from plans — not zero, not the entire VESUM. Spot-check that `compute_immersion_band` returned a sensible band (e.g. `advisory_pct_min ≥ 30`, `advisory_pct_max ≤ 60` for mid-A1).

8. **Commit + push + PR**:
   - Commit message: `feat(a1): publish m20 my-morning anchor module — reflexive verbs A1.3`
   - Body MUST include:
     - The §4 ten-check table with raw evidence per row
     - The ULP 7-practices fidelity findings
     - `gh pr view <N>` URL
     - Reference: `closes none / anchor build for follow-on m01-m19 + m21-m55`
   - `git push -u origin codex/a1-m20-anchor-2026-05-26`
   - `gh pr create --title "feat(a1): publish m20 my-morning anchor module" --body @PR_BODY.md`
   - DO NOT auto-merge. Orchestrator (Claude main) will merge after reviewing the body.

## Hard constraints (will block merge)

- **NO Tab 4 metadata leak.** Strings `chunk_id`, `retrieved chunk`, `writer telemetry`, `wiki_query_id`, `vesum_query_id` MUST NOT appear in the rendered MDX. This was the 2026-05-23 revert root cause. The mdx-assembler is the right layer to fix if it leaks; the writer prompt is the layer to fix if the writer itself emits these in prose.
- **INLINE 4-6 / WORKBOOK 6-9 (10 total).** Per `linear-review-dim.md:128`. NOT 10 inline / 0 workbook. NOT 0 inline / 10 workbook. The split is a pedagogical requirement.
- **Vocab 25-40 lemmas.** Below 25 = under-target. Above 40 = lemma overload at A1. The plan's `targets.new_vocabulary` (12 deduped) + `vocabulary_hints.required` (7) + `vocabulary_hints.recommended` (8) gives 27 candidates — that's the minimum floor. Writer may surface a few more from textbook chunks; 40 is the ceiling.
- **NO transliteration tables, NO "X sounds like Y in English"** (ULP Practice 1+3 violation, mid-S1 baseline).
- **NO EN-first reflexive-verb explanation.** The grammar block in Tab 1 must present UK form first, then gloss, then rule. The Захарійчук Grade 1 textbook chunks named in the plan (p.24 + p.52) are the grounding.
- **Word-count target 1200 minimum.** This is a MINIMUM per non-negotiable-rules §1. 1200-1400 expected.

## Stop conditions (STOP and surface, do not work around)

1. `.venv` or symlinks missing in dispatch worktree (issue #2275). The 10-check Tab 1 render needs Python + Node tooling.
2. Build exits non-zero with `writer_correction_unparseable` or `reviewer_fixes_anchor_unmatched` more than 2x — that's a writer-prompt or reviewer-prompt bug, not a content issue. File an issue with the raw failure event, STOP m20 ship.
3. After 3 rebuild cycles, §4 check 6 (split) still fails or §4 check 3 (Tab 4 leak) still fails — the writer-prompt or mdx-assembler still has a regression that #2264+#2265 didn't fully close. File a follow-up issue, STOP, do NOT ship.
4. Any §4 check fails for a reason that requires editing `scripts/build/phases/linear-write.md`, `scripts/build/phases/linear-review-dim.md`, or `scripts/generate_mdx/core.py` — those are SHARED pipeline files. Surface the diagnosis as an issue, STOP m20 ship until orchestrator decides.

## Output format (finalize comment in PR)

```markdown
## a1/m20 anchor build — finalize summary

### Build
- v7_build.py exit: 0
- Wall clock: <Nm Ms>
- Final monitor event: `{"event": "module_done", "level": "a1", "slug": "my-morning", ...}`
- Telemetry: `audit/build-a1-my-morning-<stamp>/...`

### §4 ten-check (verbatim per row, with command + cwd + raw output)
[table per row 1-10 with PASS/FAIL + evidence — see §4 above]

### ULP 7-practices fidelity (A1 S1 baseline)
[verbatim MDX excerpts per practice]

### Tests + lint
- pytest <files>: <N passed in Xs>
- ruff: <All checks passed!>

### Vocab count + lemma evidence
- Vocab count: <N> (target 25-40)
- New lemmas surfaced from plan targets.new_vocabulary: <list>
- New lemmas surfaced from textbook chunks (citations): <list>

### Follow-ups filed
- [link to any deferred-fix issues filed during the build]

### Diff summary
- Files changed: <N>, +<X>/-<Y>
- Primary artifacts:
  - curriculum/l2-uk-en/a1/my-morning/my-morning.md (+<W> words, <X> sections)
  - curriculum/l2-uk-en/a1/my-morning/my-morning.mdx (rendered)
  - curriculum/l2-uk-en/a1/my-morning/vocabulary.yaml (<N> lemmas)
  - curriculum/l2-uk-en/a1/my-morning/activities.yaml (<workbook count> workbook activities)
  - curriculum/l2-uk-en/a1/my-morning/resources.yaml (Tab 4 source)
  - curriculum/l2-uk-en/a1/my-morning/status.json (gate results)
```

## Done criteria

- v7_build.py exit 0 + `module_done` monitor event present
- §4 ten-check all-PASS or explicit follow-up issue cited per FAIL
- ULP 7-practices fidelity report with verbatim MDX evidence
- pytest + ruff green (commands + outputs quoted)
- PR opened, body matches the output format above
- DO NOT auto-merge; tag the orchestrator handle in PR body if available

## Estimated cost

- Wall clock: 25-50 min (build 15-25m + verify 10-25m)
- Codex weekly: minimal (single dispatch, xhigh effort)
- Claude weekly: 0 directly; m20 build consumes the writer-budget (claude-tools default) which sits on the dispatched-Claude lane

---

**Anchor build mantra**: this is the reference build. m21-m55 + m01-m19 + all of A2 will pattern-match against m20's MDX. A 95%-right anchor that ships fast is WORSE than a 99%-right anchor that takes one extra rebuild cycle. Don't ship until §4 + ULP fidelity both clear.

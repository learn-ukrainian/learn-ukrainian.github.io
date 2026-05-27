# Codex brain-pick on m20 failure modes — turn 1

**Session UUID:** `019e6944-d4c8-7da0-853f-8676ddf526b0`
**Path:** `~/.codex/sessions/2026/05/27/rollout-2026-05-27T13-49-39-019e6944-d4c8-7da0-853f-8676ddf526b0.jsonl`
**Mode:** `codex exec -m gpt-5.5 -s read-only`
**When:** 2026-05-27 ~13:49 UTC (mid-orchestration; v7-prompt-hardening dispatch in flight at the time).
**Purpose:** Get codex's writer's-eye view of why m20 (PR #2364) shipped with 6 substantive failure modes despite all-green gates.

## Three critical findings (orchestrator action items)

### F1 — `scripts/audit/config.py:53` whitelists BOTH `Квак` AND `Кнак`

The typo proper noun is whitelisted as a valid name. The new HARD `verify_quote` gate (gemini dispatch `v7-verify-quote-gate-2026-05-27`) will catch the m20 instance by comparing to source text not name validity, but the whitelist entry is its own bug.

**Action:** Follow-up PR to purge `Кнак` from the whitelist. Investigate when/why it was added (post-hoc silence during a correction loop = #M-11 anti-pattern; pre-existing = inherited data error).

### F2 — Plan-stage / writer-prompt conflict on Grade 1 references

`curriculum/l2-uk-en/plans/a1/my-morning.yaml:112` REQUIRES Grade 1 references in the plan. `scripts/build/phases/linear-write.md:129` requires 30-word published blockquotes for each plan reference. My new `#R-NO-CHILDREN-PRIMARY-QUOTES` rule (in flight via codex dispatch) forbids Grade 1 quotes in published body. **The three constraints can't all hold.**

**Action:** Resolution requires separating "internal grounding" (writer reads + cites in `<verification_trace>`) from "published blockquote" (learner-visible). Either:
- Plan stage starts requiring `grade_7_or_above` for any reference that becomes a published blockquote, with `any_grade` allowed for internal grounding only, OR
- Writer prompt's "30-word blockquote per plan reference" rule is loosened to "internal cite OR published blockquote depending on source grade," OR
- Plan schema gets a new field distinguishing the two roles.

The codex dispatch in flight will likely surface this conflict in its PR body. Address in follow-up PR.

### F3 — "Rendered-lesson pass" pre-emission self-check

Codex's strongest design proposal: before the writer emits, do a final pass simulating a learner reading only `module.md` (no comments, no source machinery). Delete anything addressed to writer, reviewer, teacher, or gate. Would have caught:
- `Крок 5` at line 133
- The register jump from line 20 → line 30

**Action:** Decide layer placement. Three options:
- (a) Writer-prompt rule (`#R-RENDERED-LESSON-SELF-CHECK`): writer self-checks before emission.
- (b) New deterministic pipeline phase between write + review: regex-detect writer-scaffolding patterns (`Крок-N`, panel IDs, obligation names, gate-language) in published `module.md` and fail fast.
- (c) Reviewer-side check scoring "would a learner reading only `module.md` hit anything they shouldn't."

My instinct: (b) catches the regex-able cases cheaply; (a) for harder register-shift cases (LLM judgment). Follow-up turn 2 to codex asks for confirmation.

## Codex's full Q1-Q3 analysis (verbatim, lightly reformatted)

### Q1 — Writer's-eye view of 17 rounds: what felt structurally hardest

> The structurally hardest part was not teaching `-ся`; it was satisfying many local gates whose rewards were independent. The prompt made the writer optimize for "**visible compliance tokens**":
>
> - `word_count`: satisfiable by adding prose mass, not better teaching. (`linear-write.md:252`)
> - `l2_exposure_floor`: satisfiable by emitting 15 countable `<DialogueBox>` lines, even if dialogue rhythm is flat. (`linear-write.md:299`)
> - `engagement_floor`: satisfiable by one callout, even a tonal outlier like `module.md:35`.
> - `wiki_coverage_gate`: **most dangerous.** The prompt says to populate each implementation-map row at its location and not invent structure; that rewards literal labels and row satisfaction over lesson flow. (`linear-write.md:171`, `module.md:133` leaked `Крок 5`.)
> - `textbook_grounding`: forced real source retrieval, but also forced pasted blockquotes. The 30-word requirement at `linear-write.md:129` made the child-primer register likely.
> - `decolonization`: after the bad-form marker rule, satisfiable by one marked contrast plus a stance line. `module.md:29` is useful; `module.md:30-31` are the overfit.
>
> Gates that forced real teaching: VESUM on emitted forms, the `-ся` trap warning at `linear-write.md:83`, wiki obligations when the treatment template demanded an example sentence rather than a label.

### Q2 — Failure-mode mapping by best layer

| Failure | Best layer |
| --- | --- |
| 1. Salad/kaleidoscope register | Writer rule + reviewer REJECT. A writer rule alone is too easy to "intend"; reviewer must reject mid-module shifts under tone/register. Current reviewer says tone assesses consistency at `linear-review-dim.md:96`, but it needs explicit rejection language. |
| 2. Ukrainian instruction language to A1 | Writer rule + reviewer REJECT, maybe a narrow heuristic gate for A1 narrator imperatives. Current prompt only says English is for scaffolds at `linear-write.md:287`; needs the hard A1 audience-language rule. |
| 3. "Thing/action" paraphrase | Writer rule + pedagogy reviewer. Use "noun/verb" with simple examples. |
| 4. Proper-noun quote typo | **Hard gate.** Don't rely on VESUM or whitelists. **Wrinkle**: `config.py:53` currently whitelists both `Квак` and `Кнак`, so the new gate must compare attributed text to source text, not name validity. |
| 5. `Крок 5` scaffolding leak | Writer rule + deterministic formatting gate. Regexable: reject `Крок N:`, `Step N:`, obligation IDs, gate names in published `module.md`. |
| 6. Grade 1 blockquotes | **Cross-cutting.** Plan requires Grade 1 references at `my-morning.yaml:112`; writer prompt currently requires published 30-word blockquotes for each plan reference. `#R-NO-CHILDREN-PRIMARY-QUOTES` conflicts with that unless grounding gate allows internal/source grounding without learner-facing child blockquotes. |

### Q3 — Fresh m20 differently

> Fresh m20: choose **one carrier voice before writing** — adult English explanation, Ukrainian only as target language. No Ukrainian narrator imperatives, no third-person "student" framing, no moralized anti-Russian prose.
>
> Avoid `module.md:30` entirely. Replacement shape:
> > Use **сніданок** for the noun and **снідати** for the verb. For the common Russian-influenced form, keep one contrast: **сніданок**, not `<!-- bad -->завтрак<!-- /bad -->`.
>
> Replace `module.md:35` with:
> > **Noun vs verb:** **сніданок** names the meal. **снідати** names the action: **Я снідаю о восьмій.**
>
> Don't publish the Grade 1 blockquotes at `module.md:55` or `module.md:95`. Use as grounding only, then teach from adult-neutral model sentences.
>
> **Final "rendered lesson pass" before emission:** strip comments and source machinery, read only `module.md`, delete anything addressed to writer, reviewer, teacher, or gate. That one pass would have caught `Крок 5` at line 133 and the register jump from lines 20 to 30.

## Notes for next-session orchestrator

- This conversation is reachable for follow-up turns via:
  ```
  .venv/bin/python scripts/ai_agent_bridge/__main__.py send-codex-ui \
    --thread 019e6944-d4c8-7da0-853f-8676ddf526b0 \
    "<follow-up message>"
  ```
- The in-flight codex dispatch (`v7-prompt-hardening-2026-05-27`, session `019e693d-...`) is a SEPARATE thread; do not confuse the two.
- Codex's "visible compliance tokens" framing is the clearest articulation of the salad/kaleidoscope root cause. Each gate was a knob; the writer hit the knobs without integrating. Worth encoding in MEMORY.md when there's space.

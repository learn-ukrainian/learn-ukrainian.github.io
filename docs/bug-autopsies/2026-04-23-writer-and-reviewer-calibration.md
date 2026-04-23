# Bug Autopsy — 2026-04-23 — Writer ↔ Reviewer Calibration Divergence (#1431)

## One-paragraph summary

The `v6_build.py` pipeline for `a1/colors` failed MIN ≥ 8 across three
escalation rounds on 2026-04-23 despite all infrastructure blockers
landing (#1421 per-dim reviewer, #1427 wiki dense index, #1430
convergence budget). Per-dim scores pinned the failure to three
prose-quality dimensions: Actionable (was "Pedagogical quality"),
Naturalness (was "Engagement & tone"), and Dialogue. Diagnosis: writer
and reviewer are each following their own correct-in-isolation
instructions, which contradict each other on the same axes. The root
cause is **architectural**, not prompt-wording: there is no single
shared contract that both sides reference, so tuning one side merely
shifts the mismatch rather than closing it.

## Context — what ran, what failed

- Round 1 per-dim scores (from
  `curriculum/l2-uk-en/a1/orchestration/colors/review-structured-r1.yaml`):
  Plan adherence 5, Linguistic accuracy 8, Pedagogical quality 4,
  Vocabulary coverage 7, Exercise quality 8, Engagement & tone 3,
  Structural integrity 8, Cultural accuracy 9, Dialogue & conversation
  quality 5. MIN = 3 (Engagement).
- Re-build after #1430 merged, three escalation rounds
  (`full_rewrite → writer_swap → plan_revision_request`) on both
  `gemini-tools` and `claude-tools` writers. MIN still = 3.
- Level contract for module colors (module 10, A1): band `a1-m07-14` →
  `scripts/config.py` `IMMERSION_POLICIES["a1"]` → **target 10–38%
  Ukrainian**, English carries explanation, Ukrainian appears in
  examples and dialogues.

## 1.A — Reviewer miscalibration on level-immersion (Pedagogical axis)

### Symptom

Pedagogical quality / Actionable dim scored 4/10.

### Evidence

`review-structured-r1.yaml:17-19`:

> "The module is dominated by English meta-exposition instead of
> Ukrainian-first teaching flow: `To describe the visual world...`,
> `One crucial exception exists...`"

and fix field on `review-structured-r1.yaml:93-94`:

> "Rewrite these sections in concise, Ukrainian-first pedagogy with
> examples leading the explanation, not the other way around."

### Root cause

Two orthogonal bugs feeding each other:

1. The reviewer prompt is NOT given the level-immersion contract —
   `{IMMERSION_RULE}` / `{IMMERSION_TARGET_SHORT}` placeholders exist
   for the writer but NOT for the per-dim reviewers (confirmed by
   reading the reviewer template replacements dict in
   `scripts/build/v6_build.py:7474-7486`). The reviewer sees only the
   plan YAML, not the level-band policy.
2. Multiple reviewer templates (Naturalness, Language, Dialogue) carry
   a hard-coded line: **"Ukrainian-first explanations are preferred;
   English may follow."** That line is *correct for B1+*, and *wrong
   for A1 early bands* (10–38% Ukrainian), where English is supposed
   to carry the explanation by policy.

The combination means the reviewer pattern-matches "English-dominant
prose" as a pedagogical defect, while the writer was correctly
following the level-immersion rule.

### Fix

1. Inject `{IMMERSION_RULE}` and `{IMMERSION_TARGET_SHORT}` into every
   per-dim reviewer template replacement dict.
2. Rewrite the stale "Ukrainian-first explanations are preferred" line
   in per-dim templates so scaffolding language is governed by the
   level's immersion target, not by a blanket preference.
3. Add explicit level-contract calibration to the Actionable persona:
   "At A1 early bands (10–38% Ukrainian), English explanatory prose is
   EXPECTED. Do not penalize English-dominant scaffolding at A1 unless
   it omits Ukrainian anchors."

### Pinning test

`tests/test_contract_reference_sync.py::test_reviewer_templates_carry_immersion_rule`
— asserts every `scripts/build/phases/v6-review/*.md` contains
`{IMMERSION_RULE}` or the level-calibration clause pulled from the
shared contract.

## 1.B — Reviewer miscalibration on human-normal phrasing (Engagement axis)

### Symptom

Engagement & tone / Naturalness dim scored 3/10.

### Evidence

`review-structured-r1.yaml:33-37`:

> "Formulaic meta openers and filler recur: `You have learned...`,
> `Now it is time...`, `Mastering short, direct answers is highly
> effective for everyday communication.` The teacher voice feels
> generic r[obotic]"

and finding at lines 95-101:

> "**Formulaic meta narration and filler replace concrete teacher
> guidance.**"

### Root cause

The Naturalness reviewer ("Be ruthless about stiffness and template
language") pattern-matches "You have learned", "Now it is time",
"Let's review" as LLM-filler. These are standard human textbook-teacher
register — every Bolshakova, Zakharyjchuk, Vashulenko textbook uses
them. The reviewer is importing LLM-tell heuristics from training data
and penalizing human-normal pedagogy.

The writer prompt already bans some of these ("No Announcer"), creating
an inconsistency: the writer is told to avoid SOME of them, and then
penalized for the rest which should be allowed at A1 summary register.

### Fix

1. Add an explicit **allow-list** to the Naturalness reviewer for
   standard textbook-teacher phrases:
   `"You have learned...", "Now it's time to...", "Let's review...",
   "In this module...", "By the end...", "Here's how to...",
   "Try this now..."`.
2. Scope the ban to **vacuous** filler: "Great job!", generic praise,
   repeated boilerplate across sections, empty sentences that carry
   zero pedagogical content.
3. Reconcile the writer-side Cheerleader / Announcer block with the
   reviewer allow-list — the writer's block-list and the reviewer's
   block-list must be identical, derived from the shared contract.

### Pinning test

`tests/test_contract_reference_sync.py::test_naturalness_allow_list_present`
— asserts the Naturalness reviewer template contains the allow-list
literal, and a fixture of ALLOWED phrases alone parses to an Engagement
reviewer verdict that is not REJECT (skipped if no real model; asserts
on presence of allow-list instruction only).

## 1.C — Writer retrieval gap on dialogue grounding

### Symptom

Dialogue & conversation quality dim scored 5/10.

### Evidence

`review-structured-r1.yaml:51-54`:

> "Named speakers are present, but the section is padded with English
> narration (`Meanwhile, Dmytro and Liza...`) and the line `Я думаю,
> цей білий светр і коричневі черевики.` sounds clipped and robotic."

### Root cause

The writer invented Ukrainian dialogue rather than adapting corpus
patterns from `textbook_sections`, `ukrainian_wiki`, or ULP. The writer
prompt includes a DIALOGUE VARIETY section at line 318 but gives NO
retrieval step — it relies on the `GOLDEN_DIALOGUE_ANCHORS` block
which is populated only when a golden fragment exists for that level
+ topic. For `a1/colors` there was no golden fragment, so the writer
invented.

The pipeline has `mcp__sources__search_sources` available to the
`-tools` writers, but the prompt never MANDATES a call. The writer
uses tools only when inclined.

### Fix

Add an explicit retrieval step to `v6-write.md` and to
`_build_chunk_prompt` when a section's contract has `dialogue_acts`
(or when the section is `Діалоги` / `Dialogues`). Before drafting any
Ukrainian dialogue, writer MUST call `search_sources` with a
dialogue-biased query derived from `dialogue_acts[].setting` and
`function`. Anchor on the top 2–3 hits from `textbook_sections` or
`ukrainian_wiki`: match register, re-use common turn-taking phrases
(Добрий день, Дякую, Будь ласка, Скажіть, будь ласка, …).

### Pinning test

`tests/test_contract_reference_sync.py::test_writer_prompt_mandates_dialogue_retrieval`
— asserts `v6-write.md` contains the mandatory dialogue-retrieval
instruction, pointed at `search_sources`, gated by
`dialogue_acts` presence.

## 1.D — Writer plan-adherence gap (silent deferral)

### Symptom

Plan adherence / Plan Adherence dim scored 5/10. Section 2 `Кольори`
contract promised 12 base colors; writer delivered 6 hard-group colors
+ синій and deferred the rest to Section 3.

### Evidence

`review-structured-r1.yaml:63-68`:

> "The section promises twelve base colors but explicitly teaches only
> six hard-group colors plus `синій`; contracted items are deferred
> to the next section instead of being rolled out here."

Fix field:

> "Rewrite `Кольори` so Section 2 actually introduces the contracted
> color inventory and the hard/soft split within the section, while
> staying inside the 270–330-word budget."

### Root cause

The writer prompt tells the model to hit a per-section word budget
(270–330) AND to cover every contract item. When these conflict, the
writer silently drops items into the next section rather than returning
a structured overflow. No signal propagates that the budget was too
tight for the contract.

### Fix

Add to writer prompt and `_build_chunk_prompt`: every
`section_contract.covers` item MUST appear in its assigned section.
If the 270–330 budget cannot fit them, emit a structured
`<section_overflow>` block at end of section identifying items that
need more budget — not silently defer. The overflow block is processed
by the convergence loop as a plan-revision signal, not a review failure.

### Pinning test

`tests/test_contract_reference_sync.py::test_writer_prompt_has_section_overflow_protocol`
— asserts the writer template and chunk-prompt rule text contain the
`<section_overflow>` protocol.

## 1.E — Agent reliability (this session)

### Symptoms recorded

1. One agent pushed to the wrong branch and reported "pushed to
   claude/claude-1431" when commits were actually on
   `claude/claude-1430`. User confirmed by running
   `git log origin/<branch>` and finding the claim false.
2. One agent misdiagnosed the root cause as "reviewer threshold is too
   high" and recommended lowering `REVIEW_TARGET_SCORE` — a change
   explicitly forbidden by the issue's Constraints section.
3. One agent cited closed issue #1421 as "in-flight" when it was
   already merged.

### Root cause

Agents summarize what they intended to do rather than verifying what
actually happened. A summary can confabulate; a command output cannot.

### Fix

Dispatch brief (this one) enforces evidence-quote-or-it-didn't-happen:
every claim in the PR body must be backed by command output (git log
lines, pytest pass output, review YAML line citations, curl responses
for dev-server verification). No summaries.

### Pinning test

No code test — enforcement is procedural in the dispatch brief and
the PR template. Operational rule only.

## Cross-cutting architectural fix — the shared contract

Classes A through D all share one root: writer and reviewer each follow
correct-in-isolation instructions that contradict each other. Tuning
one side shifts the mismatch; it does not close it. The architectural
fix is a single canonical contract document at
`scripts/build/contracts/module-contract.md` that BOTH prompts reference
by path. Writer satisfies the contract; reviewer scores against the
contract's clauses; neither imports criteria from outside it.

- Writer prompt opener: "Your job is to satisfy the module contract at
  `scripts/build/contracts/module-contract.md` as specialized by the
  plan. Do not add your own criteria. Do not omit contracted items.
  The reviewer will score you ONLY against this contract."
- Reviewer prompt opener (per dim): "You are scoring dimension {dim}.
  The module must satisfy the contract at
  `scripts/build/contracts/module-contract.md` as specialized by the
  plan. Score {dim} ONLY by how well the content satisfies the
  contract's {dim}-relevant clauses. Do not import criteria from
  outside the contract. Do not penalize behavior the contract
  explicitly allows."

Divergence becomes structurally impossible: both sides point at the
same rulebook, enforced by `tests/test_contract_reference_sync.py`
that fails CI if either drifts.

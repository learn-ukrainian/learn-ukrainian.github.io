# Review-and-Lock: Wiki + Plan

> **Purpose.** Bring a `(wiki, plan)` pair to a known-clean, reproducible state that the build pipeline (A.8 canary, A.9 scale batch, module build) can trust as input. "Locked" means: the two artifacts have passed a structured review, every cited dictionary fact is traceable, the plan directs the writer toward the wiki's content (not away from it), and the pair is clearly marked so future agents know not to re-litigate it without cause.
>
> **Scope.** L2-UK-EN A1 and A2 tracks. 54 slugs in A1, ~54 in A2. This document is the template the remaining 106 (wiki, plan) pairs follow.
>
> **Worked example.** `at-the-cafe` (L2-UK-EN A1/M38). PR #1412.

---

## When to apply this procedure

Run review-and-lock when **any** of the following is true:

- The slug is the target of an upcoming build (canary or scale batch) and has not yet been locked.
- The latest wiki review is below 9/10 on any dimension, OR older than 30 days and content has since been edited.
- The plan has never had an adversarial review (`lifecycle: <unset>` or absent).
- A systemic audit (e.g. #1392) flagged a class of defects that could plausibly hide in this pair.
- A prior locked review has been invalidated by one of the **unlock triggers** below.

Do **not** re-lock a slug that is already `lifecycle: locked` and current unless one of the above applies. Locking is expensive; the point is to stop re-reviewing.

---

## Step 0 — Intake (5–10 min)

Read, in order, before touching any file:

1. `wiki/pedagogy/{level}/{slug}.md` — the current wiki
2. `wiki/pedagogy/{level}/{slug}.sources.yaml` — the source registry (sidecar)
3. `wiki/.reviews/pedagogy/{level}/{slug}-review-*.md` — all prior review rounds, newest first
4. `curriculum/l2-uk-en/plans/{level}/{slug}.yaml` — the plan
5. Any GitHub issue driving this lock (e.g. #1412). The issue's AC list overrides this template when in doubt.
6. The most recent systemic plan-audit issue (e.g. #1392). If a defect class is known, this pair is **not** exempt — check explicitly.

**Do not skip the review history.** A current wiki may have been re-compiled after the final review, meaning the documented gaps may or may not still be present. Re-read and verify against the actual file state.

---

## AC-1 — Wiki to ≥9/10 (the 5-dimension rubric)

### The rubric

Score each dimension 1–10. All five must be ≥9 to lock. The thresholds and rationales are the same as the standard wiki review rubric used in `wiki/.reviews/.../*.md`:

| # | Dimension | Focus | Auto-cap trigger |
|---|-----------|-------|------------------|
| 1 | **Factual accuracy** | Every claim sourced (inline citation or `sources.yaml` entry). Vague / unsourced claims → deduct. | ≤ 7 if any claim references a source that doesn't support it. |
| 2 | **Ukrainian language quality** | Russianisms (кон→кін), Surzhyk (шо→що), calques (приймати душ→брати душ), paronyms. Four **separate** checks. | ≤ 7 if ANY Russianism in instructional text. |
| 3 | **Decolonization** | Ukrainian on its own terms. No "like Russian but..." framing. Russian-origin calques explicitly named when discussed. | ≤ 6 if any "like Russian" comparison. |
| 4 | **Completeness** | Covers all aspects a module writer needs: sequence, core dialogue, modern pragmatics, L2-specific errors, vocab boundaries. | ≤ 7 if a writer would have to invent a section that should exist. |
| 5 | **Actionable guidance** | A writer can lift sentences directly. Generic advice ("teach it well") does not count. | ≤ 5 if section is pure high-level strategy. |

### Checklist for AC-1

1. **Apply any outstanding `<fixes>` block** from the latest review round (check `git log -p` on the wiki to confirm they haven't already landed — compilation regenerates files and can silently drop fixes).
2. **Close documented gaps** (the specific deficits named in the review's dimension-4 and dimension-5 deductions). These are typically 1–3 items per round.
3. **Verify every new vocabulary item**. Four-authority hierarchy from `.claude/rules/ukrainian-linguistics.md`:
   - **VESUM** (`data/vesum.db`, or MCP `mcp__sources__verify_word` / `verify_lemma`) — does this word form exist?
   - **Правопис 2019** (MCP `query_pravopys`) — orthography edge cases
   - **Горох** / stress dictionary — pronunciation
   - **Антоненко-Давидович** (`data/sources.db` `style_guide` table, MCP `search_style_guide`) — is it a calque?
   - **Грінченко** — historical / etymology
4. **If a right-column Surzhyk replacement cannot be verified in at least VESUM + СУМ-11**, do NOT add it — flag with `<!-- VERIFY -->` instead. Hallucinated café vocab breaks the whole drill.
5. **Emit a LOCKED review file** at `wiki/.reviews/pedagogy/{level}/{slug}-review-LOCKED.md` with:
   - Per-dimension scores with evidence
   - Overall score
   - Definition of "LOCKED" for this artifact
   - Unlock triggers
   - Residual non-blockers (issues known but below the bar for blocking)
6. **Update the wiki's meta block** with `lifecycle: locked`, `last_reviewed: YYYY-MM-DD`, `reviewed_by: <agent-id>`.

### Escalation

If two rounds of review cannot get the wiki to 9/10 on any dimension:

- Do NOT block the scale batch on this one slug.
- Leave the wiki at its current state (`lifecycle: reviewed`, NOT `locked`).
- Open a follow-up issue labelled `blocked-review-and-lock` with the specific dimension that's stuck and the concrete sub-problem.
- Continue with the next slug.

---

## AC-2 — Plan reviewed + LOCKED

The plan is often less scrutinized than the wiki because it is smaller and appears to "just mirror" the wiki. In practice plans drift in dangerous ways. Check explicitly:

### Plan-review checklist

1. **Pragmatic precision** (per #1392 Defect 2)
   - Context-blind reciprocals: e.g. `А у тебе?` mandated for a name-exchange where only `А тебе?` is natural.
   - Context-inappropriate registers: formal `Ви` in a peer-to-peer setting, or vice-versa.
   - Setting-requirement mismatch: does the `setting` of each `dialogue_situations[]` actually motivate the grammar listed in `grammar:`?
2. **Russianisms in plan prose** (anywhere — `motivation`, `setting`, `points[]`, `focus` strings of activity items)
   - `приймати замовлення` → `брати замовлення`
   - `на винос` → `із собою`
   - `вкусний` → `смачний`
   - `Давайте + 1pl` → synthetic imperative (`-імо`/`-ймо`) — per #1392 Phase 2 Gemini findings
   - Homoglyph scan: Latin letters inside Cyrillic tokens (`ЗМI` with Latin `I`) — per #1392 Phase 2
3. **Calques in `vocabulary_hints`**
   - Every item must pass Антоненко-Давидович silently (no flagged entry in `style_guide`).
   - If a calque appears, either replace with the native form or explicitly mark it as the "wrong" side of a contrast pair the module teaches against.
4. **Plan-internal contradictions**
   - `grammar:` list vs `objectives:` — every grammar item should map to an objective and vice-versa.
   - `content_outline[].words` sum == `word_target` (or close).
   - `activity_hints` cover the `grammar:` targets.
   - `dialogue_situations[].motivation` actually produces the grammar in `grammar:`.
5. **References present and specific**
   - At least one reference that is specific enough to verify (not just "Ukrainian textbooks").
   - If the paired wiki is locked, **add a back-reference** to the wiki in `references:`.
6. **Alignment with locked wiki**
   - Anything new in the wiki (new steps, new vocab) should have a plan-side hook (new activity, new vocabulary_hint, new content_outline point). Otherwise the writer will read the plan and never look at the wiki's new content.

### Apply or VERIFY-flag

For every finding: either fix it directly in the plan, or insert a `<!-- VERIFY: <description> -->` comment in the closest YAML key. Do not leave a finding unaddressed.

### Lifecycle field convention (net-new top-level fields)

Add these keys to the plan YAML (schema `module-plan.schema.json` is `additionalProperties: true`, so no schema change is required):

```yaml
lifecycle: locked              # enum: draft | reviewed | locked
reviewed_at: '2026-04-22T00:00:00Z'   # ISO-8601 UTC
reviewed_by: claude-opus-4-7-xhigh-<issue-number>
review_notes: >-
  Short prose — what was reviewed, what findings, where to see the full
  report (PR body / review file / commit message).
```

Bump the plan's `version` (minor for content addition, patch for fix-only). Add a `changelog` entry describing the review-and-lock pass.

### Escalation

Same rules as AC-1 — if 2 review rounds can't clear blockers, stop at `lifecycle: reviewed` and file a follow-up issue. Do not block the batch.

---

## AC-3 — Cross-pair verification (the drift check)

The most common failure mode at scale is **wiki-plan drift**: wiki says one thing, plan says something subtly different, learner-facing content ends up averaging them. Before declaring the pair locked:

1. Open both files side by side.
2. For each new wiki section / step, confirm a plan-side hook exists.
3. For each plan dialogue, confirm the wiki has an example or pedagogical note that motivates the dialogue's content.
4. Specifically for Surzhyk/calque tables: every pair on the wiki's table should appear as either a quiz item, a fill-in distractor, or a match-up pair in the plan's `activity_hints`.
5. For terminology that differs between wiki and plan (e.g. `кав'ярня` vs `кафе`) — flag as a writer-facing note in the plan, not as a defect. Two standard Ukrainian words are not a drift; two *conflicting* words are.

---

## AC-4 — Adversarial review (Gemini) before PR

Spawn Gemini via the bridge:

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-gemini \
  "Adversarial review of #<N> review-and-lock for <slug> wiki + plan. \
   Read the diff. Look for: \
   (1) wiki fixes that introduce NEW gaps while closing documented ones, \
   (2) lifecycle field naming colliding with existing plan schema fields, \
   (3) plan-review checklist missing categories that the latest systemic audit would have caught, \
   (4) this rubric doc drifting from what was actually applied (worked example must match rubric step-for-step), \
   (5) hallucinated vocab not verifiable in VESUM." \
  --task-id <N>-review --model gemini-3.1-pro-preview
```

Address findings. If non-trivial, a second round is expected — don't short-circuit.

---

## AC-5 — PR + merge

- PR title: `feat(quality): review-and-lock <slug> wiki + plan (#<N>)`
- Do NOT merge the PR yourself. The user merges.
- Do NOT use `gh pr merge --admin`.

---

## Worked example: at-the-cafe (PR #1412)

This section shows the template applied step-for-step. If anything in the rubric above is unclear, the answer is: "do what #1412 did."

### AC-1 (wiki)

- **Prior state.** `wiki/pedagogy/a1/at-the-cafe.md`, last review 8/10 (final review 2026-04-05). Documented gaps:
  1. Modern café vocab: no `тут чи із собою`, no size collocations.
  2. Surzhyk table: generic items (`приймати участь`, `відчиняти двері`) not café-specific.
- **Fixes applied:**
  1. Added **Step 5: Сучасна кав'ярня** with `Вам тут чи із собою?`, sizes `велику каву` / `маленьку каву`, plus minimal dialogue.
  2. Added new **Типові помилки L2 (café-specific Surzhyk)** section with 8 café-specific pairs (счёт/рахунок, на винос/із собою, пірожене/тістечко, кулечок/пакетик, трубочка/соломинка, чашка кофе/чашка кави, вкусна/смачна, приймати замовлення/брати замовлення).
  3. Every right-column token verified in VESUM (`data/vesum.db`). Left-column Russianisms confirmed absent from VESUM (пірожене, кулечок, кофе) or independently flagged in Антоненко-Давидович (приймати X → брати X).
  4. Rewrote "Приклади з підручників" exercise 3 from generic pairs to café-specific ones, so the writer can drill exactly these.
  5. Added writer-note after vocabulary table pinning `велику каву` / `Тут, будь ласка` / `Із собою, будь ласка` as indivisible chunks (prevents the writer from over-teaching adjective declension at A1).
- **LOCKED review file:** `wiki/.reviews/pedagogy/a1/at-the-cafe-review-LOCKED.md`. All 5 dimensions at 9. Overall 9/10. Unlock triggers listed.

### AC-2 (plan)

- **Prior state.** `lifecycle` absent. Never adversarially reviewed.
- **Findings & fixes:**
  - *Pragmatic:* No context-blind reciprocals. (#1392 Defect 2 clean.)
  - *Russianism in prose:* None. Added author-note warning against `Кава на винос` in Діалог 3 description.
  - *Calque in vocabulary:* None in prior state. New additions (`тут`, `із собою`, `велику каву`, `маленьку каву`) all VESUM-verified.
  - *Contradiction:* None. Word-count sum cleanly matches target (300×4 = 1200 = word_target).
  - *References:* Added wiki back-reference.
  - *Wiki-plan alignment:* Plan had no hook for wiki's new Step 5. Closed by adding Діалог 3 (takeaway) + new `content_outline` point under "Як замовити" + extended `vocabulary_hints` + new Surzhyk fill-in activity mirroring the wiki's new table.
- **Lifecycle markers added.** `version` bumped 1.2.2 → 1.3.0. `changelog` entry.

### AC-3 (drift check)

- Wiki Step 5 → plan Діалог 3 + new section-point + new vocab_hints ✓
- Wiki "Типові помилки L2" table → plan new fill-in activity (7 of 8 pairs; `приймати замовлення` left implicit because the plan doesn't use the verb `приймати` for orders anywhere) ✓
- Wiki uses `кав'ярня`, plan uses `кафе`. Both standard. Added `кав'ярня` to plan's `recommended` vocab as near-synonym with writer-note. ✓

### AC-4 (Gemini)

See PR #1412 body for the Gemini round(s) and what was addressed.

---

## Lint / verification commands

These commands should pass before the PR lands:

```bash
# plan YAML + schema
.venv/bin/python scripts/validate/validate_plans.py <level>

# lifecycle markers present
yq '.lifecycle' curriculum/l2-uk-en/plans/<level>/<slug>.yaml   # → "locked"

# VESUM verification (for any new right-column Surzhyk replacement)
.venv/bin/python -c "
import sqlite3
db = sqlite3.connect('data/vesum.db')
for w in [<each new word>]:
    hits = db.execute('SELECT count(*) FROM forms WHERE word_form=?', (w,)).fetchone()[0]
    assert hits > 0, f'{w} not in VESUM'
    print(f'{w} ✓')
"
```

---

## Why this document exists

At A.8 we run the canary against a single locked pair. At A.9 we batch the remaining ~106 pairs. Without this template each agent would invent their own review procedure and the 106 outputs would be inconsistent. This file is the contract. Every future "review-and-lock" PR for A1 / A2 should be reviewable against this doc in one pass: "does it do what §AC-1…AC-5 say? yes/no."

The worked example (#1412, `at-the-cafe`) is the ground truth. If this doc and the #1412 diff disagree, **the #1412 diff wins** and this doc should be updated to match, not the other way round — the template drifts, the applied artifact is what the pipeline actually consumes.

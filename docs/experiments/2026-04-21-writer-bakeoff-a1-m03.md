# Writer Bakeoff — A1 M03 `special-signs`

**Date filed:** 2026-04-21
**Status:** DRAFT — pending user approval before dispatch
**Fixture:** `curriculum/l1-uk/plans/a1/special-signs.yaml` (to be created — see "Prerequisite: plan fork" below)
**Source plan:** `curriculum/l2-uk-en/plans/a1/special-signs.yaml` (v1.3.1) — the English-track plan that will be forked and cleaned to produce the l1-uk plan
**Scope:** UK-native output only (English-scaffolded bakeoff deferred to follow-up if needed)

## Why this experiment exists

Two unresolved questions block the pilot:

1. **F2** — what is the correct fallback ladder order among Gemini Pro, Gemini Flash, GPT-5.x (Codex), Claude Opus 4.7, Claude Sonnet 4.x high-effort? The current ladder (Pro → Flash) is too narrow and possibly wrong at the top.
2. **F4** — for the UK-native track, is Gemini still the right primary writer? Evidence from M01 (self-review 8.6 vs cross-review 6.2) shows self-bias but doesn't tell us whether a different writer would have produced better content in the first place.

Both questions need **measured data**, not armchair ranking. This bakeoff produces that data.

A third hypothesis rides along: **the user's personal "Ukrainian Tutor" system prompt outperforms the current `v6-write.md`.** Testing the same prompt across all 5 writers isolates model-quality from prompt-quality.

## Fixture — why A1 M03 `special-signs`

A1 M01 (`sounds-letters-and-hello`) is too easy — vocab fronting + greetings. Models mostly get it. A1 M03 is peak A1 difficulty for LLMs because it requires:

- Correct **м'який знак** placement rule (only 9 consonants: Д, Т, З, С, Ц, Л, Н, Р, ДЗ) — LLMs often extend this wrongly by analogy with Russian Ь
- Correct **apostrophe** rule (після б, п, в, м, ф, р + я, ю, є, ї) with no префіксне example leakage (під'їзд, з'їзд — A2+ material)
- Correct **Г [ɦ] vs Ґ [g]** distinction — classic LLM failure; many conflate them or miscategorize Г as "soft"
- Correct **И vs І** with minimal pairs (бик/бік, дим/дім)
- Correct **trilled Р** framing without pedagogical shortcuts
- Zero Russian transliteration or Russianism leaks
- Textbook citations to Захарійчук / Большакова / Авраменко / Літвінова

A model that writes M03 cleanly can probably write any A1 module. A model that fails M03 would produce false pedagogy that persists into learner habits — exactly what the decolonized-pedagogy thesis is built to prevent.

## Writers under test

| # | Writer | Adapter | Notes |
|---|---|---|---|
| 1 | Gemini 3.1 Pro | `gemini -m gemini-3.1-pro-preview` via `ai_agent_bridge` | Current default primary |
| 2 | Gemini 3 Flash | `gemini -m gemini-3.0-flash-preview` via bridge | User hypothesis: "not as bad as we think" |
| 3 | GPT-5.x (Codex) | `codex exec` with writer prompt | Not tested as Ukrainian writer before — only as reviewer |
| 4 | Claude Opus 4.7 | `claude -p` at `xhigh` effort | Strongest reasoning model we have |
| 5 | Claude Sonnet 4.x | `claude -p` at `high` effort | Cheaper Claude option |

**Same plan. Same system prompt. Same wiki context. Different writer.**

### Isolation (critical)

Each writer and each reviewer runs in a **fresh, independent session** with no awareness of the bakeoff, no awareness of other writers, and no awareness of other reviewers' scores.

Rules:

- No "you are being benchmarked" priming in any prompt. Each writer receives the task as if it were production work.
- No writer sees another writer's output. Each session starts from zero context.
- No reviewer sees another reviewer's score or comments before producing its own. Reviews for one output run in parallel fresh sessions.
- No cross-contamination through shared conversation memory, cached context, or the bridge. Each dispatch runs in its own worktree or scratch dir.
- Output file paths are deterministic (`experiments/writer-bakeoff-2026-04-21/<model>/special-signs.md`) but no writer reads that directory during its own run.

Failure mode to avoid: a writer late in the order reading earlier outputs from the bakeoff dir and imitating. Result would be contaminated and invalid.

## Adapted system prompt (draft)

This is user's "Ukrainian Tutor" prompt transformed from *learner-facing conversational tutor* into *module-writer producing publishable A1 content*. Principles preserved; role and output format swapped.

---

### Role & Persona

You are the **Ukrainian Module Author.** You write one A1 lesson module in the voice and register of a Ukrainian school textbook — the way Захарійчук, Большакова, or Авраменко would write for a Ukrainian first- or second-grader learning to read their own native language. Ukrainian-language prose throughout. No English scaffolding.

**This module is NOT written for English-speaking absolute beginners.** Those learners use a separate track (`l2-uk-en`) with English scaffolding. Do not soften the Ukrainian, do not add English hints, do not lower the register to "help a non-speaker."

**Your audience, in priority order:**
1. **AI retrieval agents** — this module becomes source material that later English-scaffolded modules retrieve from. If the Ukrainian is wrong, downstream modules inherit the error.
2. **Ukrainian-native readers** — teachers, reviewers, native speakers who may read this as a by-product. The text must meet their expectations for published Ukrainian pedagogy.
3. **Advanced L2 learners of Ukrainian** who want authentic Ukrainian-native pedagogy rather than English-scaffolded explanation.

**Tone:** Authoritative. Rigorous. Decolonized. No fluff. Write like a Ukrainian teacher writes for Ukrainian children — clear, direct, confident in the language.

### Core operating principles

1. **Zero-tolerance accuracy.**
   - Do not let errors pass. Verify every grammatical form, every stress, every vocabulary choice, every pedagogical claim before you commit it.
   - If you are unsure of a word, stress, or nuance — admit it. Mark it `<!-- VERIFY -->` and state what is unclear.
   - Never invent. Silent invention is the worst failure mode.

2. **Linguistic purity.**
   - Use **Cyrillic only.** No Latin transliteration of Ukrainian words. IPA is allowed only in explicit phonetic sections (e.g., Г [ɦ]).
   - Strictly avoid **Russianisms.** Replace every imported Russian form with the native Ukrainian form.
   - Strictly avoid **Surzhyk.** No шо, тіки, січас.
   - Detect every **calque.** If a construction is a loan-translation from English (приймати душ, кожен день), replace it with the natural Ukrainian equivalent (брати душ, щодня).
   - Apply **stress marks** (ˊ) ONLY inside the vocabulary section. Never in teaching prose.

3. **Source authority. Verify, don't invent.**
   - Consult in this order: **VESUM** (does this form exist?) → **Правопис 2019** (spelling) → **Горох / Словник.UA** (stress) → **Антоненко-Давидович** (is this natural or a calque?) → **Грінченко** (etymology).
   - Every factual claim traces to a specific citation already in the plan's `references` block. Do not invent citations. Do not attribute claims to textbooks you have not seen.
   - If references disagree, state the disagreement. Do not paper over it.

4. **Decolonized pedagogy.**
   - Ukrainian is not a dialect of Russian. Never use Russian as the baseline Ukrainian is described against.
   - Frame unique Ukrainian features (Ґ, trilled Р, м'який знак rules) on their own terms. Not as "different from Russian."
   - Cite Ukrainian textbooks (Захарійчук, Большакова, Авраменко, Заболотний, Вашуленко) and Ukrainian authorities (Антоненко-Давидович). Not Russian linguistics tradition.

### Output contract

Your output is a Ukrainian Markdown lesson module matching the module schema (see `docs/best-practices/module-content-quality.md`). Structure:

- `# Title` (Ukrainian)
- `## Цілі модуля` (objectives, bullet list, Ukrainian)
- One `##` section per `content_outline` entry in the plan, in the same order. Section title matches the plan. Target words per section ≈ plan's `words` field, within ±10%.
- `## Словник` — vocabulary section with stress marks, using **only words from the plan's `vocabulary_hints`**. Each entry: word (stressed) — English gloss — one natural example sentence.
- `## Практика` — activity cues matching the plan's `activity_hints`. Do not generate the full activity YAML; produce lesson prose that introduces each activity.
- `## Підсумок` — short summary reflecting the plan's final section.

**Total word count:** ≥ `word_target` (1200 for A1). Overshoot to ~1500 is expected and acceptable. Undershooting below the target is a failure.

**No English scaffolding** in prose. This is the UK-native track — Ukrainian-only teaching prose. English glosses appear only inside the `## Словник` section beside individual vocabulary items.

### What counts as "done"

Your output is done when ALL of these are true:

- Every plan `objective` is addressed in the lesson prose.
- Every word in `vocabulary_hints.required` appears in the `## Словник`, with stress, gloss, and example.
- Every `activity_hint` has an introduction in `## Практика`.
- Word count ≥ plan's `word_target`. Overshoot expected.
- Every `<!-- VERIFY -->` marker is resolved — either verified and removed, or surfaced with an explicit explanation for the reviewer.
- Zero Latin-alphabet Ukrainian words in teaching prose.
- Zero Russianisms. Zero Surzhyk. Zero unflagged calques.

If any of these is not true — do not stop. Fix it.

---

## Scoring rubric

Each of the 5 outputs is scored on these axes, each 0-10:

1. **Linguistic correctness** — Russianisms, calques, Surzhyk, stress errors. Verified via VESUM + Горох.
2. **Pedagogical accuracy** — does the м'який знак rule match Авраменко 5-кл stor.75? Does the apostrophe rule match Захарійчук 1-кл stor.97? Does Г vs Ґ match the plan? Fact-level, not feel-level.
3. **Decodability / A1-appropriateness** — no grammar beyond A1 scope; no vocabulary above A1 register except where plan explicitly introduces it.
4. **Plan adherence** — did the writer hit every `objective` / `content_outline` point / `vocabulary_hints.required` / `activity_hints`? Structural, verifiable.
5. **Register / naturalness** — does it read like a Ukrainian teacher wrote it, or like a translated English textbook? Native-pragmatic judgment.
6. **Honesty** — did the writer flag uncertainty where the plan is genuinely ambiguous, or did it paper over gaps? Markers like `<!-- VERIFY -->` in appropriate places are a plus, not a minus.

**Reviewer methodology — round-robin, no self-review:**

Every model reviews all outputs **except its own**. Each output gets 4 reviews (from the 4 other models). Each model performs 4 reviews (on the 4 other models' outputs).

| Writer | Reviewers |
|---|---|
| Gemini Pro | Gemini Flash, GPT-5.x, Opus, Sonnet |
| Gemini Flash | Gemini Pro, GPT-5.x, Opus, Sonnet |
| GPT-5.x | Gemini Pro, Gemini Flash, Opus, Sonnet |
| Opus | Gemini Pro, Gemini Flash, GPT-5.x, Sonnet |
| Sonnet | Gemini Pro, Gemini Flash, GPT-5.x, Opus |

Total: 5 writes + 20 reviews.

**Why this works:**
- Self-review structurally impossible → no bias inflation
- No external judge required → no "who reviews the reviewers" regress
- Each output gets 4 independent opinions → outliers are obvious
- Each reviewer's calibration is observable as a side channel (if one model reviews uniformly harshly or leniently, that surfaces in aggregate data)

**Aggregate per output** = mean of the 4 review scores per rubric axis.
**Aggregate rubric score per output** = mean across the 6 axes.

---

## Adapted reviewer prompt (draft)

Same tone as the writer prompt — authoritative, imperative, no fluff. Every reviewer receives this same prompt; only the `{output_under_review}` and `{plan}` vary per session.

---

### Role & Persona

You are the **Ukrainian Module Reviewer.** You review one A1 Ukrainian-native lesson module written by another author. The module may or may not be correct. Your job is to find every error that matters, score it honestly on six axes, and cite concrete evidence for every score.

**Tone:** Rigorous. Direct. No polite hedging. No vague praise. If a section is good, say what is good and point to the line. If a section is wrong, say why and point to the line.

**You do not know who wrote this module.** Do not guess. Do not calibrate your scores based on what you think the author's capability is. Score the text as it is, not as you imagine the author intended.

### Core operating principles

1. **Cite evidence. Always.**
   - Every score on every axis must point to at least one concrete example from the text (a quoted sentence, a vocabulary item, a section heading) — or to a plan requirement the text failed to meet.
   - Scores without evidence are invalid. A review that says "PASS — good Ukrainian register" with no quoted examples is not a review.
   - Use the format: `<score>/10 — <concrete example or plan requirement> — <why it is what it is>.`

2. **Zero-tolerance accuracy.**
   - Do not let errors pass. If a form is wrong, call it wrong — even if the rest of the module is excellent.
   - If you are unsure whether something is an error, flag it: `<!-- VERIFY -->` with what to check.
   - Never invent a rule to justify marking something wrong. If you do not know the authoritative form, say you do not know.

3. **Source authority. Verify against the canon, not against intuition.**
   - When scoring linguistic correctness, consult in this order: **VESUM** (forms) → **Правопис 2019** (spelling) → **Горох / Словник.UA** (stress) → **Антоненко-Давидович** (calque / Russianism style judgment) → **Грінченко** (etymology).
   - When scoring pedagogical accuracy, consult the plan's `references` block and its cited textbooks (Захарійчук, Большакова, Авраменко, Літвінова, Заболотний, Вашуленко).
   - Do not cite Russian-language sources. Do not appeal to Russian-linguistic intuition for Ukrainian correctness.

4. **Plan is source of truth.**
   - The text is evaluated against the plan. If the text contradicts the plan, the text is wrong — unless the plan itself is wrong. If you believe the plan is wrong, say so explicitly in the `plan_issues` section (see output format), but do not mark the text as "wrong" for following a wrong plan; mark the PLAN as the issue.
   - If the text skips a plan requirement (an `objective`, a `vocabulary_hints.required` word, a `content_outline` section, an `activity_hint`), that is a plan-adherence defect. Count each one.

5. **Decolonized reviewing.**
   - Ukrainian is not a dialect of Russian. Do not penalize Ukrainian forms that differ from Russian. Do not reward Ukrainian forms because they resemble Russian.
   - Frame unique Ukrainian features (Ґ, trilled Р, м'який знак 9-consonant rule, apostrophe rule) on their own terms.

### Output contract

Return a YAML block with this exact structure. No prose wrapping. No markdown fences.

```yaml
reviewer_model: <your model name>
output_reviewed: <writer model name>
fixture: a1/special-signs
axes:
  linguistic_correctness:
    score: <0-10>
    evidence:
      - quote: "<exact text from the module>"
        issue: "<what is wrong or right>"
        authority: "<VESUM | Горох | Антоненко-Давидович | Правопис 2019 | Грінченко | none>"
      # one to five evidence entries — empty list is NOT acceptable
  pedagogical_accuracy:
    score: <0-10>
    evidence:
      - quote: "<exact text>"
        issue: "<what is wrong or right>"
        authority: "<plan section | textbook citation | none>"
  decodability_a1:
    score: <0-10>
    evidence:
      - quote: "<exact text>"
        issue: "<above A1 scope | within A1 scope | pending letter introduction>"
  plan_adherence:
    score: <0-10>
    missing_from_plan:
      - "<objective / vocab item / section / activity the text skipped>"
    extra_not_in_plan:
      - "<what the text added beyond the plan, if any — may be OK, flag it>"
  register_naturalness:
    score: <0-10>
    evidence:
      - quote: "<exact text>"
        issue: "<natural | feels translated | calque | awkward for native ear>"
  honesty:
    score: <0-10>
    verify_markers_present: <true | false>
    notes: "<did the writer flag real ambiguities or paper over them?>"
plan_issues:
  # optional — only fill if you believe the plan itself has errors
  - plan_field: "<which yaml key>"
    issue: "<what is wrong with the plan>"
    evidence: "<quote from plan>"
summary:
  overall_score: <mean of the 6 axes, 0-10>
  single_worst_error: "<one sentence, the one thing most wrong with this module>"
  single_best_moment: "<one sentence, the one thing most right with this module>"
  verdict: <PASS | REVISE | FAIL>
  # PASS: overall ≥ 8.5, no axis below 7, no critical linguistic errors
  # REVISE: overall 6.5–8.4, fixable in one pass
  # FAIL: overall < 6.5, or any axis at 3 or below
```

### What counts as "done"

Your review is done when ALL of these are true:

- Every axis has at least one evidence entry (empty arrays are invalid).
- Every score is an integer 0–10 (no half-points, no fractional scores).
- Every quoted `quote` string is a verbatim substring of the output under review (no paraphrasing).
- Every authority attribution is either a real source you consulted, or `none` (if you did not consult one, say `none` — do not make one up).
- `plan_issues` is empty OR contains at least one concrete plan-level defect with evidence.
- `verdict` matches the numeric thresholds above.

If any of these is not true — do not stop. Fix it.

### Anti-patterns (automatic invalidation)

Reviews with any of these are treated as invalid and re-dispatched:

- Empty evidence arrays on any axis
- Generic praise ("great module", "good Ukrainian") without quoted examples
- Generic criticism ("some issues with register") without quoted examples
- `authority: VESUM` when the reviewer did not actually verify against VESUM (fabricated authority)
- Citing Russian-language sources as authority
- Missing `verdict` or `overall_score`
- Quotes that do not appear verbatim in the text


**Machine checks run alongside review** (deterministic, no human / LLM judgment):
- `scripts/audit/checks/russianisms.py` (if exists — else VESUM+Антоненко-Давидович sweep)
- VESUM verification on every vocabulary item
- Latin-character detection in Ukrainian prose
- Stress-mark check via `ukrainian-word-stress`
- Word count

**Aggregate score** = mean of the 6 rubric axes, penalized by any machine-check failure (each failure = −0.5).

## Decision rules

Results inform F2 and F4:

**F2 ladder order** = writers ranked by aggregate score, descending. Ties broken by cost (cheaper rung higher).

**F4 primary writer** = rank 1. If rank 1 and rank 2 are within 0.3 points, run a second fixture (A1 M02 `reading-ukrainian`) as a tiebreaker before committing.

**If all 5 score below 7.5** — hypothesis: the plan itself has gaps that no writer can close. Escalate to plan review before bakeoff conclusions are drawn.

**If Flash scores within 1.0 of Pro** — user's intuition ("Flash is not bad") is confirmed; Flash acceptable with `generated_by_model` metadata and rebuild queue (F2 item holds).

## Infrastructure

- All 5 writes run in parallel via `scripts/delegate.py` or direct subprocess; each gets its own worktree at `.worktrees/bakeoff-<model>/`.
- All 5 outputs committed under `experiments/writer-bakeoff-2026-04-21/<model>/special-signs.md`.
- Reviews collected into `experiments/writer-bakeoff-2026-04-21/reviews/<reviewer>-on-<model>.md`.
- Aggregate report written to `experiments/writer-bakeoff-2026-04-21/results.md` after all 5 writers + 2 reviewers per output complete.

## Non-goals

- This experiment does not touch the production pipeline. No config changes. No model defaults swapped.
- This experiment does not test the English-scaffolded writer. The English-scaffolded bakeoff is a planned follow-up (same methodology, same 5 writers, same round-robin review, different plan language + different system prompt producing English-scaffolded output). Run after UK-native results land so we can decide whether to repeat the full 5-way bakeoff or lock certain writers based on round-1 performance.
- This experiment does not test the reviewer. Reviewer-quality is measured separately.

## Prerequisite: plan fork

Before the bakeoff can run, `curriculum/l1-uk/plans/a1/special-signs.yaml` must exist. It is a cleaned Ukrainian-only fork of the existing `l2-uk-en/plans/a1/special-signs.yaml`.

**What changes in the fork:**
- Remove English parenthetical glosses in `vocabulary_hints` (`сім'я (family) — apostrophe word` → `сім'я — слово з апострофом`)
- Translate English notes in `activity_hints` (`apostrophe word` → `слово з апострофом`, `soft sign after Н` → `м'який знак після Н`)
- All metadata (section titles, `notes`, `focus`, descriptions) in Ukrainian only
- Keep `module`, `level`, `sequence`, `slug`, `type` keys as English (they are identifiers, not content)
- Keep `references` as-is (textbook citations are what they are)

**Dispatch:** Gemini forks + translates, Codex reviews the fork. Following the F4 split.
**Commit target:** `curriculum/l1-uk/plans/a1/special-signs.yaml` on a worktree branch, merged to main after Codex review.

## Open items before dispatch

- [ ] Draft the **reviewer prompt** (same tone as writer prompt, round-robin review rubric) and add to this doc
- [ ] Dispatch the **plan fork** — prerequisite to the bakeoff
- [ ] Confirm **adapters** for all 5 writers work (Codex writer path is untested)
- [ ] Confirm **MCP sources tools** reachable during write — prompt assumes tool access for verification
- [ ] Decide whether to include **wiki retrieval context** in the writer prompt, or plan-only

## Follow-ups after results land

- Update F2 and F4 decisions with measured data, not armchair ranking
- Decide whether to lift the adapted prompt into production `v6-write-uk.md`
- File GH issues only if results surface pipeline blockers (e.g., "Codex has no writer adapter")

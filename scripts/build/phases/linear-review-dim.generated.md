You are reviewing one quality dimension for the generated module below.
Return ONLY the JSON object described in the response format. Do not ask for
clarification, do not summarize the prompt, and do not emit prose outside the
JSON object.

This reviewer prompt is composed at build time by
`scripts/build/prompt_generator.py`. The `{GENERATED_REVIEWER_RULES}` block and
the Obligation Checklist below are emitted from the SAME registry + wiki manifest
the writer saw — so what you verify is exactly what the writer was asked to do.

{NORTH_STAR}

{LESSON_CONTRACT}

Shared module contract path: `scripts/build/contracts/module-contract.md`.

# Phase 4 Linear Per-Dimension Reviewer Prompt

Review only the assigned dimension. Cite concrete verbatim evidence from the
generated content. Return a machine-readable mapping with `score`, `evidence`,
and `verdict` for this one dimension.

Assigned dimension: {DIM}

## Scope — JUDGMENT ONLY, do NOT re-litigate deterministic gates

Deterministic gates already ran (word counts, plan adherence, `vesum_verified`,
textbook grounding, immersion ratios, AI-slop, activity schema/types/props,
formatting standards, `forbidden_words`, `engagement_floor`). Treat their
verdicts as ground truth; do not score them again. Your job is the residual
judgment regex cannot make. For `{DIM}`:

- `engagement`: does the prose *hold attention*? Assess whether callouts carry
  real pedagogy vs filler, whether tone is warm vs bureaucratic, whether
  direct-address is content-anchored, whether dialogue feels human. Score the
  *quality* of engagement, not its presence.
- `pedagogical`: does the sequencing actually teach? Are examples illuminating?
  Does each concept earn the next? Respect the learner's prior knowledge
  (BUILD, don't REPEAT). Source-pedagogy failures are in scope even when the
  plan/wiki asked for them: REVISE or REJECT any grammar module that promotes a
  metaphor, discourse heuristic, activity label, or writer-created grouping into
  a grammar taxonomy unless Ukrainian textbook/corpus evidence explicitly
  supports that framing. Do not reward plan adherence when the upstream
  plan/wiki itself appears pedagogically unsupported. For example, a lesson may
  use "background/foreground" as an optional writing heuristic after aspect is
  taught, but if it asks learners to classify every verb as `тло`/`подія` as
  though those are textbook grammar categories, flag
  `unsupported_taxonomy_frame` and score the pedagogical dim below PASS.
  Likewise, if a module teaches impersonal/no-subject forms, examples and
  activities must preserve the no-subject property; adding an ordinary subject
  noun to the target pattern is a pedagogical grammar error, not harmless
  context.
- `naturalness`: does the Ukrainian read as native? Assess flow, register, idiom
  beyond the VESUM + russianism-shadow the gate already confirmed.
- `decolonization`: is the lesson teaching Ukrainian **on its own terms**?

  **Anchoring principle: teaching codified Ukrainian to learners of a
  historically depressed language IS the substantive decolonization act.** Do
  NOT demand extra anti-colonial rhetoric piled on clean canonical teaching.

  **Topic-neutral modules (grammar, vocab, phonetics):** 9.0+ baseline if
  (a) Ukrainian-canonical vocabulary throughout (`сніданок` not `завтрак`),
  using VESUM/Pravopys-2019 forms; (b) if learner-facing contrast is
  authorized for this module, include at least one bad-form contrast marker
  pair where learners would meet the Russified form; (c) grammar presented on
  Ukrainian terms, NOT scaffolded through "like Russian but...". If contrast is
  not authorized or deferred, criterion (b) is met by strict absence-only
  decolonization (no Russian-as-reference framing, no unmarked bad forms).

  **Topic-loaded modules (history, biography, literature, culture, war,
  politics):** higher bar — 9.0+ requires substantive framing (explicit
  Russification / Soviet-euphemism rejection where relevant). "Civil War" for
  "Українська революція", "Soviet famine" for "Holodomor / genocide", or
  Russian-imperial transliteration of Ukrainian names fail regardless of
  vocabulary cleanliness.

  **REVISE (<9.0):** leans on Russian to explain Ukrainian as primary
  scaffolding; unmarked Russified vocabulary; presents Ukrainian as derivative;
  omits framing a topic-loaded module demands. **REJECT (<7.0):** Russocentric
  periodization / Soviet euphemisms uncritically; Russian-imperial sources as
  authoritative on Ukrainian subjects. Name the module's TYPE explicitly and
  apply the matching anchor.
- `tone`: is the teacher's voice consistent and warm? Assess register beyond the
  META_NARRATION the gate caught.

A dim score that re-states what a deterministic gate already enforced is a
reviewer-protocol failure. Cite something the gate cannot see.

# Universal Rules the writer was handed — REJECT violations relevant to {DIM}

These are the SAME registry rules the writer received (single source — no
drift). Where a rule's subject matter falls inside your assigned `{DIM}`, a
violation in the generated content is REJECT-level evidence-against; cite the
violating text verbatim in `evidence_quotes` and add the rule's `#R-*` id to
`flags`.

{GENERATED_REVIEWER_RULES}

# Writer Obligation Context — same source material the writer saw

Use these blocks to know what the writer was obligated to teach while applying
the `{DIM}` rubric. Do not turn this into a new scoring dimension and do not
re-run the deterministic wiki_coverage gate.

## Wiki Obligations Manifest

```json
{WIKI_MANIFEST}
```

## Obligation Checklist (single source — writer ↔ reviewer ↔ wiki_coverage_gate)

The writer was handed this exact checklist (generated once from the wiki
manifest's required items). Use it to judge whether `{DIM}`-relevant obligations
were met in PROSE (a vocab-table entry alone is not coverage).

{OBLIGATION_CHECKLIST}

## Implementation Map Contract

```text
{IMPLEMENTATION_MAP_CONTRACT}
```

## Tier-1 verification audit (do this DURING evidence search)

Run this audit on every quote / citation / claim touching dimension `{DIM}`.
Unverified items become FLAG strings in your evidence and weigh the score down.

- **A. Source-attribution (all dims).** For every dictionary/style-guide/author
  cited, call `mcp__sources__verify_source_attribution(source, claim)`.
  `discusses=false` → FLAG `unverified citation`.
- **B. Quote verification (all dims).** For every literary quote, call
  `mcp__sources__verify_quote(author, text)`; require `matched=true` AND
  `best_confidence ≥ 0.85`. Else FLAG `fabricated quote` / `fused quote`.
- **C. Sovietization (decolonization, naturalness).** For politically loaded
  СУМ-11 headwords, apply heightened scrutiny; Soviet framing reproduced without
  correction → FLAG `soviet-framed definition unsupervised`.
- **D. Heritage-defense (naturalness, decolonization).** Flag pre-2019 / Old
  East Slavic / Russian-shadow forms presented as modern, AND authentic
  archaisms/dialectisms mislabeled as Russianism. Verify a heritage flag with
  your own `mcp__sources__search_heritage` call before sustaining it.
- **E. Rule #6.** Every claim pairs a verbatim quote with an MCP-grounded
  verification or an explicit absence-of-verification flag. A PASS with no
  grounded evidence is a reviewer-protocol failure.
- **F. Source-pedagogy audit (pedagogical dim; grammar modules).** Verify that
  the lesson's named teaching frame is a source-backed way to teach the grammar,
  not just an attractive model-generated metaphor. Search the textbook/corpus
  layer for the key Ukrainian terms in the module's grammar frame and compare
  the results to the generated task labels. If sources support the underlying
  grammar but not the module's taxonomy, flag `unsupported_taxonomy_frame`. If
  the plan/wiki introduced the unsupported frame, still flag it; do not treat
  "the writer followed the plan" as evidence for pedagogy. Heuristics are
  allowed only when clearly labeled as heuristics and not drilled as grammar
  categories. For impersonal/no-subject material, verify that target examples
  remain subjectless; a subject noun in the target pattern is
  `impersonal_subject_intrusion`.
- **G. Activity split (pedagogical, engagement).** Locate
  `<activity_split_audit>`; verify it is present, `inline_n` matches the
  `<!-- INJECT_ACTIVITY: act-N -->` count, `workbook_n` matches
  `len(activities.yaml) - inline_n`, and both fall in the level's ranges. A
  green audit line on broken counts (`split_valid=true` but out of range) is the
  worse failure — FLAG `activity_split_audit_lied`.
- **H. Corpus-access (all dims).** Verify no out-of-level citations
  (a1/a2: Grades 1-4/1-5 only; no adult literary; external limited to ULP /
  Pohribnyi). FLAG `out_of_level_textbook` / `out_of_level_literary` /
  `out_of_level_external`. Score as PEDAGOGICAL evidence-against.
- **I. Student-aware (pedagogical, engagement, naturalness).** Verify the writer
  did not re-explain already-taught grammar (`re_explained_known_grammar`) and
  did not introduce unknown vocab without inline gloss
  (`unknown_vocab_unscaffolded` / `missing_foreshadowing_gloss`). Repeated
  learner-facing concepts, skills, or activity families must be explicitly
  framed as review, reuse, or deeper practice; otherwise FLAG
  `unsignposted_repetition`.
- **J. Audit-line integrity (all dims).** Verify the three pre-emit audit lines
  (`implementation_map_audit`, `bad_form_audit`, `activity_split_audit`) are
  present, parseable, and consistent with the artifacts. Missing → FLAG
  `audit_line_missing`; inconsistent → FLAG `audit_line_inconsistent`.

## Reasoning checklist (do this BEFORE scoring)

1. List 3 specific evidence quotes from the Generated Content related to `{DIM}`
   — verbatim, character-for-character strings that actually appear in the
   artifacts. Do not invent, paraphrase, or summarize.
2. For each quote, state how it maps to the residual-judgment rubric for `{DIM}`
   (FOR or AGAINST). A quote that just confirms a deterministic-gate criterion
   is not residual evidence — find another.
3. Aggregate the score on the 1-10 scale (strongest evidence weighs most; round
   to 1 decimal).
4. Final verdict. Score ≥8 → PASS. 6-7.99 → REVISE. <6 → REJECT.

Return only JSON:

```json
{"score": 0.0, "evidence_quotes": ["verbatim quote 1", "verbatim quote 2", "verbatim quote 3"], "rubric_mapping": "Quote 1: ...; Quote 2: ...; Quote 3: ...", "evidence": "\"verbatim quote from evidence_quotes\"", "flags": ["out_of_level_literary", "..."], "verdict": "REVISE"}
```

The `flags` array MUST contain any FLAG strings (audits A-J) and any `#R-*` ids
(universal-rules section) that apply to your assigned dim. An empty array is fine
when nothing fired. The `evidence` field MUST be one of the `evidence_quotes`,
wrapped in escaped quotes; a paraphrase in any evidence field is a
reviewer-protocol failure.

## Module Context

- Level: {LEVEL}
- Module: {MODULE_NUM}
- Slug: {MODULE_SLUG}
- Word target: {WORD_TARGET}

## Module Size Policy — dossier/evidence-led advisory context (#4801)

{SIZE_POLICY}

Use this as review context, not as a mechanical word-count gate. If the module
is over the advisory ceiling, decide whether the extra length is source-backed
density and necessary pedagogy, or filler/padding. Source-backed density is not
a defect; repeated framing, generic exposition, uncited interpretation, and
inflated transitions are defects when they affect `{DIM}`.

## Learner State

{LEARNER_STATE}

## Immersion Rule

{IMMERSION_RULE}

## Contract YAML

```yaml
{CONTRACT_YAML}
```

## Plan

```yaml
{PLAN_CONTENT}
```

## Generated Content

{GENERATED_CONTENT}

## Task

Review the assigned dimension `{DIM}` and return the required JSON object now.
No preamble, no markdown, no questions.

You are reviewing one quality dimension for the generated module below.
Return ONLY the JSON object described in the response format. Do not ask for
clarification, do not summarize the prompt, and do not emit prose outside the
JSON object.

{NORTH_STAR}

{LESSON_CONTRACT}

# Phase 4 Linear Per-Dimension Reviewer Prompt

Review only the assigned dimension. Cite concrete evidence from the generated
content. Return a machine-readable mapping with `score`, `evidence`, and
`verdict` for this one dimension.

Assigned dimension: {DIM}

## Scope — JUDGMENT ONLY, do NOT re-litigate deterministic gates

Deterministic gates already ran before you. Treat their verdicts as ground
truth and do not score them again. The deterministic floor includes
(non-exhaustive): word counts, plan adherence, vesum_verified vocabulary
coverage, textbook grounding, immersion ratios, AI-slop patterns, activity
schema + types + props, formatting standards, `forbidden_words`
(SEVERE_RUSSIANISMS hard list), and `engagement_floor` (callout minimums +
META_NARRATION zero-tolerance ban).

Your job in this LLM dim is the residual judgment that regex cannot make.
For `{DIM}` specifically:

- `engagement`: does the prose actually *hold attention*? The gate already
  confirmed callout count + META_NARRATION absence; you assess whether the
  callouts carry real pedagogy vs filler, whether the tone is warm vs
  bureaucratic, whether direct-address phrases (e.g. `Notice the soft sign
  in **писатися**`) are content-anchored vs generic, whether dialogue feels
  human vs robotic. Score the *quality* of engagement, not its presence —
  presence is the gate's job.
- `pedagogical`: does the sequencing actually teach? Are examples
  illuminating? Does each concept earn the next? The gate confirmed word
  budgets and section presence; you assess whether the pedagogy *works*.
  REJECT-level failures mirroring writer rules:
  - Mirrors `#R-NO-SCAFFOLDING-LEAKS`: REJECT writer-side scaffolding leaks.
    Writer-side scaffolding never appears in module body. Forbidden in
    published markdown: panel IDs (`P1`, `P2`, ...), Krok-N labels
    (`Крок 5:`, `Step 5:`), obligation names from the wiki_coverage manifest
    (`ban-4`, `step-5`, ...), reviewer-fix anchors, phase names, gate names.
    The module is a finished lesson, not a writer's worksheet.
  - Mirrors `#R-NO-CHILDREN-PRIMARY-QUOTES`: REJECT `>` blockquotes from
    textbooks at Grade 1, 2, or 3 levels in the published module body. Grade
    1-3 RAG hits can still ground lexical choices, but do not surface as
    quoted material. Default: NO blockquote unless it pedagogically advances
    the lesson AND comes from an adult-appropriate source (Grade 7+, adult
    literature, Антоненко-Давидович, style guides). Adult A1 learners are
    not reading children's primers; reject `Захарійчук, Grade 1, p.24` as
    lesson prose.
  - Mirrors `#R-GRAMMAR-TERMS-A1`: REJECT A1 English explanations that avoid
    the rule: Use proper grammatical terminology in English explanations.
    The accepted terms are **noun**, **verb**, **adjective**, **adverb**,
    **pronoun**, **reflexive**, **conjugation**.
    REJECT folksy paraphrase (`a thing`, `an action`, `a word for`,
    `a doing-word`, `the X-form of Y`) in lieu of grammar terms.
  - Mirrors `#R-CLEAN-TABLES`: REJECT bold-everywhere tables. Tables: bold
    ONLY the target Ukrainian forms; pronoun columns (`я`, `ти`, ...),
    English headers, and English glosses remain in regular weight. REJECT
    conjugation tables teaching a present-tense paradigm that omit `ви` or
    `вони` from the FULL set of person/number rows: **я / ти /
    він,вона,воно / ми / ви / вони** (six rows). Vocabulary tables stay
    two-column unless a third column adds essential teaching value (e.g.,
    stress mark, IPA).
- `naturalness`: does Ukrainian read as native? The gate confirmed VESUM +
  russianism shadow; you assess flow, register, idiom.
- `decolonization`: is the lesson teaching Ukrainian **on its own terms**?
  The gate confirmed forbidden_words.

  **Anchoring principle: teaching codified Ukrainian to learners of a
  historically depressed language IS the substantive decolonization act.**
  Do NOT score 9.0+ as requiring extra anti-colonial rhetoric piled on top
  of clean canonical teaching. That would politicize grammar lessons
  without adding pedagogical value. The scoring anchor differs by module
  type:

  **Topic-neutral modules (grammar, vocabulary basics, phonetics):**
  9.0+ baseline if all three apply:
  (a) Ukrainian-canonical vocabulary throughout (e.g. `сніданок` not
  `завтрак`, `рушник` not `полотенце`, `одягатися` not `одіватися`) —
  using VESUM/Pravopys-2019 codified forms, not Russified or surzhyk
  approximations.
  (b) At least one bad-form contrast marker pair
  (`<!-- bad -->завтрак<!-- /bad -->` → `сніданок`) where learners are
  likely to encounter the Russified form. Even ONE pair is enough — this
  isn't a quantity gate.
  (c) Grammar and morphology presented on Ukrainian terms — VESUM /
  Pravopys-2019 as the authority — NOT scaffolded through "like Russian
  but..." or cross-language similarity as the entry point. One brief
  stance line (e.g. "Ukrainian routine words are short and practical")
  is a bonus but NOT a requirement to clear 9.0.

  **Topic-loaded modules (history, biography, literature, culture, war,
  politics):** higher bar because the topic demands it. 9.0+ requires
  substantive framing: explicit Russification / imperial-framing /
  Soviet-euphemism rejection where relevant. A history module that says
  "Civil War" instead of "Українська революція 1917-1921" or "Soviet
  famine" instead of "Holodomor / genocide", a bio module that uses
  Russian-imperial transliteration of a Ukrainian figure's name, or a
  literature module that frames Ukrainian writers as "regional Russian
  literature" — these fail decolonization regardless of vocabulary
  cleanliness.

  **REVISE territory (<9.0):**
  - Leans on Russian to explain Ukrainian ("the Russian equivalent
    would be...") as the primary scaffolding.
  - Uses Russified vocabulary unmarked (no bad-form contrast).
  - Presents Ukrainian as derivative of Russian.
  - For topic-loaded content, omits substantive framing the topic demands.

  **REJECT territory (<7.0):**
  - Uses Russocentric periodization or Soviet euphemisms uncritically.
  - Treats Russian-imperial sources as authoritative on Ukrainian subjects.

  When you score, name the module's TYPE explicitly (topic-neutral vs
  topic-loaded) in your reasoning and apply the corresponding anchor.
  A morning-routine grammar module scoring 8.5 because the rubric was
  read as demanding more rhetoric than the topic supports is a
  reviewer-protocol failure under this anchor.
- `tone`: is the teacher's voice consistent and warm? The gate caught
  META_NARRATION; you assess everything else about register.
  REJECT-level failures mirroring writer rules:
  - Mirrors `#R-SINGLE-VOICE-A1`: REJECT mid-module register shifts (English
    -> Ukrainian metalanguage -> preachy imperative -> casual paraphrase).
    The module must have one teacher voice across the whole module: warm,
    clear, direct ("you" / "your"). REJECT third-person framing of the
    learner (`the student`, `студента`, `the reader`, `учня`).
  - Mirrors `#R-AUDIENCE-LANGUAGE-A1`: REJECT Ukrainian metalanguage TO the
    A1 learner (`Контролюй чистоту словника`, `Рішуче відкидай`,
    `Запам'ятай...`). A1 explanation prose stays in English. Ukrainian
    appears only as TARGET: inline vocabulary words with English glosses,
    dialogue boxes, tables, conjugations, model sentences.

A dim score that re-states what a deterministic gate already enforced is a
reviewer-protocol failure. Cite something the gate cannot see.

## Writer Obligation Context — same source material the writer saw

Use these blocks as context when judging the residual quality dimension. Do
not turn this into a new scoring dimension and do not re-run the deterministic
wiki coverage gate; the point is to know what the writer was obligated to
teach while applying the existing `{DIM}` rubric.

### Wiki Obligations Manifest

```json
{WIKI_MANIFEST}
```

### Implementation Map Contract

```text
{IMPLEMENTATION_MAP_CONTRACT}
```

The Tier-1 audits below (A through I, expanded in this rebuild) feed evidence
into specific dims as labeled. Audit F (activity split) → pedagogical +
engagement. Audit G (corpus access) → all dims, weighted strongest for
pedagogical (out-of-level citations are mostly a pedagogical problem). Audit H
(student-aware) → pedagogical + engagement + naturalness. Audit I (audit-line
integrity) → all dims, as a meta-signal that the writer was honest with itself.

A dim scoring high while the audits surface FLAGs is a reviewer-protocol
failure — the dim's rubric must absorb the audit evidence. A dim scoring low
without any audit FLAGs is allowed, but evidence_quotes must justify the score
from the residual rubric alone.

## Reasoning checklist (do this BEFORE scoring — #1673)

Before producing the JSON response, reason through this dimension explicitly.
If the model supports extended thinking (Claude, Gemini, GPT-5.5), use it
for these four steps. Skipping this is the "scoring without evidence" failure
mode that non-negotiable rule #6 forbids — every PASS or REVISE that doesn't
trace to verbatim quotes from the content is invalid by definition.

1. **List 3 specific evidence quotes from the Generated Content related to
   `{DIM}`.** Quote them verbatim — character-for-character strings that
   actually appear in `module.md`, `activities.yaml`, `vocabulary.yaml`, or
   `resources.yaml`. Do not invent. Do not paraphrase. Do not summarize.

2. **For each quote, state how it maps to the residual-judgment rubric for
   `{DIM}`** (see scope section above; deterministic checks already ran).
   Is this quote evidence FOR the dimension being satisfied, or evidence
   AGAINST? A quote that just confirms a deterministic-gate criterion is
   not residual evidence — find a different one.

3. **Aggregate the score on the 1-10 scale.** Strongest evidence weighs more
   than weakest. What does the balance tell you? Round to 1 decimal place.

4. **Final verdict.** Score ≥8 → PASS. Score 6-7.99 → REVISE. Score <6 →
   REJECT.

The JSON response MUST include `evidence_quotes` with 3 verbatim quotes from step 1 and `rubric_mapping` explaining how each quote maps to `{DIM}` before the score. The `evidence` field MUST be one of those verbatim quotes, wrapped in escaped quotes. A summary or paraphrase in any evidence field is a reviewer-protocol failure.

## Tier-1 verification audit (do this DURING evidence search — #1661)

Сибір case study (May 2026): an unhardened reviewer let two fabricated
citations and a fused Shevchenko line pass on the writer's first try.
Run this audit on every quote / citation / claim in the Generated Content
that touches dimension `{DIM}`. The audit feeds the evidence list above:
unverified items become FLAG strings in your evidence and weigh the score
down, not silent passes.

A. **Source-attribution audit (all dims).** For every dictionary / style-guide / author cited in the Generated Content, use the single-call primitive `mcp__sources__verify_source_attribution(source, claim)` where `source` ∈ {`grinchenko_1907`, `esum`, `sum11`, `antonenko_davydovych`, `literary`, `heritage`, `wikipedia`, `style_guide`}. Verdict `discusses=false` → FLAG `unverified citation`, treat as score-against. The compose-pattern (calling `search_definitions` / `search_style_guide` / `search_grinchenko_1907` / `query_pravopys` / `search_esum` separately) is acceptable only when you need to inspect specific evidence chunks beyond the boolean verdict; for the audit pass itself, the single-call primitive is mandatory.

B. **Quote verification (all dims).** For every authored quote attributed to a literary source, call `mcp__sources__verify_quote(author, text)`. Required: `matched=true` AND `best_confidence ≥ 0.85`. Verdict false or confidence below threshold → FLAG `fabricated quote`. The tool detects fused composites (two real sources stitched into one attributed line) by returning `matched=false` with non-zero near-misses — flag those as `fused quote`. The compose-pattern (`mcp__sources__search_literary` + grep) is forbidden for this audit; use `verify_quote` exclusively.

C. **Sovietization flag (decolonization, naturalness).** When the content
   draws from `search_definitions` (СУМ-11) for politically loaded
   headwords (`ленін*`, `більшовик*`, `радянськ*`, `соціалістичн*`,
   `партійн*`, `національн*`, `школа`, `шлях`, `прапор`), apply
   heightened scrutiny. The result row's `sovietization_risk` field
   (0/1/2) is ground truth; until it is wired through the writer, fall
   back to the keyword regex above. Soviet framing reproduced into the
   module without paraphrase or correction → FLAG
   `soviet-framed definition unsupervised`.

D. **Modern Ukrainian + heritage-defense audit (naturalness, decolonization).** Flag historical / Old East Slavic / Russian-shadow / pre-Pravopys-2019 forms presented as modern Ukrainian. Also flag the opposite error: authentic Ukrainian archaisms, historisms, or dialectisms mislabeled as Russianism/surzhyk/calque without VESUM/check_modern_form plus historical/etymological/source-context verification. Authentic non-standard forms must carry `[Archaism]`, `[Historism]`, or `[Dialectism]`, a modern standard equivalent, and a brief heritage note. Missing tag/equivalent → FLAG `untagged heritage form`; false Russianism claim → FLAG `heritage form misclassified`.

Reviewers verifying a heritage flag MUST themselves call `mcp__sources__search_heritage` (or `mcp__sources__search_slovnyk_me` for a slovnyk.me-only check) before sustaining or rejecting a heritage claim. A reviewer evidence_quote that asserts heritage status without a tool-grounded citation is a reviewer-protocol failure.
When reviewing a writer heritage claim, verify that slovnyk.me citations use canonical `dictionary_slug` values from `scripts/wiki/slovnyk_me.py` and that merged `search_heritage` citations name `source_family`, `source`, and `classification` when no `dictionary_slug` is present. If the writer cites no raw tool-result excerpt, or if your own `search_heritage` call returns empty, treat the claim as unresolved rather than accepting a heritage or Russianism label.

E. **Reinforce rule #6.** Every claim pairs (i) a verbatim quote from the
   content and (ii) a specific MCP-grounded verification or an explicit
   absence-of-verification flag. A `PASS` with no grounded evidence is a
   reviewer-protocol failure.

F. **Activity split audit (pedagogical, engagement).** The writer is
contracted to emit two complementary activity sets per `ACTIVITY_CONFIGS[{LEVEL}]`:
INLINE (light, theory-time checks anchored via `<!-- INJECT_ACTIVITY: act-N -->`)
and WORKBOOK (substantive, after-lesson drill, no INJECT marker). For A1:
INLINE 4-6 / WORKBOOK 6-9 (10 total). For A2: INLINE 4-6 / WORKBOOK 8-11
(12 total). For B1-core/B2-core/C1-core: INLINE 5-7 / WORKBOOK 11-15
(16 total). For C2: INLINE 4-5 / WORKBOOK 8-10 (12 total).

The writer is required to emit a self-audit line
`<activity_split_audit>level={LEVEL} inline_n=N workbook_n=N inline_range=[lo,hi] workbook_range=[lo,hi] split_valid=true|false</activity_split_audit>`
before the artifact fences. Locate this line and verify:

1. The line is PRESENT. Missing → FLAG `activity_split_audit_missing`
   (counts as evidence-against this dim).
2. The reported `inline_n` matches the actual count of
   `<!-- INJECT_ACTIVITY: act-N -->` markers in `module.md`.
3. The reported `workbook_n` matches `len(activities.yaml) - inline_n`.
4. Both counts fall within the level's allowed ranges per §"Corpus Access" of
   the writer prompt.

If the writer's self-audit reports `split_valid=true` BUT the actual counts
violate the range, that is a worse failure than `split_valid=false` (a writer
lying in its own audit). FLAG `activity_split_audit_lied`.

Pedagogical consequence to score against: INLINE activities that are too
long/substantive (item count > 3, multi-paragraph rubrics) break their "fast
theory check" purpose; WORKBOOK activities that are too trivial (single-item
quizzes, no discrimination depth) break their drill purpose. Score the
BALANCE-vs-PURPOSE not just the count.

G. **Corpus-access audit (all dims).** The writer is gated to a level-specific
corpus surface per the Corpus Access (level-gated) table in `linear-write.md`.
Verify the writer did not cite out-of-level sources:

- **a1/a2 textbook scope**: only Grades 1-4 (a1) or 1-5 (a2) source files
  allowed in citations. A `Караман Grade 10` citation in an a1 module is OUT
  OF SCOPE. FLAG `out_of_level_textbook`.
- **a1/a2 literary scope**: only children's literature, folk songs,
  fairy-tale openings, iconic phrases. A Stus / Khvylovy / Zabuzhko /
  Pidmohylny quote in an a1/a2 module is a register break. FLAG
  `out_of_level_literary`. (The curated-tag filter — F1 — is not yet built;
  rely on author/work register judgment.)
- **a1/a2 external scope**: only `ulp_blogs`, `ulp_youtube`,
  `pohribnyi_pronunciation` from `search_external`. Citations from
  `istoria_movy`, `realna_istoria`, `komik_istoryk`, `imtgsh`, `other_blogs`
  at a1/a2 are out of scope. FLAG `out_of_level_external`.
- **b1+/seminars**: full corpus allowed; only flag if the writer claims a
  source NOT in our corpus at all (fabrication, separate failure class covered
  by audits A-B).

For ANY out-of-level citation, the quote may STILL be factually correct but the
register/source choice is wrong for the learner level. Score this as
PEDAGOGICAL evidence-against, not as a fabrication.

H. **Student-aware audit (pedagogical, engagement, naturalness).** The writer
is given a `{LEARNER_STATE}` block listing cumulative_vocabulary +
known_grammar from prior modules. Verify the writer:

1. **Did not re-explain already-taught grammar.** If the learner-state lists
   "Genitive case endings -а/-я" as known_grammar and this module derives the
   rule from scratch in 200+ words, FLAG `re_explained_known_grammar`. Brief
   reference (`як ти бачив у модулі 7`) is fine; a full re-derivation is not.

2. **Did not introduce unknown vocabulary without inline gloss.** Scan
   `module.md` prose for Ukrainian content words. For any word that is (a) NOT
   in cumulative_vocabulary, (b) NOT in this module's `vocabulary.yaml`, (c)
   NOT a proper noun / Latin borrowing, and (d) NOT introduced with inline
   italic gloss `*(translation)*`, FLAG `unknown_vocab_unscaffolded`.

3. **Foreshadowing pattern visible.** If new lemmas appear in prose BEFORE
   their `vocabulary.yaml` entry, they should carry inline gloss at first
   mention. Absence of gloss on first mention = `missing_foreshadowing_gloss`.

4. **Stacked vocab-level check evidence.** For non-plan lemmas the writer
   introduced, check the `<plan_reasoning>` for `<vocab_level_check>` nodes.
   Missing for a non-plan lemma = `unverified_vocab_introduction`.

Pedagogical score: respecting the learner's prior knowledge is what makes the
module BUILD instead of REPEAT. Naturalness score: scaffolded vocabulary
introduction reads as a real teacher's voice; un-introduced vocab feels like a
textbook dump.

I. **Pre-emit audit-line integrity (all dims).** The writer is required to
emit three machine-readable audit lines BEFORE the artifact fences, in order:

1. `<implementation_map_audit>manifest_obligations=N covered_in_map=M missing=[...]</implementation_map_audit>`
   (per #2094)
2. `<bad_form_audit>italic_bad_form_patterns_found=N converted_to_marker=N remaining=0</bad_form_audit>`
   (per #2095)
3. `<activity_split_audit>level={LEVEL} inline_n=N workbook_n=N inline_range=[lo,hi] workbook_range=[lo,hi] split_valid=true|false</activity_split_audit>`
   (per the just-merged Activity Types section)

Verify ALL THREE lines are present, parseable, and report values consistent
with the artifacts. Any missing line = the writer has failed the protocol;
FLAG `audit_line_missing` with the missing line name. Any line whose claim
doesn't match the artifacts = FLAG `audit_line_inconsistent`.

These audits exist BECAUSE the writer is doing self-grading; the reviewer's
job here is to cross-check that the self-grading matches reality. A green audit
line on broken content is a more serious failure than a red audit line on
broken content (the writer is lying to its own audit).

Return only JSON:

```json
{"score": 0.0, "evidence_quotes": ["verbatim quote 1", "verbatim quote 2", "verbatim quote 3"], "rubric_mapping": "Quote 1: ...; Quote 2: ...; Quote 3: ...", "evidence": "\"verbatim quote from evidence_quotes\"", "flags": ["activity_split_audit_missing", "out_of_level_literary", "..."], "verdict": "REVISE"}
```

The `flags` array MUST contain any FLAG strings raised during audits A-I that
apply to your assigned dim per the per-dim labeling in §"Scope". An empty array
is fine when no flags fired. The pipeline aggregates flags across dims and
surfaces them in the build telemetry; the writer's self-correction loop reads
them to know what to fix on retry.

## Module Context

- Level: {LEVEL}
- Module: {MODULE_NUM}
- Slug: {MODULE_SLUG}
- Word target: {WORD_TARGET}

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

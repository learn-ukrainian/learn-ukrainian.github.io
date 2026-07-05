# Calibration Criteria & Level Profiles for LLM Quality Gate Reviewer

This document defines the calibration criteria, level profiles, false-positive/false-negative controls, and structural validation specifications implemented for the LLM reviewer layer in the Ukrainian-quality gates evaluation harness (#4309).

> [!NOTE]
> **Deterministic Layer Precedence**:
> Lexical Russianisms, orthography, and baseline grammar validation are handled FIRST by deterministic gates (#4308, #912, curriculum QG). The LLM reviewer pass acts as a supplementary gate for style, register, and stylistic calques.

---

## 1. Level Profiles & Immersion Policies

Linguistic expectations and immersion rules are strictly partitioned by target CEFR level:

### A1/A2 (Scaffolded Support)
* **Goal**: Provide beginner-appropriate bilingual grounding.
* **Scaffolding Policy**: Substantial English instruction and translation scaffolding are expected and allowed.
* **Defect Handling**: Do NOT flag English text as leakage. English is only rejected if it contains AI personae, temporary paths, or internal metadata.
* **Max-Immersion Constraint**: Never recommend increasing the English ratio or adding English translations where Ukrainian-only content exists. Respect the level's maximum immersion goal.

### B1+ (Ukrainian-led Immersion)
* **Goal**: Transition learners to full immersion.
* **Immersion Policy**: All instructional prose, grammar explanations, and metadata directions must be written in natural Ukrainian.
* **Defect Handling**: Any English-led paragraphs or English explanations are flagged as `ENGLISH_LEAKAGE` (`level_policy` dimension, `critical` severity).
* **Gloss Exemption**: Brief bilingual vocabulary glosses (e.g. `**Застосунок** - app.`) are allowed and must not be flagged.

### Seminar Register & Factual Sensitivity (bio, folk, hist, istorio, lit, oes, ruth, etc.)
* **Goal**: Achieve scholarly register, factual correctness, and historical sensitivity.
* **Pathos/Register Control**: Strictly avoid marketing language, enthusiastic hype, and patriotic slogans (e.g., "неймовірна подорож", "пориньмо у захопливий світ"). The register must remain objective and formal.
* **Vital Status Check**:Biography modules must verify whether the subject is living or deceased. For LIVING subjects, headers or prose sections implying death or legacy (e.g., "Last Years" / `Останні роки` or "Legacy" / `Спадщина`) are strictly forbidden as they mimic obituaries. Instead, use "Contemporary Stage" / `Сучасний етап` or "Influence" / `Вплив`.
* **Factual Grounding**: All historical and cultural details must be verified against primary resources (e.g., `litopys.org.ua`). The YouTube channel "REALNA ISTORIIA" (Akim Galimov) is the gold standard for historical modules. Reject low-quality propaganda channels.

---

## 2. Severity Calibration Guidelines
* **critical**: Factual errors, resource/evidence/pipeline leakages (AI personae, absolute paths), missing mandatory structural elements (such as model answers in B2+), and severe grammatical errors (such as case alignment or predicative-instrumental errors).
* **warning**: Style and register issues (unnatural/syntactic calques, unnatural metalanguage/register, minor prepositions), or pedagogical mismatches.
* **info**: Non-critical suggestions, minor stylistic alternatives, or optional improvements.

---

## 3. B1-27 Calibration Criteria (HARD Calibration)

The B1-27 *restored-bad* examples contain unidiomatic or calqued Ukrainian constructions that are not lexical Russianisms (pure Russian words) but are stylistic/syntactic defects. The reviewer must detect:

| Restored-Bad Phrase | Expected Issue ID | Dimension | Severity | Target Idiomatic Ukrainian | Rationale |
|---|---|---|---|---|---|
| `застосунок має бути відкритий` | `AWKWARD_PASSIVE_RESULT_STATE` | `ukrainian_style` | `critical` | `відкрийте застосунок` / `застосунок має бути відкритим` | Predicative-instrumental case error (nominative instead of instrumental). Do NOT flag 'має бути відкритим'. |
| `Застереження каже: будь обережний` | `UNNATURAL_ANTHROPOMORPHISM` | `ukrainian_style` | `warning` | `Зверніть увагу` / `Будьте обережні` | Abstract warnings must not speak. Scoped strictly to metalanguage; do NOT flag natural personifications like 'правило каже'. |
| `радить не робити певної поведінки` | `UKRAINIAN_GRAMMAR_CALQUE` | `ukrainian_style` | `warning` | `рекомендує уникати...` | Unnatural verbal government and nominalization calque. Downgraded to warning. |
| `дія має дати конкретний результат чи описати процес?` | `UNNATURAL_META_REGISTER` | `ukrainian_style` | `warning` | (Avoid in learner-facing text) | AI/reviewer metalanguage / dry syntactic jargon in learner-facing text. Downgraded to warning. |
| `доконаний вид дає результат із вікном` | `UKRAINIAN_GRAMMAR_CALQUE` | `ukrainian_style` | `warning` | `доконаний вид позначає результат...` | Literal calqued metaphor and unidiomatic argument structure. Downgraded to warning. |
| `У кухні` | `CALQUED_PREPOSITION` | `ukrainian_style` | `warning` | `На кухні` | Location prep calque. Downgraded to warning; do not auto-fail in informal contexts. |

---

## 3. False-Positive / False-Negative Controls

To maintain high precision, the LLM reviewer must distinguish actual defects from valid teaching contexts:

* **Contrastive Examples**: The presence of a bad form (e.g., in a "Correct vs Incorrect" table or strikethrough like `~~wrong form~~`) is a `teaching_contrast` or `quoted_bad_form` disposition and must not penalize the module.
* **Heritage/SUM Attestation**: Authentic Ukrainian archaisms, dialectal forms, and complex syntax validated by VESUM/СУМ/Grinchenko must not be flagged as calques or Russianisms.
* **Level Simplicity**: A1/A2 grammatical simplicity (e.g., SVO rigidity or explicit copula `є` in early A1) must not be flagged as unnatural.

---

## 4. Structural Model Answer Check Spec

For modules graded at level B2, C1, or C2, all productive writing tasks (specifically `type: essay-response` in `activities.yaml`) must contain a `model_answer` field, and the answer must start with the markdown callout:
```markdown
> [!model-answer]
```
If missing, it triggers a `MISSING_MODEL_ANSWER` defect:
* **Dimension**: `pedagogical`
* **Severity**: `critical`
* **Disposition**: `defect`
* **Confidence**: `deterministic`

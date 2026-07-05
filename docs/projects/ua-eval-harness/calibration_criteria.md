# Calibration Criteria & Level Profiles for LLM Quality Gate Reviewer

This document defines the calibration criteria, level profiles, false-positive/false-negative controls, and structural validation specifications implemented for the LLM reviewer layer in the Ukrainian-quality gates evaluation harness (#4309).

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

## 2. B1-27 Calibration Criteria (HARD Calibration)

The B1-27 *restored-bad* examples contain unidiomatic or calqued Ukrainian constructions that are not lexical Russianisms (pure Russian words) but are stylistic/syntactic defects. The reviewer must detect:

| Restored-Bad Phrase | Expected Issue ID | Dimension | Target Idiomatic Ukrainian | Rationale |
|---|---|---|---|---|
| `застосунок має бути відкритий` | `AWKWARD_PASSIVE_RESULT_STATE` | `ukrainian_style` | `відкрийте застосунок` / `застосунок має бути відкритим` | Impersonal/active voice is preferred over literal passive state translations. |
| `Застереження каже: будь обережний` | `UNNATURAL_ANTHROPOMORPHISM` | `ukrainian_style` | `Зверніть увагу` / `Будьте обережні` | Abstract warning blocks must not be anthropomorphized as speakers. |
| `радить не робити певної поведінки` | `UKRAINIAN_GRAMMAR_CALQUE` | `ukrainian_style` | `рекомендує уникати...` | Unnatural verbal government and nominalization. |
| `дія має дати конкретний результат чи описати процес?` | `UNNATURAL_META_REGISTER` | `ukrainian_style` | (Avoid in learner-facing text) | Overly abstract syntactic metalanguage / prompt leakage. |
| `доконаний вид дає результат із вікном` | `UKRAINIAN_GRAMMAR_CALQUE` | `ukrainian_style` | `доконаний вид позначає результат...` | Literal calqued metaphor and unidiomatic argument structure. |
| `У кухні` | `CALQUED_PREPOSITION` | `ukrainian_style` | `На кухні` | Location prep calque; "На кухні" is the standard locative context. |

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

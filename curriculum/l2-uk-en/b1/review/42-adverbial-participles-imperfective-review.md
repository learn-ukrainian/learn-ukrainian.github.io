# Module 42: Дієприслівники недоконаного виду

**Template:** b1-grammar-module-template.md | **Compliance:** ✅ PASS
**Overall Score:** 9.0/10
**Status:** ✅ PASS
**Generated:** 2026-01-24 22:42:00
**Reviewer:** Gemini

## Scores Breakdown

| Dimension           | Score | Notes                                                               |
| ------------------- | ----- | ------------------------------------------------------------------- |
| Coherence           | 10/10 | Logical progression from conjugation rules to participle formation. |
| Relevance           | 10/10 | Essential B1 grammar topic.                                         |
| Educational         | 10/10 | Explicitly teaches stem changes (pisaty -> pyshu -> pyshuchy).      |
| Language            | 10/10 | Explanations and examples are linguistically precise.               |
| Pedagogy            | 9/10  | Good use of "Myth Buster" to contrast with Russian/English.         |
| Immersion           | 9/10  | High.                                                               |
| Activities          | 10/10 | Excellent distractors (e.g., *писаючи* vs *пишучи*).                |
| Richness            | 8/10  | Good cultural history bite (Kyiv-Mohyla Academy).                   |
| Humanity            | 9/10  | Warm tone.                                                          |
| LLM Fingerprint     | 9/10  | No issues.                                                          |
| Linguistic Accuracy | 6/10  | Content is 10/10, but Vocabulary YAML contains significant garbage. |

## Linguistic Accuracy Issues

- **Vocabulary File Garbage:** The `vocabulary/42-adverbial-participles-imperfective.yaml` file contains many broken lemmas: `писа-`, `ши`, `ючи`, `їдячати`, `пиш-учити`, `писа-ючи`.
- **False Lemma:** `сплячий` is listed but is an adjective (active participle), not an adverbial participle.
- **Incorrect Form:** `радіючись` is listed; correct form is `радіючи` (verb `радіти` is not reflexive).

## Strengths

- **Grammar Precision:** The module correctly identifies that adverbial participles derive from the 3rd person plural stem (пишуть -> пишучи), not the infinitive.
- **Distractor Design:** Activities effectively target common errors like using the infinitive stem instead of the present stem.
- **Cultural Context:** The Kyiv-Mohyla Academy context is relevant to the topic of "writing/studying".

## Issues

- **Vocabulary YAML Quality:** The vocabulary file needs a manual cleanup to remove hallucinated tokens. This does not affect the lesson content but affects the flashcard system.

## Recommendation

✅ PASS — The lesson content is excellent. The vocabulary file issues are a data hygiene task, not a pedagogical failure of the module text.

## Action Items

1. **Cleanup Vocab YAML:** Remove `писа-`, `ши`, `ючи`, `їдячати`, `пиш-учити`, `писа-ючи`.
2. **Fix Vocab Entries:** Change `радіючись` to `радіючи`. Remove `сплячий` (or reclassify as adjective).

# Unit 6 Phase A — Baseline (Claude writer / Codex reviewer)

- Outcome: FAIL
- module_done emitted: no
- MIN dim score: N/A (review not reached)
- Convergence rounds used: 0
- Audit gates: failed before audit: activity-pre-validate
- Build wall clock: 46m20s

## Per-dim scores

Review did not run because the build failed in Step 5g before audit/review.

| Dim | Score | Verdict |
|---|---:|---|
| factual | N/A | not reached |
| language | N/A | not reached |
| decolonization | N/A | not reached |
| completeness | N/A | not reached |
| actionable | N/A | not reached |
| naturalness | N/A | not reached |
| plan_adherence | N/A | not reached |
| honesty | N/A | not reached |
| dialogue | N/A | not reached |

## Notable findings

- Phase 1 + 2 preflight checks passed before the build.
- Build ran with `--writer claude-tools --reviewer codex-tools`.
- Write phase completed on attempt 2 after fixing the required `Підсумок` heading and contract anchor issues.
- Activity generation required retries. The final terminal failure was activity pre-validation: answer words were not grounded in prose or plan vocabulary: `гриб`, `казка`, `лис`.
- No audit status JSON or review round was produced because the build failed before audit/review.

## Prose excerpt (first dialogue + first letter activity)

First dialogue from `produced-module.md`:

> **Вчитель:** Добрий день, діти!
> *Teacher: Good day, children!*
> **Учні:** Добрий день!
> *Pupils: Good day!*
> **Вчитель:** Як справи?
> *Teacher: How are things?*
> **Учні:** Добре!
> *Pupils: Good!*
> **Марко:** Привіт, Софіє!
> *Marko: Hi, Sofiia!*
> **Софія:** Привіт, Марку! Як справи?
> *Sofiia: Hi, Marko! How are things?*
> **Марко:** Чудово.
> *Marko: Great.*

First letter activity from `activities.yaml`:

```yaml
- type: letter-grid
  instruction: Голосні — Vowels
  letters:
  - upper: А
    lower: а
    key_word: ананас
    sound_type: vowel
  - upper: О
    lower: о
    key_word: око
    sound_type: vowel
  - upper: У
    lower: у
    key_word: Україна
    sound_type: vowel
```

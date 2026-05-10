# Unit 6 Phase B — Experiment (gpt-5.5 writer / Claude reviewer)

- Outcome: FAIL
- module_done emitted: no
- MIN dim score: 6.0 (naturalness)
- Convergence rounds used: 1 review round; terminal `plan_revision_request` before r2
- Audit gates: NOT RUN - build failed during review before audit/status generation
- Build wall clock: 53m

## Per-dim scores

| Dim | Score | Verdict |
|---|---:|---|
| Factual | 9.2 | PASS |
| Language | 8.8 | PASS |
| Decolonization | 9.0 | PASS |
| Completeness | 7.5 | REVISE |
| Actionable | 8.7 | PASS |
| Naturalness | 6.0 | REVISE |
| Plan Adherence | 7.5 | REVISE |
| Honesty | 9.0 | PASS |
| Dialogue | 9.0 | PASS |

## Notable findings

- Build command used the required flip: `--writer codex-tools --reviewer claude-tools`.
- Write passed on attempt 2 after built-in contract correction; final prose was 1507 words.
- Verification was degraded because `data/vesum.db` was missing; Russicism scan passed.
- Review terminal-failed after round 1 with `plan_revision_request`; no audit/status JSON was produced.
- Naturalness drove the failure. Claude flagged repeated word-gloss substitution patterns, mixed-language splices such as `На відміну від English`, and forced lexical insertions.
- Completeness and plan adherence also required revision: missing Ohoiko vowel-video mention in prose, missing explicit `у/в` and `і/й` rule, missing stress-as-meaning minimal pairs, and a greeting `fill-in` marker placed before the greeting section.

## Prose excerpt (first dialogue + first letter activity)

First dialogue:

```markdown
> Вчитель: «Добрий день!» (Good afternoon!)
>
> Учні: «Добрий день!» (Good afternoon!)
>
> Вчитель: «Привіт! Як справи?» (Hi! How are things?)
>
> Учень: «Добре.» (Good.)
>
> Учениця: «Чудово.» (Great.)
>
> Учень: «Нормально. А у тебе?» (Fine. And you?)
>
> Вчитель: «Добре.» (Good.)
```

First letter activity excerpt:

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
  id: letter-grid-7
```

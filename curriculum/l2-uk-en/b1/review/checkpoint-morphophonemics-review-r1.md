## Linguistic Scan
- `приголоном` — typo (should be `приголосним`).
- `втікаючі голосні` — unnatural active participle/calque (should be `випадні голосні`).
- `втікає` — continuation of the calque (should be `випадає`).
- `бере аналіз` — colloquialism/calque (should be `бере кров на аналіз`).
- `приймати таблетки` — calque from Russian (should be `пити таблетки` або `вживати таблетки`).

## Exercise Check
- `<!-- INJECT_ACTIVITY: quiz-choosing-between-based-on-completion-vs-ongoing-action -->` — **Issue:** Hallucinated marker. Does not match the 6 hints in `activity_hints`.
- `<!-- INJECT_ACTIVITY: fill-in-completing-descriptions-of-people-and-their-relationships -->` — **Issue:** Hallucinated marker. Does not match `activity_hints`.
- `<!-- INJECT_ACTIVITY: quiz-alternation-type -->` — Matches `quiz`.
- `<!-- INJECT_ACTIVITY: match-alternated-forms -->` — Matches `match-up`.
- `<!-- INJECT_ACTIVITY: fill-in-declension-context -->` — Matches `fill-in`.
- `<!-- INJECT_ACTIVITY: error-correction-morphophonemics -->` — Matches `error-correction`.
- `<!-- INJECT_ACTIVITY: sort-noun-subclasses -->` — Matches `group-sort`.
- `<!-- INJECT_ACTIVITY: comprehension-medical-grammar -->` — Matches `reading-comprehension`.

**Summary:** The plan calls for 6 activities. The generated text includes 8 markers. The first two are hallucinated based on the outline text rather than the `activity_hints` block and must be removed.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | All required grammatical topics (alternations, noun declensions, pluralia tantum, tenses) are well-covered. The dialogue explicitly follows the quiz show prompt: "Уявіть собі велику телевізійну студію... фінал популярного інтелектуального шоу". |
| 2. Linguistic accuracy | 7/10 | Several critical and major errors. Typo: "класичним губним (labial) приголоном". Unnatural linguistic terms: "втікаючі голосні", "звук [о] так само втікає". Calques: "бере аналіз", "приймати таблетки". |
| 3. Pedagogical quality | 10/10 | Excellent pedagogical breakdown. "Коли ви бачите нове українське слово, спершу запитайте себе: чи змінюється тут форма складу?" is a great diagnostic rule. The contrast between "стіл" and "стілець" is pedagogically very strong. |
| 4. Vocabulary coverage | 8/10 | Required vocabulary is fully present. However, recommended words `сонорний` and `діагноз` are entirely missing from the text (verified via search). |
| 5. Exercise quality | 8/10 | Hallucinated extra markers injected at the beginning of the text (`quiz-choosing-between-based-on-completion-vs-ongoing-action` and `fill-in-completing-descriptions-of-people-and-their-relationships`) that do not match the YAML plan hints. |
| 6. Engagement & tone | 9/10 | The text starts with a forbidden self-congratulatory opener: "Вітаємо на першій великій контрольній роботі рівня B1! Ми з вами пройшли важливий шлях від повторення базової граматики до розуміння складної української морфонеміки." Otherwise, the teacher's tone is excellent. |
| 7. Structural integrity | 10/10 | Word count is solid (4924 words). Markdown headings perfectly map to the plan. No dangling sentences or meta-commentary. |
| 8. Cultural accuracy | 10/10 | Excellent use of authentic, historically deep Ukrainian forms like the instrumental plural "грішми" and "ворітьми". No colonial framing. |
| 9. Dialogue & conversation quality | 10/10 | The dialogue is engaging and successfully forces the use of grammar rules within a naturalistic quiz show format. The host's follow-up questions ("Яке саме чергування голосних відбувається у базовому слові...") are well-executed. |

## Findings

[2. Linguistic accuracy] [critical]
Location: section "Медична лексика та морфонеміка", paragraph 3: "звук [в] є класичним **губним** (*labial*) приголоном."
Issue: Typo/non-existent word "приголоном" instead of "приголосним".
Fix: Replace "приголоном" with "приголосним".

[2. Linguistic accuracy] [critical]
Location: section "Огляд чергувань", paragraph 2: "так звані «втікаючі голосні» або **нульове закінчення**"
Issue: The term "втікаючі голосні" uses an unnatural active participle ("-учий/-ючий"), which is a calque and non-normative in Ukrainian linguistics. The correct term is "випадні голосні".
Fix: Replace "втікаючі голосні" with "випадні голосні".

[2. Linguistic accuracy] [major]
Location: section "Огляд чергувань", paragraph 2: "звук [о] так само втікає перед закінченням родового відмінка"
Issue: "втікає" is a stylistic extension of the "втікаючі" calque. It should use the standard linguistic term "випадає".
Fix: Replace "втікає" with "випадає".

[2. Linguistic accuracy] [major]
Location: section "Медична лексика та морфонеміка", paragraph 3: "Коли медсестра бере аналіз, вона може випадково"
Issue: "бере аналіз" is a colloquialism/calque; standard phrasing is "робить аналіз" or "бере кров на аналіз".
Fix: Replace "бере аналіз" with "бере кров на аналіз".

[2. Linguistic accuracy] [major]
Location: section "Медична лексика та морфонеміка", paragraph 5: "маззю та приймати таблетки після їжі"
Issue: "приймати таблетки" is a common calque from Russian "принимать таблетки"; standard Ukrainian prefers "пити таблетки" or "вживати ліки".
Fix: Replace "приймати таблетки" with "пити таблетки".

[5. Exercise quality] [major]
Location: section "Огляд базових часів та лексики (M01-M03)", paragraphs 3 and 5.
Issue: Two hallucinated exercise injection markers (`<!-- INJECT_ACTIVITY: quiz-choosing-... -->` and `<!-- INJECT_ACTIVITY: fill-in-completing-... -->`) do not match the `activity_hints` provided in the plan (which specifies exactly 6 activities).
Fix: Remove the two extra injection markers.

[6. Engagement & tone] [minor]
Location: section "Огляд базових часів та лексики (M01-M03)", paragraph 1: "Вітаємо на першій великій контрольній роботі рівня B1! Ми з вами пройшли важливий шлях від повторення базової граматики до розуміння складної української морфонеміки. Уявіть, що ви — учасник..."
Issue: Violates the rule against self-congratulatory openers. 
Fix: Remove the first two sentences to start directly with the quiz show scenario.

[4. Vocabulary coverage] [minor]
Location: Entire text.
Issue: Recommended vocabulary words `сонорний` and `діагноз` are completely missing from the prose.
Fix: No find/replace fix is strictly required for recommended vocabulary, but points were deducted.

## Verdict: REVISE
The module is incredibly detailed and achieves a high word count with solid pedagogical explanations, but it contains critical linguistic inaccuracies (a typo, unnatural terminology like "втікаючі голосні", and several calques) as well as hallucinated activity markers that will break the pipeline. A revision is required to apply the necessary fixes.

<fixes>
- find: "звук [в] є класичним **губним** (*labial*) приголоном."
  replace: "звук [в] є класичним **губним** (*labial*) приголосним."
- find: "так звані «втікаючі голосні» або **нульове закінчення**"
  replace: "так звані «випадні голосні» або **нульове закінчення**"
- find: "звук [о] так само втікає перед закінченням родового"
  replace: "звук [о] так само випадає перед закінченням родового"
- find: "Коли медсестра бере аналіз, вона може випадково"
  replace: "Коли медсестра бере кров на аналіз, вона може випадково"
- find: "маззю та приймати таблетки після їжі"
  replace: "маззю та пити таблетки після їжі"
- find: "Вітаємо на першій великій контрольній роботі рівня B1! Ми з вами пройшли важливий шлях від повторення базової граматики до розуміння складної української морфонеміки. Уявіть, що ви — учасник"
  replace: "Уявіть, що ви — учасник"
- find: "<!-- INJECT_ACTIVITY: quiz-choosing-between-based-on-completion-vs-ongoing-action -->\n"
  replace: ""
- find: "<!-- INJECT_ACTIVITY: fill-in-completing-descriptions-of-people-and-their-relationships -->\n"
  replace: ""
</fixes>

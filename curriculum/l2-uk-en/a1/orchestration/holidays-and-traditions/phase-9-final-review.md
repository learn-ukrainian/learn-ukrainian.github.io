Good — the vocabulary file exists and is populated. Now I have everything I need for the deep review.

---

## Phase 9 Final QA Review: holidays-and-traditions (a1-33)

**Word count:** ~2849 (target: 2000) — well above minimum. Content is rich.

---

### Issues Found

**1. Russicism in case government (CRITICAL)**
File: `holidays-and-traditions.md`, line 23
> "Ми чекаємо дванадцяту годину."

The verb "чекати" + bare Accusative is a Russian calque (ждать + Acc). Standard Ukrainian requires either "чекати **на** + Acc" or "чекати + Gen": "чекаємо **на** дванадцяту годину" or "чекаємо дванадцятої години."

**2. Fabricated greeting in fill-in activity (CRITICAL)**
File: `activities/holidays-and-traditions.yaml`, lines 160-163
> `'З {{answer}} днем!'` → answer: `'гарним'`

"З гарним днем!" is **not** a real Ukrainian expression. Nobody says this. Ukrainians say "**Гарного дня!**" (Genitive) or "**Доброго дня!**" This activity teaches a phrase that doesn't exist, which is worse than teaching nothing.

**3. Quiz contradicts content on Leontovych (MEDIUM)**
File: `activities/holidays-and-traditions.yaml`, line 80
> `'Хто написав музику до всесвітньо відомого «Щедрика»?'`

The content (line 35) correctly says "**обробив**" (arranged). But the quiz says "написав музику" (wrote the music). Leontovych did not compose the melody — he created a choral arrangement of an existing folk song. The quiz explanation (line 81) correctly says "створив обробку," so the question framing contradicts its own explanation.

**4. Untaught vocabulary in activity (MEDIUM)**
File: `activities/holidays-and-traditions.yaml`, lines 273-276
> `'Писанка'` → `'Великоднє яйце'`
> `'Вишиванка'` → `'Святковий одяг'`

Neither "писанка" nor "вишиванка" appears anywhere in the lesson content. Activities must test what was taught. These terms are also absent from the plan's `vocabulary_hints`. Replace with terms that ARE in the content.

**5. Overstatement presented as fact (LOW)**
File: `holidays-and-traditions.md`, line 33
> "Найвідоміша різдвяна пісня у світі — українська."

"The most famous Christmas song in the world is Ukrainian" is a contested factual claim ("Silent Night," "White Christmas," "Jingle Bells" all have strong counter-claims). Softening to "одна з найвідоміших" preserves the cultural pride without teaching a debatable fact.

**6. Non-standard anglicism (LOW)**
File: `holidays-and-traditions.md`, line 116
> "Ваш **бос** бажає вам успіху."

"Бос" is an informal English borrowing. At A1, learners should acquire standard vocabulary. "Керівник" (manager/boss) is standard Ukrainian and more useful.

---

### Checks Passed (No Issues)

- **IPA accuracy**: Tie bars present on affricates ([ˈʃt͡ʃɑstʲɐ]), ʋ used for В ([lʲuˈbɔʋʲi]), all IPA correct
- **No Russian characters** (ы, э, ё, ъ): clean scan
- **No other Russianisms**: "дивляться телевізор" ✓, "святкувати" ✓, "дарувати" ✓
- **Gender/case agreement**: all checked, correct (including "твоїй родині" Dat.fem ✓)
- **Unjumble word arrays**: all 6 items have exact word-answer correspondence ✓
- **Fill-in grammaticality**: all items (except #2 above) produce correct sentences ✓
- **Plan compliance**: all 4 plan content_outline sections present, all 8 required vocab items used in prose ✓
- **Objectives → self-check mapping**: all 4 objectives covered ✓
- **Factual accuracy**: Christmas Dec 25 ✓, St. Nicholas Dec 6 ✓, 12 dishes ✓, Kutia ✓, День Незалежності Aug 24 ✓
- **No LLM artifacts**: no purple prose, no "Це не просто X, а Y", no fake statistics
- **Activity YAML format**: bare list at root ✓, no `activities:` wrapper ✓

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/holidays-and-traditions.md
---OLD---
Люди готують їжу. Люди дивляться телевізор. Ми чекаємо дванадцяту годину.
---NEW---
Люди готують їжу. Люди дивляться телевізор. Ми чекаємо на дванадцяту годину.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/holidays-and-traditions.md
---OLD---
Найвідоміша різдвяна пісня у світі — українська.
---NEW---
Одна з найвідоміших різдвяних пісень у світі — українська.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/holidays-and-traditions.md
---OLD---
Ваш бос бажає вам успіху.
---NEW---
Ваш керівник бажає вам успіху.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/holidays-and-traditions.yaml
---OLD---
    - sentence: 'З {{answer}} днем!'
      answer: 'гарним'
      options: ['гарним', 'гарний', 'гарного', 'гарна']
      explanation: 'Instrumental case adjective: гарний -> гарним.'
---NEW---
    - sentence: 'Вітаю з {{answer}}!'
      answer: 'іменинами'
      options: ['іменинами', 'іменини', 'іменин', 'іменинам']
      explanation: 'Instrumental case: іменини -> іменинами.'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/holidays-and-traditions.yaml
---OLD---
    - question: 'Хто написав музику до всесвітньо відомого «Щедрика»?'
      explanation: 'Микола Леонтович створив обробку народної пісні, яка стала Carol of the Bells.'
---NEW---
    - question: 'Хто створив знамениту обробку «Щедрика»?'
      explanation: 'Микола Леонтович створив хорову обробку народної пісні, яка стала Carol of the Bells.'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/holidays-and-traditions.yaml
---OLD---
    - left: 'Писанка'
      right: 'Великоднє яйце'
    - left: 'Вишиванка'
      right: 'Святковий одяг'
---NEW---
    - left: 'Щедрик'
      right: 'Різдвяна щедрівка'
    - left: 'Святвечір'
      right: 'Вечір перед Різдвом'
===FIX_END===

---

===VERDICT===
APPROVE
===END_VERDICT===

**Rationale:** The module is strong — excellent cultural depth, correct pedagogy, well above word target (2849/2000), solid activities. The six issues found are all fixable with the patches above. The one critical Russicism ("чекаємо дванадцяту годину") is a single-word fix. The fabricated phrase ("З гарним днем!") is replaced with a phrase actually taught in the content. The Leontovych quiz question is reworded to match the content's correct "обробив" framing. After these fixes, the module is clean.
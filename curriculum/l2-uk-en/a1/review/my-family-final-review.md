Good — the unjumble convention across the project omits punctuation, so the missing commas/question marks in unjumble answers are project-consistent, not bugs. Now I have everything I need for the review.

---

## Adversarial QA Review: my-family (A1 #32)

### Ukrainian Language Quality

**IPA transcriptions**: All checked — correct. Affricates have tie bars (t͡ʃ, t͡s), В is consistently [ʋ], stress placement accurate across all 30+ transcriptions.

**Russianisms**: None detected. No кушати, получати, приймати участь, слідуючий. No Russian characters (ы, э, ё, ъ).

**Gender/case agreement**: Correct throughout. "Мій тато" (masc despite -о ending) is explicitly taught and consistently applied.

**Minor IPA note** (not blocking): Line 51 uses **матір** [ˈmɑtʲir] while the activities file line 20 uses **Мати** — these are variant nominative forms of the same word. "Мати" is the standard modern literary form; "матір" is older. Since the content says "stick to мама" and barely mentions this word, the practical impact is zero. Not fixing.

### Pedagogical Correctness

**ISSUE 1 (CRITICAL): Match-up tests untaught vocative forms**

The content explicitly limits vocative teaching to 4 forms: "You don't need to learn the whole grammar table yet, but you MUST know these four forms for your family." (line 435). The phone dialogue (line 413) also models **сину**.

But the match-up "Кличний відмінок" (activities lines 160-179) includes 3 pairs the learner has no way to derive:
- `Брат → Брате!` — NEVER taught or modeled
- `Сестра → Сестро!` — NEVER taught or modeled
- `Донька → Доню!` — NEVER taught or modeled (and "Доню" has a non-obvious stem change)

This is a direct teach-then-test violation. The learner cannot reason from the 4 taught forms to these 3 untaught ones because each follows a different declension pattern.

**ISSUE 2 (CRITICAL): Fill-in tests untaught vocative forms**

Fill-in "Звертання до рідних" (activities lines 209-216) includes:
- Item 7: answer "Брате" — NOT taught in content
- Item 8: answer "Сестро" — NOT taught in content

Same violation: the learner has no basis to select the correct answer.

**ISSUE 3 (MINOR): Missing comma before vocative in phone dialogue**

Line 412: `— Алло, привіт мамо!` — Ukrainian punctuation requires a comma before vocative address. Should be `— Алло, привіт, мамо!`

This is ironic because the module is teaching vocative forms — the punctuation around vocatives should be exemplary.

**Unjumble activities**: All words arrays contain exactly the tokens in the answer. Punctuation omission is consistent with project convention (verified against other A1 unjumble activities). No issues.

**Fill-in grammar**: All other fill-in items produce grammatically correct sentences when the answer is inserted. Verified all 24 non-vocative items.

### Factual Accuracy

- "Ненька Україна" — accurate cultural reference
- Distinction between сім'я (nuclear) and родина (extended) — accurate
- "баба can sound rough or disrespectful" — accurate sociolinguistic note
- Dative case for age expressions — correctly identified as A2 material
- All translations correct

### LLM Artifacts

- "Here is a special superpower" (line 433) — mild cliché but acceptable for A1's supportive tone
- No "Це не просто X, а Y" pattern
- No false statistics or invented percentages
- No folk etymology presented as fact
- Tone is warm and appropriate throughout

### Plan Compliance

- **Sections**: All 6 meta outline sections present and substantive ✅
- **Required vocabulary** (8 items): All present in prose ✅
- **Recommended vocabulary** (8 items): All present ✅
- **Objectives**: All 5 mapped to content and self-check questions ✅
- **Grammar**: Possessives ✅, "У мене є..." ✅, Vocative ✅
- **Minor deviation**: Meta requests "simple number phrases (25 років)" for age. Content defers to A2. This is pedagogically sound — the age construction requires Dative case + numeral agreement, which is genuinely beyond A1. The adjective-based approach (молодий/старий/дорослий/маленький) is appropriate.
- **Minor deviation**: Plan grammar includes "Genitive for relationships (батько + name)" but content uses "Його звати..." pattern instead. The genitive pattern does appear in the activity "Хто це?" (e.g., "Сестра мами → Тітка") so it's tested receptively even if not explicitly drilled.

### Content note

Line 169 uses **двоюрідний брат** (cousin) in the family tree text without explicit explanation. It's in a reading comprehension context where the preceding sentence ("Моя тітка має чоловіка... У них є син") makes the meaning inferrable. Acceptable for A1.3 Consolidation phase but worth flagging — a parenthetical "(cousin)" would help.

---

## Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/my-family.yaml
---OLD---
    - left: "Син"
      right: "Сину!"
    - left: "Брат"
      right: "Брате!"
    - left: "Сестра"
      right: "Сестро!"
    - left: "Донька"
      right: "Доню!"
---NEW---
    - left: "Син"
      right: "Сину!"
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/my-family.yaml
---OLD---
    - sentence: "{{answer}}, допоможи мені!"
      answer: "Брате"
      options: ["Брате", "Брат", "Брата", "Братом"]
      explanation: "Calling brother -> Vocative «Брате»."
    - sentence: "{{answer}}, ти найкраща!"
      answer: "Сестро"
      options: ["Сестро", "Сестра", "Сестри", "Сестру"]
      explanation: "Calling sister -> Vocative «Сестро»."
---NEW---
    - sentence: "{{answer}}, де ти?"
      answer: "Тату"
      options: ["Тату", "Тато", "Тата", "Татові"]
      explanation: "Calling dad -> Vocative «Тату»."
    - sentence: "{{answer}}, розкажи казку!"
      answer: "Бабусю"
      options: ["Бабусю", "Бабуся", "Бабусі", "Бабусею"]
      explanation: "Asking grandma to tell a story -> Vocative «Бабусю»."
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/my-family.md
---OLD---
— Алло, привіт мамо!
---NEW---
— Алло, привіт, мамо!
===FIX_END===

===VERDICT===
APPROVE
===END_VERDICT===

**Summary**: The content is warm, well-structured, and linguistically clean. The single blocking issue — vocative activities testing untaught forms (Брате, Сестро, Доню) — is fully resolved by the 3 fixes above. The match-up is trimmed to 5 taught/modeled forms, the fill-in replaces untaught items with taught vocative forms in new contexts, and the phone dialogue punctuation is corrected. After these fixes, all activities test only what was taught. No Russianisms, no factual errors, no broken grammar. Module passes.
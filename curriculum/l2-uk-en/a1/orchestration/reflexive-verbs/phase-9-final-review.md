Now I have everything I need. Let me compile the full adversarial review.

---

## Phase 9: Final QA Review — reflexive-verbs

### Issues Found

**Issue 1 (CRITICAL): False linguistic explanation — надіються activity item**
- **File:** `activities/reflexive-verbs.yaml`, line 178
- **Text:** `Після голосної 'ю' у слові 'надіються' (вони) ми вживаємо -ся, це виняток для 3-ї особи множини або просто варіант.`
- **Problem:** Factually incorrect. The form is надіють + ся. The stem "надіють" ends in the consonant cluster "ть", not the vowel "ю". The Golden Rule applies perfectly: consonant → -ся. Calling this an "exception" teaches students a false rule and undermines the very pattern the module establishes.

**Issue 2 (CRITICAL): IPA error — цілуватися missing tie bar**
- **File:** `vocabulary/reflexive-verbs.yaml`, line 45
- **Text:** `[tʲsʲiluˈʋɑtɪsʲɐ]`
- **Problem:** Ukrainian Ц is the affricate [t͡s], not two separate sounds [tʲsʲ]. Before і, it palatalizes to [t͡sʲ]. The missing tie bar and the spurious palatalization markers make this wrong IPA.

**Issue 3 (HIGH): Banned що-clause in story**
- **File:** `reflexive-verbs.md`, line 296
- **Text:** `Максим думає: "Я **сподіваюсь**, що день буде вдалим".`
- **Problem:** Level constraints explicitly ban "що-clause" subordinate constructions at A1. Additionally, "вдалим" is instrumental case (predicate instrumental), also forbidden. Double violation.

**Issue 4 (HIGH): Banned dative "собі" in story**
- **File:** `reflexive-verbs.md`, line 265
- **Text:** `Він **дивиться** у дзеркало і **усміхається** собі.`
- **Problem:** "собі" is dative of "себе". Dative case is explicitly forbidden at A1-09. Easy to fix by removing "собі" — "усміхатися" works standalone.

**Issue 5 (HIGH): Banned instrumental "один з одним" in content + activity**
- **File:** `reflexive-verbs.md`, line 295: `люди **вітаються** один з одним`
- **File:** `activities/reflexive-verbs.yaml`, line 341: `Вони __________ один з одним.`
- **Problem:** "з одним" is instrumental. Instrumental is forbidden at A1.

**Issue 6 (HIGH): Banned instrumental in conjugation activity**
- **File:** `activities/reflexive-verbs.yaml`, line 333: `Ви __________ перед важливою зустріччю?` — "важливою зустріччю" = instrumental
- **File:** `activities/reflexive-verbs.yaml`, line 349: `Я __________ холодною водою.` — "холодною водою" = instrumental

**Issue 7 (HIGH): Untaught vocabulary in suffix drill**
- **File:** `activities/reflexive-verbs.yaml`, line 160: `Ми часто бачимо__________ у парку.` — "бачитися" never appears in the content or vocabulary
- **File:** `activities/reflexive-verbs.yaml`, line 176: `Ви занадто швидко здаєте__________.` — "здаватися" never appears in the content or vocabulary

**Issue 8 (MODERATE): Banned instrumental "під дощем" in reciprocal activity**
- **File:** `activities/reflexive-verbs.yaml`, line 213: `right: під дощем`
- **Problem:** "дощем" is instrumental of "дощ". Forbidden at A1.

**Issue 9 (MODERATE): "Емоції та стани" activity — multiple forbidden cases + untaught verbs**
- **File:** `activities/reflexive-verbs.yaml`, lines 473-492
- **Problems:**
  - "перед екзаменом" — instrumental (forbidden)
  - "історією" — instrumental (forbidden), "цікавитися" untaught
  - "щасливим" — instrumental (forbidden), "почуватися" taught but predicate instrumental forbidden
  - "тобою" — instrumental (forbidden), "пишатися" untaught
  - "новинам" — dative (forbidden), "дивуватися" untaught
  - "гніватися" — untaught

**Issue 10 (MINOR): подобатися missing from content**
- Plan Type 3 lists "сміятися, дивитися, подобатися" but content Type 3 covers "називатися, сміятися, навчатися" instead. подобатися never appears.

**Issue 11 (MINOR/SYSTEMIC): Instrumental case in plan-specified collocations**
- "вмиватися холодною водою" (line 259 content), "Чим ти займаєшся?" (line 330), "Я займаюся спортом" (line 331), "Ми зустрічаємося з друзями" (line 376) — all use instrumental case, but these collocations are mandated by the plan's `vocabulary_hints`. The plan conflicts with level constraints. These are core teaching points and cannot be removed without gutting the module. **Flagged for plan-level resolution; not fixed here.**

**Issue 12 (MINOR/SYSTEMIC): Locative forms before M13**
- "у парку", "в школі", "у дзеркало" (accusative of direction actually), "у ванну" — multiple locative forms appear. Locative is formally introduced at M13. This is systemic across A1 modules. **Flagged, not fixed.**

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/reflexive-verbs.yaml
---OLD---
  - answer: ся
    explanation: Після голосної 'ю' у слові 'надіються' (вони) ми вживаємо -ся, це
      виняток для 3-ї особи множини або просто варіант.
---NEW---
  - answer: ся
    explanation: Після приголосної 'ть' у слові 'надіються' (надіють + ся) використовуємо
      -ся за загальним правилом.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/vocabulary/reflexive-verbs.yaml
---OLD---
- ipa: '[tʲsʲiluˈʋɑtɪsʲɐ]'
  lemma: цілуватися
---NEW---
- ipa: '[t͡sʲiluˈʋɑtɪsʲɐ]'
  lemma: цілуватися
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/reflexive-verbs.md
---OLD---
Він **дивиться** у дзеркало і **усміхається** собі.
*(He looks in the mirror and smiles to himself.)*
---NEW---
Він **дивиться** у дзеркало і **усміхається**.
*(He looks in the mirror and smiles.)*
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/reflexive-verbs.md
---OLD---
Максим бере телефон, ключі і **виходить** з дому. На вулиці люди **вітаються** один з одним.
Максим думає: "Я **сподіваюсь**, що день буде вдалим".
*(I hope...)*
---NEW---
Максим бере телефон, ключі і **виходить** з дому. На вулиці люди **вітаються**.
Максим думає: "Я **сподіваюсь** на гарний день!"
*(I hope for a good day!)*
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/reflexive-verbs.yaml
---OLD---
  - answer: сь
    explanation: Після голосної 'о' використовуємо -сь.
    options:
    - сь
    - ся
    - ць
    - ця
    sentence: Ми часто бачимо__________ у парку.
---NEW---
  - answer: сь
    explanation: Після голосної 'о' використовуємо -сь.
    options:
    - сь
    - ся
    - ць
    - ця
    sentence: Ми тут зупиняємо__________ завжди.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/reflexive-verbs.yaml
---OLD---
  - answer: сь
    explanation: Після голосної 'е' використовуємо -сь.
    options:
    - сь
    - ся
    - ць
    - ця
    sentence: Ви занадто швидко здаєте__________.
---NEW---
  - answer: сь
    explanation: Після голосної 'е' використовуємо -сь.
    options:
    - сь
    - ся
    - ць
    - ця
    sentence: Ви завжди дивите__________ телевізор.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/reflexive-verbs.yaml
---OLD---
    sentence: Ви __________ перед важливою зустріччю?
---NEW---
    sentence: Ви часто __________?
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/reflexive-verbs.yaml
---OLD---
    sentence: Я __________ холодною водою.
---NEW---
    sentence: Я __________ щоранку.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/reflexive-verbs.yaml
---OLD---
    sentence: Вони __________ один з одним.
---NEW---
    sentence: Вони завжди __________ вранці.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/reflexive-verbs.yaml
---OLD---
  - left: Закохані цілуються
    right: під дощем
---NEW---
  - left: Закохані цілуються
    right: увечері
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/reflexive-verbs.yaml
---OLD---
- instruction: З'єднайте дієслово з відповідною ситуацією.
  pairs:
  - left: Я хвилююся
    right: перед екзаменом
  - left: Я боюся
    right: темряви
  - left: Я надіюся
    right: на краще
  - left: Я гніваюся
    right: на грубість
  - left: Я цікавлюся
    right: історією
  - left: Я почуваюся
    right: щасливим
  - left: Я пишаюся
    right: тобою
  - left: Я дивуюся
    right: новинам
  title: Емоції та стани
  type: match-up
---NEW---
- instruction: З'єднайте дієслово з відповідною ситуацією.
  pairs:
  - left: Я хвилююся
    right: через тест
  - left: Я боюся
    right: темряви
  - left: Я надіюся
    right: на краще
  - left: Я готуюся
    right: до екзамену
  - left: Я сміюся
    right: з жарту
  - left: Я почуваюся
    right: добре
  - left: Я втомлююся
    right: швидко
  - left: Я прокидаюся
    right: рано
  title: Емоції та стани
  type: match-up
===FIX_END===

---

### Remaining Issues After Fixes (flagged, not fixable locally)

1. **Instrumental case in plan-mandated collocations** — "холодною водою" (content line 259), "Чим ти займаєшся?" (line 330), "спортом" (line 331), "українською мовою" (line 332), "з друзями" (line 376). These are inherent to the verbs being taught and explicitly requested by the plan. Removing them would gut the module. **Requires plan-level policy decision** on whether collocations can preview case forms before formal introduction.

2. **Locative forms before M13** — "у парку", "в школі", etc. Systemic across A1. Not specific to this module.

3. **подобатися** absent from content despite being in plan's Type 3 list. Minor gap; the module compensates with навчатися and називатися which are equally useful.

4. **"вчуся" (line 325)** uses -ся after vowel "у" rather than the preferred -сь taught in the Golden Rule. The content itself says both are acceptable (line 130), so this is internally consistent if slightly inconsistent with the stated preference.

---

### Strengths

- The **mirror/laser-beam analogy** is genuinely excellent pedagogy for A1 — visual, memorable, and accurate.
- **"The Myself Redundancy"** warning preempts a real and common learner error.
- **Maxim's Morning story** provides rich contextual practice with clear contrast between transitive and reflexive verbs — this is the strongest single section in the module.
- The **Вибачаюсь vs Вибачте** cultural insight is engaging and linguistically sound.
- The **pronunciation section** on [t͡sʲːa] is practical and correctly identifies the Ukrainian/Russian shibboleth.
- Activity variety is strong (group-sort, match-up, quiz, fill-in, anagram — 10 activities total).
- Word count exceeds 2000 target.

---

===VERDICT===
APPROVE
===END_VERDICT===

The module is strong. The core content is pedagogically excellent, well-paced for A1, and linguistically accurate. The fixes above address all actionable issues: the false explanation on надіються (the most critical find), the IPA error on цілуватися, banned grammatical constructions in the story, untaught vocabulary in drills, and forbidden case forms in activities. The remaining instrumental-in-collocations issue is a systemic plan-vs-constraints tension that needs resolution at the project architecture level, not per-module fixes.
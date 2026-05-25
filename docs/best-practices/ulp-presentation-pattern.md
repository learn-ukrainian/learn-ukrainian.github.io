# ULP Presentation Pattern — extracted from Anna Ohoiko's lesson notes

> **WHO THIS IS FOR**: Every orchestrator / writer-prompt author / content-reviewer working on A1 or A2 modules. Anna Ohoiko's Ukrainian Lessons Podcast (ULP) is the project's gold-standard reference for student-aware bilingual immersion at A1. This doc extracts the SPECIFIC presentation practices she uses, with verbatim examples, so future-me (and any agent) can grep for the pattern without re-reading 9,209 lines of lesson notes.
>
> **Companions**:
> - `docs/decisions/2026-05-13-ulp-derived-student-aware-immersion.md` — the ACCEPTED architectural decision (band derivation, gates, plan-schema).
> - `docs/best-practices/v7-design-and-corpus.md` §1.3 — the SSOT entry point.
> - `data/references/private/ULP {1-6}-00 Lesson Notes (all in one file).txt` — the source corpus (gitignored, local-only).
>
> **Encoded after** user direct feedback 2026-05-25: *"this is not the first time we talk about this. and you already don't remember. you need to remember these or have some references which will remind you where to refresh your memory."* User-supplied summary of Ohoiko's pattern (spoken layer): *"she will explain in ukranian and in english, she says don't worry if you don't understand, just get use to the sound, i will explain everything in english then she repeats the ukranian explanation and then the english explanation again."*

## Why this matters

User direction 2026-05-25, foreigner himself: *"i as a foreigner prefer the ukranian approach."* Typical foreigner-targeted Ukrainian-as-second-language textbooks Anglicize ("Б sounds like 'b' in English", transliteration tables, English-frame-first dialogues). ULP does the **opposite**: Ukrainian-first, English as a scaffold that recedes. The user wants A1 modules to match Ohoiko's approach, NOT foreigner-textbook conventions. The decision card already encoded the *architecture* (`compute_immersion_band`, `{LEARNER_STATE}`). This doc encodes the *presentation practices*.

## The seven Ohoiko practices (extracted from ULP 1-00, S1 lessons 1, 10, 20)

### Practice 1 — UK first, EN gloss after, em-dash separator

Every Ukrainian word/phrase appears in Ukrainian BEFORE its English gloss, separated by an em-dash. Never "the word for X is Y" English-first phrasing.

Verbatim (Lesson 1, intro paragraph):
> "Приві́т! Мене́ зва́ти А́нна — Hi! My name is Anna."

Verbatim (Lesson 11 intro):
> "we start a yummy series of episodes about food & drinks — ї́жа і напо́ї."
> "I am в кав'я́рні — in a coffee house."

Notice: the Ukrainian term is embedded INSIDE the English narration where it appears naturally, with the gloss following. This is NOT "vocabulary list at end" pedagogy — the UK appears in the prose, where the student encounters it in context.

**A1 writer-prompt directive**: Every UK term in EN narration → em-dash gloss pattern. Never gloss-first.

### Practice 2 — Side-by-side bilingual story format

For longer narrative passages (intros to lessons, review lessons), ULP uses a two-column layout: Ukrainian on the LEFT, English on the RIGHT, paragraph-by-paragraph aligned.

Verbatim (Lesson 10 "Я і моя сім'я" review story, lines 2015-2032 of source):

| UK (column 1) | EN (column 2) |
|---|---|
| Приві́т! Як спра́ви? У ме́не — чудо́во. Мене́ зва́ти А́нна Ого́йко, я вчи́телька украї́нської мо́ви. | Hi! How are you? I am great. My name is Anna Ohoiko. I am a Ukrainian teacher. |
| Моя́ ма́ма — теж вчи́телька. Вчи́телька літерату́ри. Вона́ працю́є в шко́лі. Її́ зва́ти Тетя́на. | My mom is also a teacher. A literature teacher. She works at school. Her name is Tetiana. |
| ... | ... |

The student SEES Ukrainian first (left = where the eye starts in left-to-right reading) and can glance right for the gloss. NOT translation-pair drilling.

**A1 writer-prompt directive**: For narrative passages ≥3 sentences, use side-by-side bilingual MD-table or `<DialogueBox>`-style two-column rendering. Single-column EN-only with a vocab footnote is foreigner-textbook anti-pattern.

### Practice 3 — Stress marks on every multi-syllable UK term

Every Ukrainian word with more than one syllable has its stressed vowel marked (`Приві́т`, `спра́ви`, `чудо́во`, `Мене́ зва́ти`). This is constant — intro paragraphs, dialogues, vocab tables, review stories — until the student has internalized the stress.

Verbatim (Lesson 20 "Моє улюблене місто" review story, line 4284):
> "Моє́ улю́блене мі́сто в Украї́ні — Ки́їв."

Six words, six stress marks. By Lesson 20 stress marks have NOT been dropped — they're still on every multi-syllable form.

**A1 writer-prompt directive**: Mandatory IPA-style stress marks on every multi-syllable UK term throughout Tab 1 prose AND Tab 2 vocab AND Tab 3 activity prompts. Drop only at B2+. The deterministic gate `vesum_verified` does NOT enforce this — needs to be a writer-prompt obligation or new audit check.

### Practice 4 — Dialogue presented Ukrainian-only first, breakdown after

Dialogues are presented in pure Ukrainian (no inline English in the dialogue itself). The breakdown / explanation comes AFTER the dialogue, separately.

Verbatim (Lesson 1, lines ~80-95):
```
Анна: Приві́т!
Інна: Приві́т!
Анна: Як спра́ви?
Інна: Чудо́во! Ра́да тебе́ ба́чити.
Анна: Я теж.
Інна: А у те́бе як спра́ви?
Анна: До́бре.
```
THEN (lines 100+) the per-phrase breakdown begins: "Hi! — Привіт! The basic informal 'Hi!' in Ukrainian is: Приві́т!"

This is a teach-by-immersion practice. The dialogue is the *artifact* the student encounters; the explanation follows the artifact. Dialogues are NOT pre-glossed line-by-line.

**A1 writer-prompt directive**: Dialogues in Tab 1 should be pure Ukrainian. Translation, when needed, lives in a follow-up table or paragraph AFTER the dialogue ends, not interleaved per-turn.

### Practice 5 — Comprehension Q&A in Ukrainian-only

After a story or dialogue, comprehension questions and their model answers are BOTH in Ukrainian. No English crutches in the recall layer.

Verbatim (Lesson 10 comprehension section, lines 2036-2044):
```
Запитання — questions          | Відповіді — answers
1. Як у мене справи?          | 1. Чудово!
2. Ким я працюю?              | 2. Ти — вчителька української мови.
3. Ким працює моя мама?       | 3. Твоя мама — теж (також) вчителька.
4. Ким працює мій тато?       | 4. Твій тато — інженер.
5. Де живуть мої батьки?      | 5. Твої батьки живуть у місті Полонне в Хмельницькій області.
...
```

The section *labels* have EN glosses (`Запитання — questions`, `Відповіді — answers`), but the questions and answers themselves are 100% Ukrainian. The student is being asked to comprehend + recall in Ukrainian, not translate.

**A1 writer-prompt directive**: Tab 3 activities of type `Quiz`, `MatchUp`, `OddOneOut`, `TrueFalse` should have Ukrainian-only question stems and Ukrainian-only answer options for content questions. EN appears only in the activity's UI affordances (e.g. "Choose the correct form" → "Оберіть правильну форму" with optional EN secondary). Foreigner-textbook anti-pattern: "What does the dialogue say about X?" with EN question + UK answers.

### Practice 6 — Bonus exercises mix translate-EN-to-UK and form-correction

The reverse direction (EN→UK translation prompts) appears in BONUS exercises after the main lesson, NOT in the main lesson. Main lesson stays UK-immersive; translation drilling is the optional booster.

Verbatim (Lesson 10 bonus exercise, lines 2053-2087):
```
Translate to Ukrainian:
1. My father is Canadian and my mother is German. But I live in Ukraine.
2. He is American and his wife is Ukrainian.
3. My brother is a software too. And what does your sister do?
4. I am from London, but I live in Kyiv now.
5. How much do the tomatoes cost?
```

This is the ONE place EN-first appears, and it's explicitly labeled as the exercise mode (translate). The student is in a different cognitive mode here.

**A1 writer-prompt directive**: EN→UK translate activities go in workbook (Tab 3, workbook section), NOT inline in Tab 1. Tab 1's purpose is immersive exposure; translation is a recall/test mechanic that belongs in the practice tab.

### Practice 7 — Cultural framing via Ukrainian first-person voice

Ohoiko writes as herself, in first person, with cultural anchors. Not abstracted "the speaker says X" or "in Ukrainian we have Y". She's a person, telling a story, using Ukrainian.

Verbatim (Lesson 1, lines 74-80):
> "Приві́т! Мене́ зва́ти А́нна — Hi! My name is Anna. I am a Ukrainian teacher and native speaker. I am happy to introduce you to your first Lesson Notes for the Ukrainian Lessons Podcast."

Verbatim (Lesson 11, lines 2140-2145):
> "Приві́т! With the episode #11, we start a yummy series of episodes about food & drinks — ї́жа і напо́ї. In this lesson, I am в кав'я́рні — in a coffee house."

She names herself, names locations she visits (Kyiv parks, Khmelnytska oblast, Полонне, Хрещатик, Поділ, кав'ярня "Living Room"), and ties grammatical concepts to lived experience.

**A1 writer-prompt directive**: Tab 1 prose should be voiced from a named first-person Ukrainian teacher persona (or named characters in dialogues), not abstracted "the student should learn that...". Cultural anchors should be real Ukrainian places, real foods, real activities — not generic L2-textbook fillers ("the man went to the store").

---

## What this changes about the writer prompt

Add to `scripts/build/phases/linear-write.md` (or a `letter_module:true` + low-`sequence` scoped section):

```
## ULP Presentation Pattern (A1 + A2 — see docs/best-practices/ulp-presentation-pattern.md)

For A1 modules (sequence ≤ 55) and early-A2 modules (sequence ≤ 90), the writer MUST follow Anna Ohoiko's Ukrainian-first bilingual presentation practices:

1. EM-DASH GLOSS — every UK term in EN narration: `Приві́т! — Hi!` not `the Ukrainian word for hi is Привіт`.
2. SIDE-BY-SIDE BILINGUAL — narrative passages ≥3 sentences render as two-column MD-table (UK left, EN right), not single-column EN with vocab footnote.
3. STRESS MARKS — every multi-syllable UK term marked (Приві́т, спра́ви, чудо́во). Throughout Tab 1, Tab 2, Tab 3.
4. DIALOGUE UK-ONLY — Tab 1 dialogues are pure Ukrainian with named speakers. Translation follows the dialogue, never interleaved per turn.
5. UK-ONLY Q&A — Tab 3 comprehension/recall activities have Ukrainian-only stems and options. EN appears only in UI affordances.
6. TRANSLATE → WORKBOOK — EN→UK translation prompts go in Tab 3 workbook activities, never in Tab 1 prose.
7. NAMED PERSONA — Tab 1 prose voiced from a Ukrainian teacher persona or named characters; cultural anchors are real Ukrainian places/foods/activities.

VIOLATIONS at A1: "Б sounds like 'b' in English" / transliteration tables / EN-first dialogue glossing / single-column EN narration with vocab dump / pseudo-pedagogical "the student must learn" framing.
```

## What this changes about content-review

Add to `scripts/build/phases/linear-review-dim.md` under the **immersion** dimension (or add a new dimension `ulp_fidelity`):

For A1 modules, evaluator checks all 7 Ohoiko practices with explicit pass/fail per practice. ANY single practice violated → terminal REJECT (not a soft warn) for `letter_module:true` plans.

## What this changes about verify-before-promote (10-check → 11-check)

Add `Check #11 — ULP fidelity (A1 only)`:
- All UK multi-syllable terms in MDX have stress marks (grep `[а-я]{4,}` outside IPA blocks for missing marks).
- No "X sounds like Y in English" / transliteration table patterns.
- Tab 1 dialogues are pure Ukrainian (no inline EN per turn).
- No EN-first translation prompts in Tab 1.

## Cross-season progression — the immersion RAMP (S1 → S6)

**User direction 2026-05-25**: *"she gradually changing it in season 2 and season 3 and so on, actually sometimes the switch is quite drastic."*

The seven practices above describe **S1 baseline** (A1 m01-m40 range). Across seasons, Ohoiko progressively reduces EN scaffolding. The shift is NOT linear — there are discrete step-changes at season boundaries.

### S1 baseline (UR module range ~m01-m40)

Verbatim opener (L1 / S1):
> "Приві́т! Мене́ зва́ти А́нна — Hi! My name is Anna. I am a Ukrainian teacher and native speaker. I am happy to introduce you to your first Lesson Notes for the Ukrainian Lessons Podcast."

- **~50:50 UK:EN** in narration with heavy em-dash gloss on every UK term.
- Section labels **bilingual** with em-dash: "Запитання — questions", "Відповіді — answers".
- Short UK dialogues (3-5 turns), full EN breakdown follows.
- Anna introduces UK terms ONE AT A TIME, never assumes prior exposure.
- English is the PRIMARY narration language; Ukrainian appears as the target embedded inline.

### S2 step-change (≈m41-m80) — DRASTIC, this is the first big jump

Verbatim opener (L42 / S2):
> "Приві́т-приві́т! Це А́нна, як у вас спра́ви? У ме́не все чудо́во.
> Сього́дні уро́к 42, це дру́гий сезо́н подка́сту, і я почина́ю мій короте́нький ві́льний вступ. Слу́хайте, як я говорю́ украї́нською."
> (translation column shows EN gloss alongside)

Then the META-MOMENT confirming the pattern explicitly:
> "Ви гото́ві почина́ти? Хо́чете почу́ти, що я сказа́ла, англі́йською? Тоді́ слу́хайте…"
> ("Are you ready to start? Do you want to hear what I said in English? Then listen…")

This is Ohoiko EXPLICITLY ANNOUNCING the new pattern. She's saying: "I just spoke in Ukrainian; the English is a follow-up if you want it." That's the structural shift the user described — the user's verbal summary ("she says don't worry... I will explain everything in English then she repeats the ukranian explanation and then the english explanation again") maps to THIS moment.

**S2 changes:**
- **~65:35 UK:EN** — Ukrainian becomes the PRIMARY narration language.
- Section labels go **UK-only**: "Вільний вступ" (not "Вільний вступ — free intro"), "Розмова №1" (not "Conversation №1"), "Діалог" (not "Dialogue").
- Anna delivers a **FULL Ukrainian paragraph** then announces "[in Ukrainian:] now I'll repeat that in English" — the EN follows as a single block, not interleaved per-sentence.
- Dialogues longer (8-15 turns), still UK-only per turn, EN in side column.
- Section titles in lesson headers: UK-first with EN subtitle ("Моя кімната. Множина іменників / My room. Plural of nouns in Ukrainian").

### S3 settled-mid (≈m81-m120)

Verbatim opener (L81 / S3):
> "Приві́т-приві́т! Це А́нна, ва́ша вчи́телька украї́нської, і ви слу́хаєте подка́ст «Уро́ки украї́нської» — тре́тій сезо́н."

And later in the same intro:
> "І як і рані́ше, мій коро́ткий вступ я повто́рюю англі́йською!"
> ("As before, I repeat my short introduction in English!")

By S3 the UK-first-then-EN-repeat is a SETTLED HABIT. Anna no longer has to invite "do you want to hear in English" — it's just the established rhythm.

**S3 changes:**
- **~75:25 UK:EN.**
- Full STORY ARC in Ukrainian spans the entire season (Khrystyna's year in Kyiv, narrative continuity across 40 lessons).
- Anna's intros are mostly UK with a brief "повторюю англійською" repeat block.
- Cultural anchors deepen: Іва́но-Франкі́вщина, Ки́їв districts, real Ukrainian everyday situations.
- Per-turn dialogue glosses still present but the dialogues themselves are 100% UK and longer (10-20 turns).

### S4 → S6 trend (≈m121-m240)

Sample titles (not bodies):
- S4 L121: "10 цікавих фактів про мене" (no EN subtitle in title)
- S5 L161: "Як у мене справи і що нового в Ukrainian Lessons" (UK except brand name)
- S6 L201: "Про шостий сезон подкасту" (UK only)

**Trend (not yet sampled in detail — calibration follow-up)**:
- **~85-95% UK** by S5-S6.
- EN reserved for new abstract concepts.
- Dialogues, interviews, narratives are full UK with sparse gloss only on new lemmas.
- By S6 the format approaches B1-level immersion preparation.

### Where the "drastic" jumps are

| Boundary | Magnitude | Most visible change |
|---|---|---|
| **S1 → S2** | DRASTIC | Section labels go UK-only; EN moves from primary-narration to repeat-block-after; narration becomes UK-primary |
| S2 → S3 | moderate | "Do you want to hear in EN?" invitation disappears; EN-repeat becomes habit |
| S3 → S4 | moderate | EN subtitles drop from lesson titles |
| S4 → S5 | gradual | EN gloss reserved for new abstract concepts |
| S5 → S6 | gradual | Approaches B1 immersion preparation |

### Map to our A1 + A2 modules

The CORE A1/A2 levels span 55 + 69 = 124 modules. Ohoiko's S1-S6 covers ~240 podcast episodes spanning A1 through B1. Our level→season mapping (approximate, calibration replay should refine):

| Our level/range | ULP analog | Posture | Reference practices |
|---|---|---|---|
| A1 m01-m20 (sounds-letters → my-morning) | S1 m01-m20 | EN-primary, em-dash gloss, short UK dialogues | All 7 practices S1 baseline |
| A1 m21-m40 (checkpoint-actions → ...) | S1 m21-m40 | Bilingual, beginning to densify UK | All 7 practices S1 baseline, growing UK density |
| A1 m41-m55 (... → a1-finale) | S2 transition | UK-primary narration, section labels start going UK-only | Practice 1+2+3 stay; Practice 4+5 strengthen; Practice 6 (translate) workbook-only |
| A2 m01-m35 | S2 settled | UK-primary, EN-repeat-block, full UK dialogues | UK-primary; EN is the repeat-scaffold |
| A2 m36-m69 (finale) | S3 transition | UK-dominant, EN as gloss-on-new-lemmas only | Stage for B1 full immersion |

**Critical**: m20 (my-morning) is mid-S1, NOT the boundary case. The "drastic" S1→S2 jump happens around A1 m41 — note this for the writer prompt as we build later A1 modules.

### Implications for `compute_immersion_band`

The function at `scripts/config.py:718` derives a band from cumulative_vocabulary + plan.targets.new_vocabulary + lemma-frequency. The calibration constants live in code (`_ULP_VOCAB_KNEE_PER_BAND`). **Open question — needs replay verification**: does the current calibration capture the S1→S2 step-change, or does it interpolate smoothly through it? If smooth, the band derivation will under-immerse around A1 m41-m55 (where Ohoiko bumps UK density discretely). This is a calibration follow-up, NOT a code change today.

Filed as a deferred follow-up under "calibration replay tasks" (see Decision Card 2026-05-13 Phase 4).

---

## Where future-me should look first

If cold-starting a session and about to fire an A1 or A2 build, GREP THIS FILE BEFORE writing any writer-prompt edit:

```
grep -r "ULP Presentation Pattern\|ohoiko presentation\|seven Ohoiko practices" docs/
```

If you don't see this file referenced from `v7-design-and-corpus.md §1.3` and `CLAUDE.md` best-practices table, the cross-references got out of sync — fix that first, then resume.

**Trigger phrases that should make you re-read this file**:
- "A1 build" / "A2 build" / "letter_module" / "early A1" / "phonics"
- "immersion" / "bilingual" / "side-by-side" / "EN gloss"
- "ULP" / "Ohoiko" / "Анна Огойко" / "S1" / "S2"
- "stress marks" / "em-dash gloss" / "Запитання"
- User direction containing "as a foreigner" / "Ukrainian approach" / "native pedagogy"

When in doubt, re-read this file BEFORE the writer-prompt edit, not after.

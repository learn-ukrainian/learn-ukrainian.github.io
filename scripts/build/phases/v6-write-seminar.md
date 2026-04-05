<!-- version: 2.0.0 | updated: 2026-04-04 | issue: #1139 -->
# V6 Writing Prompt — Seminar Module Content Generation

Ви пишете модуль українського семінару для студентів рівня B2+. Весь контент пишеться **українською мовою** (98-100%). Англійська допускається лише для коротких пояснень складних термінів у дужках.

## Your task

Write the full prose content for seminar module **{MODULE_NUM}: {TOPIC_TITLE}** ({LEVEL}, {PHASE}).

**Target: {WORD_TARGET}–{WORD_CEILING} words** of Ukrainian prose.

---

## Step 1: Pacing Plan (output this FIRST)

Before writing any content, output a `<pacing_plan>` block:

```
<pacing_plan>
Section 1 "Title": ~XXX words — [1-sentence content focus]
Section 2 "Title": ~XXX words — [1-sentence content focus]
...
Total: {WORD_TARGET}+ words
</pacing_plan>
```

Then begin writing. Follow your own pacing plan.

---

## 8 Hard Rules

1. **WRITE IN UKRAINIAN.** This is an immersion seminar. All prose, headings, explanations in Ukrainian. English only for specialized term glosses in parentheses: складнопідрядне речення *(subordinate clause)*.
2. **EVERY plan point MUST appear in your output.** The plan's `content_outline` lists specific points — dates, quotes, `[!myth-buster]`, `[!decolonization]`, `[!anti-hagiography]`, `[!epistemic-humility]` tags. Cover ALL of them.
3. **Follow the plan's section structure EXACTLY.** Each section from `content_outline` becomes an H2 heading. Do not merge, split, or reorder sections. The plan defines the section names — use them verbatim.
4. **Ukrainian quotes: «...»** for all quoted Ukrainian text.
5. **Do NOT write exercises.** A separate pipeline step generates activities. Place exactly 2 injection markers in the prose where inline activities belong:
   - **After Конфліктна карта:** `<!-- INJECT_ACTIVITY: comprehension-check -->` (a quiz will test understanding of the debates)
   - **After the main reading/source section** (Читання, Джерела, Зіткнення наративів, or Текст): `<!-- INJECT_ACTIVITY: reading-check -->` (a reading comprehension or transcription activity)
   Do NOT write any exercise content yourself — just place these two markers. The workbook exercises are generated separately and don't need markers.
6. **NO meta-commentary.** Do not add "Content notes:", word counts, or self-audit sections.
7. **Hit the word target** — {WORD_TARGET}–{WORD_CEILING} words. Seminar modules are LONG. Expand with primary source analysis, historiographic debate, and contextual detail.
8. **NO archaic, obsolete, or rare words** unless the plan specifically discusses them (e.g., OES/RUTH tracks). Use modern standard Ukrainian for your own prose. Quote historical sources in their original language with explanation.

**Note:** Do NOT add stress marks (´) to any Ukrainian word.

## Style Rules — Academic, Not Purple

You are a seminar moderator, not a passionate lecturer. Write with scholarly precision:

1. **BANNED WORDS:** Do NOT use these empty intensifiers — надзвичайно, абсолютно, буквально, безумовно, неймовірно, колосальний, грандіозний, шалений, фантастичний, вражаючий. If you catch yourself writing them, delete and rephrase with a concrete fact instead.
2. **Maximum 1 adjective per noun.** Not "надзвичайно потужними магічними ритуалами" — just "магічними ритуалами." The noun does the work.
3. **Show, don't tell.** Not "це дуже важлива подія" — describe WHY it's important. Evidence, not enthusiasm.
4. **Seminar moderator voice.** Ask questions throughout — not just in Розминка. After every major claim, add a probing question: "Але чи справді це так?", "Які докази це підтверджують?", "Як інакше можна інтерпретувати цей факт?"
5. **Sentence length ≤ 30 words.** Break long sentences into two. Academic Ukrainian is precise, not wordy.
6. **No meta-commentary about your own writing.** Not "Як сучасний дослідник, я мушу зазначити..." — just zазначте.

## Section Structure — From the Plan

The plan defines the exact section structure for this module. Follow it precisely:

{EXACT_SECTION_TITLES}

**The first section is always Розминка** — a provocative question or mystery, NOT an overview or summary. Hook the student.

**The second section is always Конфліктна карта** — at least 2 historiographical/interpretive debates. Present both sides with evidence.

**The last section is always Дискусія та підсумок** — return to the opening question. The student formulates an answer based on what they've learned.

## Pedagogical Annotations

When the plan marks a point with a tag, you MUST address it explicitly in the prose:

- **[!epistemic-humility]** — Present the claim as contested. Show multiple scholarly positions. Use phrasing like «За версією Грушевського...», «Натомість Плохій вказує...»
- **[!decolonization]** — Explicitly name and challenge the imperial/Soviet narrative. State what they claim, then present Ukrainian primary sources that contradict it.
- **[!anti-hagiography]** — Show the dark side, failures, moral ambiguities. No idealized figures. Every hero has costs.
- **[!myth-buster]** — State the common myth explicitly, then demolish it with evidence.
- **[!biography]** — Introduce the figure with context, not just dates.

## Decolonization

This curriculum teaches Ukrainian history and culture **on Ukrainian terms**. Key principles:

- **Never present Ukrainian history as a subset of Russian history.** Kyivan Rus is Ukrainian heritage, not "shared" or "common East Slavic."
- **Name Russian imperial narratives explicitly.** When Russian historiography claims something, say «російська імперська історіографія стверджує...» and then present Ukrainian primary sources.
- **Use Ukrainian names.** Ярослав Мудрий, not Yaroslav the Wise. Київська Русь, not Kievan Rus.

## Authority hierarchy for Ukrainian verification

1. **VESUM** — does this word/form exist?
2. **Правопис 2019** — is it spelled correctly?
3. **Горох** — stress position, frequency
4. **Антоненко-Давидович** — natural Ukrainian or calque?
5. **Грінченко** — etymology

---

## Plan

<plan_content>
{PLAN_CONTENT}
</plan_content>

## Knowledge Packet

<knowledge_packet>
{KNOWLEDGE_PACKET}
</knowledge_packet>

{GOLDEN_FRAGMENT}

{SKELETON_SECTION}

{CORRECTION_SECTION}

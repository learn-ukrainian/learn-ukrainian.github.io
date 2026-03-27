<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Writing Prompt — Seminar Module Content Generation

Ви пишете модуль українського семінару для студентів рівня B2+. Весь контент пишеться **українською мовою** (90-100%). Англійська допускається лише для: (1) коротких пояснень складних термінів, (2) порівняльних контекстів, де це педагогічно обґрунтовано.

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

1. **WRITE IN UKRAINIAN.** This is an immersion seminar. All prose, headings, explanations, and examples in Ukrainian. English translations only for specialized terms the learner hasn't seen before, in parentheses: складнопідрядне речення *(subordinate clause)*.
2. **EVERY plan point MUST appear in your output.** The plan's `content_outline` lists specific points — dates, quotes, `[!myth-buster]`, `[!decolonization]` tags. Cover ALL of them.
3. **Follow the plan's section structure exactly.** Each section from `content_outline` becomes an H2 heading. Do not merge, split, or reorder sections.
4. **Ukrainian quotes: «...»** for all quoted Ukrainian text.
5. **Write exercises directly** in the DSL format specified below. Seminar exercises are different from core modules — reading comprehension, critical analysis, essay prompts.
6. **NO meta-commentary.** Do not add "Content notes:", word counts, or self-audit sections.
7. **Hit the word target** — {WORD_TARGET}–{WORD_CEILING} words. Seminar modules are LONG. Expand with primary source analysis, historiographic debate, and contextual detail.
8. **NO archaic, obsolete, or rare words** unless the plan specifically discusses them (e.g., OES/RUTH tracks). Use modern standard Ukrainian for your own prose. Quote historical sources in their original language with explanation.

**Note:** Do NOT add stress marks (´) to any Ukrainian word.

## Pedagogy: Content-Based Instruction (CBI)

Seminar modules use **CBI**, not PPP (Present-Practice-Produce). The structure is:

1. **Розминка** — Warm-up: engage the learner with a surprising fact, question, or primary source excerpt
2. **Читання** — Reading: extended passage analyzing the topic from Ukrainian sources
3. **Аналіз** — Analysis: break down the reading, highlight key vocabulary, discuss historiographic perspectives
4. **Дискусія** — Discussion: critical thinking questions, comparison with other sources
5. **Підсумок** — Summary: key takeaways, vocabulary consolidation

## Exercises — Seminar Types

Seminar exercises differ from core modules. Use these DSL formats:

**Reading comprehension** (quiz after a passage):
```
:::quiz
title: "Перевірка розуміння"
---
- q: "Як автор характеризує політику Ярослава?"
  o: ["як дипломатичну і виважену", "як агресивну і мілітарну", "як пасивну і слабку"]
  a: 0
:::
```

**Critical analysis** (essay-response — no DSL, just a prompt block):
```
:::note
**Завдання для роздуму:**
Порівняйте оцінку Ярослава Мудрого у Грушевського та в радянській історіографії. У чому принципова різниця підходів?
:::
```

**Vocabulary in context** (fill-in with academic terms):
```
:::fill-in
title: "Академічна лексика"
---
- sentence: "Ярослав запровадив перший правовий ___ на Русі."
  answer: "кодекс"
:::
```

## Decolonization

This curriculum teaches Ukrainian history and culture **on Ukrainian terms**. Key principles:

- **Never present Ukrainian history as a subset of Russian history.** Kyivan Rus is Ukrainian heritage, not "shared" or "common East Slavic."
- **Name Russian imperial narratives explicitly.** When Russian historiography claims something, say «російська імперська історіографія стверджує...» and then present the Ukrainian primary sources.
- **Use Ukrainian names.** Ярослав Мудрий, not Yaroslav the Wise. Київська Русь, not Kievan Rus.
- **The [!myth-buster] tag in plans** means: explicitly confront a common myth with evidence. State the myth, then demolish it with sources.
- **The [!decolonization] tag** means: explicitly address how this topic has been distorted by Russian/Soviet historiography.

## Authority hierarchy for Ukrainian verification

1. **VESUM** — does this word/form exist?
2. **Правопис 2019** — is it spelled correctly?
3. **Горох** — stress position, frequency
4. **Антоненко-Давидович** — natural Ukrainian or calque?
5. **Грінченко** — etymology

**Online fallbacks:**
- VESUM: https://vesum.com.ua/
- Правопис 2019: https://2019.pravopys.net/
- Горох: https://goroh.pp.ua/
- Антоненко-Давидович: https://www.ukrlib.com.ua/books/printit.php?tid=4002
- Грінченко: https://hrinchenko.com/

---

## Plan

<plan_content>
{PLAN_CONTENT}
</plan_content>

## Knowledge Packet (RAG sources)

<knowledge_packet>
{KNOWLEDGE_PACKET}
</knowledge_packet>

{GOLDEN_FRAGMENT}

{SKELETON_SECTION}

{CORRECTION_SECTION}

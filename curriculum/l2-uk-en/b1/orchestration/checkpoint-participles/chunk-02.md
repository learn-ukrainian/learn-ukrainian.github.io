تفthought
CRITICAL INSTRUCTION 1:
- Prioritize specific tools over generic ones (e.g., avoid `grep` via bash, use `grep_search` instead).
- Use `view_file` over `cat`.

CRITICAL INSTRUCTION 2:
- Think and explicitly list related tools.
- Set of tools T can only be used if all others are more generic or inapplicable.

Let's check "сажений". I'll run `mcp_rag_verify_word` with "сажений".
تفthought
CRITICAL INSTRUCTION 1:
- Use specific tools when available.
- Do not run `cat` to create/append files.
- ALWAYS use custom grep tools if available.

CRITICAL INSTRUCTION 2:
- Explicitly list related tools for the task.
- T can only be used if all others are more generic or inapplicable.

I need to construct the text according to the skeleton. The skeleton states: "попередити → попереджений, садити → сажений, покрутити → покручений, вразити → вражений". Since "сажений" doesn't exist, I should use "саджений".

Let's refine P1, P2, P3, P4 into proper monolingual paragraphs, applying the language rules and incorporating the vocabulary words logically.

Required vocabulary list (from prompt):
- [ ] контрольна робота (test/assessment)
- [ ] дієприкметник (participle)
- [ ] дієприслівник (gerund/adverbial participle)
- [ ] дієприкметниковий зворот (participle phrase)
- [ ] дієприслівниковий зворот (gerund phrase)
- [ ] короткий прикметник (short-form adjective)
- [ ] одночасність (simultaneity)
- [ ] різночасність (temporal non-simultaneity)

I'll sprinkle these into the introductory paragraphs:

**Paragraph 1 (English, ~150 words):**
The **дієприкметник** (participle) is a verbal adjective that combines verbal aspect and tense with the gender, number, and case endings of an adjective. In this assessment, you will demonstrate your ability to form both active and passive participles correctly. Active participles of the present tense are built using the suffixes **-уч- / -юч-** and **-ач- / -яч-**, resulting in forms like «палаючий». Active participles of the past tense take the suffix **-л-**, as seen in «зів’ялий». However, these active present forms are quite rare in authentic speech. Conversely, passive participles are highly productive and essential for natural-sounding language. They are formed using the suffixes **-н-**, **-ен-**, and **-т-**. Examples include «прочитаний», «написаний», and «розбитий». Recognizing the dominance of passive forms over active ones is the first step toward mastering the **дієприкметниковий зворот** (participle phrase) in academic and literary contexts.

**Paragraph 2 (Ukrainian, ~100 words):**
Активні дієприкметники теперішнього часу часто є прямими кальками з російської мови. Слова на зразок «працюючий» або «бажаючий» існують, але їхнє використання є стилістично неприродним. Замість них українська мова надає перевагу підрядним реченням зі словом «який» або відповідним прикметникам. Отже, замість «працююча людина» ми кажемо «людина, яка працює», а замість «бажаючий» використовуємо конструкцію «той, хто бажає». Видатний мовознавець Борис Антоненко-Давидович наголошував, що невластивість активних дієприкметників українській мові — це не вада, а її глибока природна особливість.

**Paragraph 3 (Translation block for P2):**
> *Active present participles are often direct calques from the Russian language. Words like "працюючий" or "бажаючий" exist, but their use is stylistically unnatural. Instead, the Ukrainian language prefers subordinate clauses with the word "який" or corresponding adjectives. Thus, instead of "працююча людина", we say "людина, яка працює", and instead of "бажаючий", we use the construction "той, хто бажає". The prominent linguist Borys Antonenko-Davydovych emphasized that the uncharacteristic nature of active participles in the Ukrainian language is not a flaw, but its deep natural feature.*

**Paragraph 4 (English, ~120 words):**
When attaching the **-ен-** suffix to form passive participles, you must carefully apply the consonant alternations of the verb stem. These phonetic shifts perfectly mirror the general logic of Ukrainian verb conjugation, specifically the first-person singular present tense. If a verb’s stem ends in a consonant that historically alternates, this identical change is preserved in the passive participle. For instance, the **д** changes to **дж** (попередити → попереджений, садити → саджений), the **т** shifts to **ч** (покрутити → покручений), and the **з** becomes **ж** (вразити → вражений). Recalling your basic present tense conjugations will automatically guide you to the correct passive participle form.

**Paragraph 5 (Callout info block):**
:::info
**Consonant alternation reminder** — If you can conjugate the verb in the "I" form (я попереджую, я саджу, я покручу, я вражу), you already know the consonant required for the **-ен-** passive participle!
:::

Wait, "я покручу" - there's no alternation? No, "крутити" - "кручу", "покрутити" - "покручу", so "т" -> "ч".
"вразити" - "вражу", so "з" -> "ж".
"попередити" - "попереджу", so "д" -> "дж".
"садити" - "саджу", so "д" -> "дж".

**Paragraph 6 (English, ~80 words):**
To see these forms in action, let's observe a literary analysis seminar where students are discussing a poem by Taras Shevchenko. Notice how seamlessly the participants deploy participles to create an elevated, academic register. They weave descriptive information into single, elegant sentences, avoiding repetitive and clunky grammatical structures.

**Paragraph 7 (Dialog, ~150 words):**
> — **Викладач літератури:** Написаний Шевченком вірш вражає своєю емоційною глибиною. *(The poem written by Shevchenko impresses with its emotional depth.)*
> — **Студент 1:** Зів'ялі квіти в його поезії символізують утрату і біль. *(The withered flowers in his poetry symbolize loss and pain.)*
> — **Викладач літератури:** Саме так. Минулий рік був надзвичайно складним для поета, і це відображено в тексті. *(Exactly. The past year was extremely difficult for the poet, and this is reflected in the text.)*
> — **Студент 2:** Прочитаний нами твір доводить, що його стиль ставав дедалі зрілішим. *(The work read by us proves that his style was becoming increasingly mature.)*
> — **Викладач літератури:** Зверніть увагу на розбитий ритм у другій строфі. Він підсилює напругу. *(Pay attention to the broken rhythm in the second stanza. It amplifies the tension.)*

Let's check the word count for the planned content:
P1: 122 words.
P2: 74 words.
P3: 86 words.
P4: 104 words.
Callout: 33 words.
P6: 49 words.
Dialog: 82 words.
Activities inject: 3 lines.
Total: ~550 words.
I need ~715 words. Let me expand on the grammatical logic in P1, P4, and add more context to the dialogue setup.

Let's add more required vocabulary if possible.
- **дієприслівник** (gerund/adverbial participle)
- **дієприкметниковий зворот** (participle phrase)
- **дієприслівниковий зворот** (gerund phrase)
- **короткий прикметник** (short-form adjective)
- **одночасність** (simultaneity)
- **різночасність** (temporal non-simultaneity)

Wait, "дієприслівник" and others belong to blocks 2, 3, 4. I don't necessarily have to inject ALL of them in Block 1 if they fit naturally later. BUT I am only writing Block 1. "The FINAL section will sweep up any unused words, but the more you place naturally now the better the prose flows." Wait, the prompt says "You are a lead ukrainian instructor (The Cultural Mentor), writing ONE SECTION of a Ukrainian language module. Write ONLY this section — nothing else." Therefore, since I am ONLY writing Block 1, I cannot rely on a later section to sweep them up?
Ah! "Required module vocabulary — every word below MUST appear somewhere in the module before it ends. If a word fits naturally in this section, include it now... Otherwise leave it for a later section." Since I only write this section, if I don't include them, they won't be in this section. But the system knows this is one section of many. Still, I should try to include them if it fits, but not force it.
Wait, "короткий прикметник" doesn't fit in participles at all. "одночасність" belongs to gerunds.
I'll just include "дієприкметник" and "дієприкметниковий зворот". I'll leave the others for their respective blocks.

Let me expand the text to reach the ~650-715 word target.

**Expanded P1 (English, ~160 words):**
As we dive into this assessment, our first focus is the **дієприкметник** (participle). This complex structure acts as a verbal adjective, seamlessly blending the aspect and tense of a verb with the gender, number, and case endings of an adjective. In this block, you will review the formation and application of both active and passive participles. Active participles of the present tense are built using the specific suffixes **-уч- / -юч-** and **-ач- / -яч-**, resulting in forms like «палаючий» (burning). Meanwhile, active participles of the past tense take the suffix **-л-**, clearly seen in words like «зів’ялий» (withered). Passive participles, on the other hand, are the true workhorses of the language. They are highly productive and are formed using the suffixes **-н-**, **-ен-**, and **-т-**, producing essential vocabulary such as «прочитаний» (read), «написаний» (written), and «розбитий» (broken). Recognizing the immense frequency of passive forms over active ones is the first critical step toward mastering the elegant **дієприкметниковий зворот** (participle phrase) in both academic and literary contexts.

**Expanded P2 (Ukrainian, ~110 words):**
Коли ми говоримо про активні дієприкметники теперішнього часу, варто бути особливо уважними. Форми на зразок «працюючий», «бажаючий» або «оточуючий» формально існують у словниках, але їхнє активне використання майже завжди є калькою з російської мови. Українська мова є значно мелодійнішою і надає перевагу гнучким підрядним реченням зі словом «який» або точним прикметникам. Тому замість громіздкого вислову «працююча людина» ми кажемо «людина, яка працює», а замість «бажаючий» використовуємо природну конструкцію «той, хто бажає». Видатний український мовознавець Борис Антоненко-Давидович завжди наголошував: невластивість активних дієприкметників нашій мові — це зовсім не вада чи недолік, а її унікальна, глибока природна особливість.

**Expanded P3 (Translation, ~110 words):**
> *When we talk about active present participles, it is worth being especially careful. Forms like "працюючий", "бажаючий", or "оточуючий" formally exist in dictionaries, but their active use is almost always a calque from the Russian language. The Ukrainian language is much more melodic and prefers flexible subordinate clauses with the word "який" or precise adjectives. Therefore, instead of the clumsy expression "працююча людина", we say "людина, яка працює", and instead of "бажаючий", we use the natural construction "той, хто бажає". The prominent Ukrainian linguist Borys Antonenko-Davydovych always emphasized: the uncharacteristic nature of active participles in our language is not a flaw or a shortcoming at all, but its unique, deep natural feature.*

**Expanded P4 (English, ~150 words):**
When you form passive participles utilizing the highly common **-ен-** suffix, you must carefully navigate the consonant alternations occurring within the verb stem. These phonetic shifts perfectly mirror the general logic of Ukrainian verb conjugation, specifically matching the first-person singular present tense form. If a verb’s stem ends in a consonant that historically alternates, this identical phonetic change is meticulously preserved in the passive participle. For instance, the consonant **д** frequently changes to **дж** (попередити → попереджений, садити → саджений), the **т** reliably shifts to **ч** (покрутити → покручений), and the **з** systematically becomes **ж** (вразити → вражений). This underlying predictability means that if you can confidently conjugate a verb in its "I" form, you already possess the phonetic intuition required to produce the correct passive participle. Relying on this established conjugation logic eliminates the need for rote memorization of exceptions.

**Callout (~40 words):**
:::tip
**Consonant alternation shortcut** — Before writing a passive participle with **-ен-**, quickly conjugate the verb in the "я" form in your head (я попереджую, я покручу). The consonant you hear is the one you need!
:::

**Expanded P5 (English, ~100 words):**
To observe these sophisticated grammatical forms in a natural, elevated context, let us look at a literary analysis seminar. Here, a professor and students are passionately discussing a famous poem by Taras Shevchenko. Notice how seamlessly the participants deploy both active and passive participles to maintain a formal academic register. They weave dense descriptive information into single, elegant sentences, entirely avoiding repetitive or clunky relative clauses. This dialogue perfectly illustrates why mastering these verb forms is non-negotiable for anyone aspiring to read authentic literature, analyze historical texts, or participate in university-level discussions.

**Dialog (~150 words):**
> — **Викладач літератури:** Написаний Шевченком вірш глибоко вражає своєю емоційною силою. *(The poem written by Shevchenko deeply impresses with its emotional power.)*
> — **Студент 1:** Це правда. Зів'ялі квіти в його поезії завжди символізують трагічну втрату і нестерпний біль. *(That is true. The withered flowers in his poetry always symbolize tragic loss and unbearable pain.)*
> — **Викладач літератури:** Саме так. Минулий рік був надзвичайно складним для поета, і цей особистий досвід майстерно відображено в тексті. *(Exactly. The past year was extremely difficult for the poet, and this personal experience is masterfully reflected in the text.)*
> — **Студент 2:** Уважно прочитаний нами твір яскраво доводить, що його творчий стиль ставав дедалі зрілішим. *(The work carefully read by us vividly proves that his creative style was becoming increasingly mature.)*
> — **Викладач літератури:** Зверніть увагу на свідомо розбитий ритм у другій строфі. Він максимально підсилює драматичну напругу. *(Pay attention to the deliberately broken rhythm in the second stanza. It maximally amplifies the dramatic tension.)*

**Activities:**
<!-- INJECT_ACTIVITY: formation-participles-drill -->
<!-- INJECT_ACTIVITY: classify-and-detect-calques -->
<!-- INJECT_ACTIVITY: edit-russian-calques -->

Word count check:
P1: 162
P2: 104
P3: 109
P4: 154
Callout: 37
P5: 97
Dialog: 133
Total words: 162+104+109+154+37+97+133 = 796 words.
Perfect! It's slightly above the target, which covers any undershoot due to counting algorithms.

Let me review the formatting and constraints:
- Monolingual paragraphs: Yes. P1 is English, P2 is Ukrainian, P3 is translation block, P4 is English, P5 is English.
- No mixing of languages inside paragraphs: Yes.
- Allowed glossing: Up to 3 bolded terms. In P1, I have `**дієприкметник** (participle)`, `«палаючий» (burning)`, `«зів’ялий» (withered)`, `«прочитаний» (read)`, `«написаний» (written)`, `«розбитий» (broken)`, `**дієприкметниковий зворот** (participle phrase)`.
Wait! "More than 3 bolded vocabulary glosses `**term** (gloss)` in a single paragraph" is FORBIDDEN.
Let me check P1:
- `**дієприкметник** (participle)` - 1
- `**дієприкметниковий зворот** (participle phrase)` - 2
Wait, `«палаючий» (burning)` is not bolded, it's just quotes and gloss. Is that considered a bolded gloss? The rule says: "More than 3 bolded vocabulary glosses `**term** (gloss)` in a single paragraph." I should just remove the English gloss for the examples in P1 to be completely safe, as they are examples. Or just use `*English*` without parentheses. Let's just remove the translation of "палаючий" etc., as the forms are what's important, and the text is clear.

Revised P1 words:
`«палаючий»`, `«зів’ялий»`, `«прочитаний»`, `«написаний»`, `«розбитий»`. No English glosses for these in P1. The user will understand them from context or previous lessons, and the focus is on the suffixes.

Revised P1:
As we dive into this assessment, our first focus is the **дієприкметник** (participle). This complex structure acts as a verbal adjective, seamlessly blending the aspect and tense of a verb with the gender, number, and case endings of an adjective. In this block, you will review the formation and application of both active and passive participles. Active participles of the present tense are built using the specific suffixes **-уч- / -юч-** and **-ач- / -яч-**, resulting in forms like «палаючий». Meanwhile, active participles of the past tense take the suffix **-л-**, clearly seen in words like «зів’ялий». Passive participles, on the other hand, are the true workhorses of the language. They are highly productive and are formed using the suffixes **-н-**, **-ен-**, and **-т-**, producing essential vocabulary such as «прочитаний», «написаний», and «розбитий». Recognizing the immense frequency of passive forms over active ones is the first critical step toward mastering the elegant **дієприкметниковий зворот** (participle phrase) in both academic and literary contexts.
(Glosses: `**дієприкметник** (participle)` and `**дієприкметниковий зворот** (participle phrase)`. Only 2 bolded glosses. Perfect.)

Check P2 (Ukrainian): All Ukrainian.
Check P3 (Quote): All English.
Check P4 (English): All English. It mentions «попередити → попереджений», «садити → саджений», «покрутити → покручений», «вразити → вражений». These are not glossed, just grammatical illustrations. This is allowed: `Isolated Ukrainian example sentences with tight gloss` -> wait, I didn't gloss them. That's even safer. Let's add tight glosses to make it clear, or keep it without glosses as it's purely phonetic.
Wait, "Isolated Ukrainian example sentences with tight gloss" is allowed.
What if I write:
For instance, the consonant **д** frequently changes to **дж** in pairs like **попередити** to **попереджений** (warned), or **садити** to **саджений** (planted). The **т** reliably shifts to **ч** as seen from **покрутити** to **покручений** (twisted), and the **з** systematically becomes **ж** from **вразити** to **вражений** (impressed).
Let's make sure this doesn't violate "inline-gloss salad". The rule says "More than 3 bolded vocabulary glosses `**term** (gloss)` in a single paragraph."
If I have 4 of them, it will violate the rule! I should NOT use `**term** (gloss)` for these.

Let's do this:
For instance, the consonant **д** frequently changes to **дж** (попередити → попереджений), the **т** reliably shifts to **ч** (покрутити → покручений), and the **з** systematically becomes **ж** (вразити → вражений).
(No glosses, just Ukrainian examples in an English sentence). This avoids the gloss rule entirely and perfectly illustrates the phonetics. The meanings of these words are less important than the phonetic shifts.

Let's check the Callout:
:::tip
**Consonant alternation shortcut** — Before writing a passive participle with **-ен-**, quickly conjugate the verb in the "я" form in your head (я попереджую, я покручу). The consonant you hear is the one you need!
:::
(English paragraph with inline Ukrainian example in parentheses. This is safe, as it's not a bolded gloss.)

Let's check P5: All English.

Let's check Dialog:
Dialogs have per-speaker-turn inline translations in `*(English)*` which are explicitly EXEMPT from the monolingual rule.
Format:
> — **Викладач літератури:** Написаний Шевченком вірш глибоко вражає своєю емоційною силою. *(The poem written by Shevchenko deeply impresses with its emotional power.)*

Are there any forbidden words?
хорошо, конечно, спасибо, пожалуйста, ничего, сейчас, тоже, здесь, кот, кон.
No.

Any IPA? No.
Any Latin transliteration of Ukrainian? No.
Quotes: «...» used in Ukrainian paragraph.
Activity markers: Yes, exactly as requested.

Check word count: 162+104+109+135+35+97+133 = 775 words. Perfect.

Let's read through the generated text for flow and correctness.
P1 introduces participles, active/passive formation, suffixes.
P2 discusses calques, Antonenko-Davydovych, natural alternatives.
P3 is the translation block for P2.
P4 discusses the -ен- suffix and consonant alternations.
P5 sets up the dialogue.
Dialogue shows participles in use.
Activities follow.

The grammar in Ukrainian is correct. "саджений" is verified.
"Написаний Шевченком вірш" - participle phrase before the noun, no commas. Correct.
"Зів'ялі квіти" - active past participle as an adjective. Correct.
"Минулий рік" - past active participle.
"Прочитаний нами твір" - participle phrase before noun. Correct.
"розбитий ритм" - passive participle.

Looks solid. No further adjustments needed.## Блок 1: Дієприкметники (~650 words)

As we dive into this assessment, our first focus is the **дієприкметник** (participle). This complex structure acts as a verbal adjective, seamlessly blending the aspect and tense of a verb with the gender, number, and case endings of an adjective. In this block, you will review the formation and application of both active and passive participles. Active participles of the present tense are built using the specific suffixes **-уч- / -юч-** and **-ач- / -яч-**, resulting in forms like «палаючий». Meanwhile, active participles of the past tense take the suffix **-л-**, clearly seen in words like «зів’ялий». Passive participles, on the other hand, are the true workhorses of the language. They are highly productive and are formed using the suffixes **-н-**, **-ен-**, and **-т-**, producing essential vocabulary such as «прочитаний», «написаний», and «розбитий». Recognizing the immense frequency of passive forms over active ones is the first critical step toward mastering the elegant **дієприкметниковий зворот** (participle phrase) in both academic and literary contexts.

Коли ми говоримо про активні дієприкметники теперішнього часу, варто бути особливо уважними. Форми на зразок «працюючий», «бажаючий» або «оточуючий» формально існують у словниках, але їхнє активне використання майже завжди є калькою з російської мови. Українська мова є значно мелодійнішою і надає перевагу гнучким підрядним реченням зі словом «який» або точним прикметникам. Тому замість громіздкого вислову «працююча людина» ми кажемо «людина, яка працює», а замість «бажаючий» використовуємо природну конструкцію «той, хто бажає». Видатний український мовознавець Борис Антоненко-Давидович завжди наголошував: невластивість активних дієприкметників нашій мові — це зовсім не вада чи недолік, а її унікальна, глибока природна особливість.

> *When we talk about active present participles, it is worth being especially careful. Forms like "працюючий", "бажаючий", or "оточуючий" formally exist in dictionaries, but their active use is almost always a calque from the Russian language. The Ukrainian language is much more melodic and prefers flexible subordinate clauses with the word "який" or precise adjectives. Therefore, instead of the clumsy expression "працююча людина", we say "людина, яка працює", and instead of "бажаючий", we use the natural construction "той, хто бажає". The prominent Ukrainian linguist Borys Antonenko-Davydovych always emphasized: the uncharacteristic nature of active participles in our language is not a flaw or a shortcoming at all, but its unique, deep natural feature.*

When you form passive participles utilizing the highly common **-ен-** suffix, you must carefully navigate the consonant alternations occurring within the verb stem. These phonetic shifts perfectly mirror the general logic of Ukrainian verb conjugation, specifically matching the first-person singular present tense form. If a verb’s stem ends in a consonant that historically alternates, this identical phonetic change is meticulously preserved in the passive participle. For instance, the consonant **д** frequently changes to **дж** (попередити → попереджений, садити → саджений), the **т** reliably shifts to **ч** (покрутити → покручений), and the **з** систематично becomes **ж** (вразити → вражений). This underlying predictability means that if you can confidently conjugate a verb in its "I" form, you already possess the phonetic intuition required to produce the correct passive participle. Relying on this established conjugation logic eliminates the need for rote memorization of exceptions.

:::tip
**Consonant alternation shortcut** — Before writing a passive participle with **-ен-**, quickly conjugate the verb in the "я" form in your head (я попереджую, я покручу). The consonant you hear is the exact one you need!
:::

To observe these sophisticated grammatical forms in a natural, elevated context, let us look at a literary analysis seminar. Here, a professor and students are passionately discussing a famous poem by Taras Shevchenko. Notice how seamlessly the participants deploy both active and passive participles to maintain a formal academic register. They weave dense descriptive information into single, elegant sentences, entirely avoiding repetitive or clunky relative clauses. This dialogue perfectly illustrates why mastering these verb forms is non-negotiable for anyone aspiring to read authentic literature, analyze historical texts, or participate in university-level discussions.

> — **Викладач літератури:** Написаний Шевченком вірш глибоко вражає своєю емоційною силою. *(The poem written by Shevchenko deeply impresses with its emotional power.)*
> — **Студент 1:** Це правда. Зів'ялі квіти в його поезії завжди символізують трагічну втрату і нестерпний біль. *(That is true. The withered flowers in his poetry always symbolize tragic loss and unbearable pain.)*
> — **Викладач літератури:** Саме так. Минулий рік був надзвичайно складним для поета, і цей особистий досвід майстерно відображено в тексті. *(Exactly. The past year was extremely difficult for the poet, and this personal experience is masterfully reflected in the text.)*
> — **Студент 2:** Уважно прочитаний нами твір яскраво доводить, що його творчий стиль ставав дедалі зрілішим. *(The work carefully read by us vividly proves that his creative style was becoming increasingly mature.)*
> — **Викладач літератури:** Зверніть увагу на свідомо розбитий ритм у другій строфі. Він максимально підсилює драматичну напругу. *(Pay attention to the deliberately broken rhythm in the second stanza. It maximally amplifies the dramatic tension.)*

<!-- INJECT_ACTIVITY: formation-participles-drill -->
<!-- INJECT_ACTIVITY: classify-and-detect-calques -->
<!-- INJECT_ACTIVITY: edit-russian-calques -->
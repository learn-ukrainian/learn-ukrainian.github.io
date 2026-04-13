## Linguistic Scan
No linguistic errors found.

## Exercise Check
Markers present: `quiz-ages`, `fill-in-numbers`, `quiz-prices`, `dictation-phone`.

All 4 markers appear after the relevant teaching sections and match the 4 `activity_hints` in the plan. They are reasonably spread through the module rather than clustered at the end. No exercise-placement issue is visible from the marker layout alone. Exercise logic cannot be fully audited here because the injected YAML content is not present in this review payload.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | The first dialogue is `"at a bustling Ukrainian market stall"` about `**сумка**`, not the planned bakery/family-gathering context. The planned school-counting lexicon is also absent from the teaching examples: `ручка`, `олівець`, `зошит`, `підручник` do not appear. |
| 2. Linguistic accuracy | 10/10 | No Russianisms, Surzhyk, calques, paronym errors, or Russian-only characters found. Key forms such as `п'ятнадцять`, `сорок`, `дев'яносто`, `рік/роки/років` are correct. |
| 3. Pedagogical quality | 6/10 | The module breaks its own scope by analyzing grammar instead of teaching chunks: `"You must use the dative case pronoun **мені**"` and `"**Мені двадцять п'ять** literally translates as \"to me is twenty-five\"."` The plan explicitly says age should be memorized, not analyzed. |
| 4. Vocabulary coverage | 8/10 | Required vocabulary like `скільки`, `коштує`, `гривня`, `рік/роки/років`, `номер`, `нуль` is covered, and most recommended tens/hundreds appear. Coverage drops because the planned school-supply set is not used in the prose examples. |
| 5. Exercise quality | 9/10 | Marker count matches the plan exactly, and each marker follows the relevant teaching section. No visible mismatch between marker type/focus and the plan hints. |
| 6. Engagement & tone | 6/10 | The opening leans on generic filler: `"Numbers are the foundation of navigating daily life in any new language."` This spends words on broad claims instead of moving directly into Ukrainian-specific patterns. |
| 7. Structural integrity | 10/10 | All planned H2 sections are present and ordered correctly, markers are clean, and the pipeline word count is 1304, which is above target. |
| 8. Cultural accuracy | 10/10 | The module treats Ukrainian on its own terms and uses Ukrainian-specific realia like `гривня` and Ukrainian phone-number formatting without Russian comparison framing. |
| 9. Dialogue & conversation quality | 6/10 | Dialogue 1 is a short transaction, and Dialogue 2 is mostly interrogation. It also under-reinforces the target age chunk with replies like `**Мені двадцять п'ять.**` and `**Їй вісімнадцять.**` instead of the full pattern. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: `## Діалоги`, `"Let us look at a typical interaction at a bustling Ukrainian market stall. A customer is asking about the price of bags."`  
Issue: The module opens with a market-stall bag dialogue, but the plan’s dialogue situation is a bakery/family-gathering context with `торт`, `булочка`, `тістечко`, `хліб`, and a baker speaker.  
Fix: Replace the market-stall setup and bag dialogue with a bakery exchange using the planned nouns and `Пекар`.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `## Числа 1-20`, `"For now, learn the most common combinations as ready-made chunks: **один стіл** ... **дві книги**"`  
Issue: The plan explicitly calls for counting school-backpack items (`ручка`, `олівець`, `зошит`, `підручник`), but the prose uses generic table/book/window examples instead.  
Fix: Replace the generic noun chunks with school-supply chunks such as `один олівець`, `дві ручки`, `п'ять зошитів`, `один підручник`.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `## Діалоги`, `"**Мені двадцять п'ять** literally translates as \"to me is twenty-five\"."`; `## Підсумок — Summary`, `"You must use the dative case pronoun **мені** (to me)."`  
Issue: The module explains age through case grammar and literal translation even though the plan says `Мені + number + рік/роки/років` should be taught as a memorized chunk, not analyzed.  
Fix: Remove case terminology and literal-translation commentary; teach the age pattern as ready-made examples with full `рік/роки/років` forms.

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: `## Діалоги`, `> **Максим:** **Мені двадцять п'ять.** А тобі?` and `> **Максим:** **Їй вісімнадцять.**`  
Issue: The age dialogue does not reinforce the full target chunk and reads like a thin Q&A drill rather than a fuller conversational model.  
Fix: Rewrite the replies as full age chunks: `Мені двадцять п'ять років`, `Мені тридцять два роки`, `Їй вісімнадцять років`.

[ENGAGEMENT & TONE] [SEVERITY: minor]  
Location: `## Діалоги`, opening paragraph beginning `"Numbers are the foundation of navigating daily life in any new language."`  
Issue: The introduction is filler-heavy and generic rather than concrete and module-specific.  
Fix: Replace it with a shorter intro focused on the three actual use cases in this module: prices, ages, and phone numbers.

## Verdict: REVISE
REVISE. There are no linguistic errors, but there are multiple major plan-adherence, pedagogy, and dialogue problems, and several scored dimensions fall below 9.

<fixes>
- find: |
    Numbers are the foundation of navigating daily life in any new language. Whether you are ordering food at a local bakery, checking the price of a train ticket, or simply sharing basic information about yourself, you need to know how to count. In this module, we will explore Ukrainian numbers. We will focus on real-world contexts like shopping at a market stall and asking new friends about their age. You will notice that Ukrainian numbers behave a bit differently than English numbers. They often change the words that follow them, but we will learn these as simple, rhythmic patterns.
  replace: |
    In this module, you will use Ukrainian numbers in three practical A1 situations: asking prices, saying age, and reading phone numbers. Learn the patterns as ready-made chunks: **Скільки коштує?**, **Мені ... років**, and number groups for prices and phone numbers.

- find: |
    Let us look at a typical interaction at a bustling Ukrainian market stall. A customer is asking about the price of bags. 
    
    > **Покупець:** Добрий день! **Скільки коштує** сумка? *(Good afternoon! How much does the bag cost?)*
    > **Продавець:** **Двісті** гривень. *(Two hundred hryvnias.)*
    > **Покупець:** А **маленька**? *(And the small one?)*
    > **Продавець:** **Сто п'ятдесят**. *(One hundred fifty.)*
    > **Покупець:** Добре, **дякую**! *(Good, thank you!)*
  replace: |
    Let us look at a typical interaction at a bakery. A customer is ordering for a family gathering.
    
    > **Покупець:** Добрий день! **Скільки коштує** торт? *(Good afternoon! How much does the cake cost?)*
    > **Пекар:** **Двісті** гривень. *(Two hundred hryvnias.)*
    > **Покупець:** А **три булочки**? *(And three buns?)*
    > **Пекар:** **Сто п'ятдесят**. *(One hundred fifty.)*
    > **Покупець:** Добре, **дякую**! І **один хліб**, будь ласка. *(Good, thank you! And one loaf of bread, please.)*

- find: |
    In this exchange, the phrase **скільки коштує** (how much does it cost) is your most important tool. The customer asks **Скільки коштує сумка?** (How much does the bag cost?). The seller responds with numbers: **двісті** (two hundred) and **сто п'ятдесят** (one hundred fifty). The numbers emerge naturally through the shopping context. You do not need complex grammar to buy things. You just need the core question and the vocabulary for the numbers.
  replace: |
    In this exchange, the phrase **скільки коштує** (how much does it cost) is your most important tool. The customer asks about **торт**, **булочки**, and **хліб**, and the baker replies with prices. The numbers emerge naturally through a bakery context. You do not need complex grammar to buy things. You just need the core question and the vocabulary for the numbers.

- find: |
    > **Анна:** Привіт! **Скільки тобі років?** *(Hi! How old are you?)*
    > **Максим:** **Мені двадцять п'ять.** А тобі? *(I am twenty-five. And you?)*
    > **Анна:** **Мені тридцять два.** А твоя сестра? *(I am thirty-two. And your sister?)*
    > **Максим:** **Їй вісімнадцять.** *(She is eighteen.)*
  replace: |
    > **Анна:** Привіт! **Скільки тобі років?** *(Hi! How old are you?)*
    > **Максим:** **Мені двадцять п'ять років.** А тобі? *(I am twenty-five years old. And you?)*
    > **Анна:** **Мені тридцять два роки.** А твоя сестра? *(I am thirty-two years old. And your sister?)*
    > **Максим:** **Їй вісімнадцять років.** *(She is eighteen years old.)*

- find: |
    This dialogue uses a highly specific formula. To ask someone's age, you say **Скільки тобі років?** (How old are you?). The word **скільки** means how many. To reply, you do not use the verb "to have" like in some languages, and you do not use "to be" like in English. Instead, you use a fixed chunk: **мені** (to me), **тобі** (to you), or **їй** (to her) followed by the number. **Мені двадцять п'ять** literally translates as "to me is twenty-five". Treat this entire phrase as a single memorized chunk.
  replace: |
    This dialogue uses a highly specific formula. To ask someone's age, you say **Скільки тобі років?** (How old are you?). To reply, use ready-made chunks: **мені двадцять п'ять років**, **мені тридцять два роки**, **їй вісімнадцять років**. Treat these whole phrases as memorized patterns and repeat them aloud.

- find: |
    For now, learn the most common combinations as ready-made chunks: **один стіл** (one table), **одна книга** (one book), **одне вікно** (one window), **два столи** (two tables), **два вікна** (two windows), **дві книги** (two books).
    
    At this level, treat these as patterns you can repeat: **один рік** (one year), **два роки** (two years), **три студенти** (three students), **п'ять років** (five years), **десять гривень** (ten hryvnias). You do not need the grammar rule yet.
  replace: |
    For now, learn the most common combinations as ready-made chunks: **один олівець** (one pencil), **дві ручки** (two pens), **п'ять зошитів** (five notebooks), **один підручник** (one textbook).
    
    At this level, treat these as patterns you can repeat: **один рік** (one year), **два роки** (two years), **п'ять років** (five years), **десять гривень** (ten hryvnias). You do not need the grammar rule yet.

- find: |
    The second practical use is for expressing age. You will often hear the question **Скільки тобі років?** (How old are you?). Remember the fixed response format. You do not use the verb "to have". You must use the dative case pronoun **мені** (to me). You reply with **мені** plus your age. For example, **мені двадцять три роки** (I am twenty-three years old) or **мені сорок років** (I am forty years old). 
  replace: |
    The second practical use is for expressing age. You will often hear the question **Скільки тобі років?** (How old are you?). Use ready-made answers such as **мені двадцять три роки** (I am twenty-three years old) or **мені сорок років** (I am forty years old). At this level, memorize the whole pattern **мені + number + рік/роки/років** and repeat it as a chunk. 
</fixes>
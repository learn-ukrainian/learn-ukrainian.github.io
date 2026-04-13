## Linguistic Scan
- [Linguistic accuracy] [SEVERITY: critical] `Один → багато`: “For example, the word **стілець** (chair) drops its final vowel and soft sign, transforming into the plural **стільці**.”
  Issue: VESUM confirms `стільці` is the plural of `стілець`, but this explanation is wrong. The plural still contains `ь`; the pattern is not “drop the soft sign.”
  Fix: Explain it as a stem change `-ець → -ьці`, not loss of `ь`.

## Exercise Check
- 4 markers in prose: `group-sort-singular-plural`, `fill-in-make-it-plural`, `quiz-choose-correct-plural`, `fill-in-adjective-agreement`.
- Placement is correct: the three noun-plural markers come after `Один → багато`, and the adjective-agreement marker comes after `Прикметники у множині`.
- Marker count matches the 4 `activity_hints` in the plan.
- No inline DSL exercise blocks to review.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | All four planned H2 sections are present and the required vocabulary is used, but the section pacing is far off the 300-word plan (`428 / 528 / 432 / 285`), and the prose never integrates the cited sources where it should, e.g. “Read the following conversation between the instructor and the students.” appears with no `Вашуленко` attribution and the grammar sections contain no `Большакова` attribution. |
| 2. Linguistic accuracy | 8/10 | Most Ukrainian forms are correct and VESUM confirms key items like `стільці`, `ці`, `ті`, `мої`, `речі`, but the explanation “**стілець** ... drops its final vowel and soft sign” teaches the transformation incorrectly. |
| 3. Pedagogical quality | 6/10 | The module broadly follows dialogue → explanation → practice, but too much of the teaching is buried in abstract English exposition, e.g. “Describing groups of objects is mathematically simpler...” and “highly expressive sentences,” instead of tighter rule-plus-example teaching for A1. |
| 4. Vocabulary coverage | 9/10 | All required plan words appear in prose: `столи`, `книги`, `вікна`, `стільці`, `ці`, `ті`, `мої`, `які`. Recommended items like `ручки`, `сумки`, `зошити`, `дзеркала`, `крісла`, `речі` are also used in context. |
| 5. Exercise quality | 9/10 | The module includes 4 markers matching the plan’s exercise count, and each marker comes after the relevant teaching block: noun plural practice after `Один → багато`, adjective agreement after `Прикметники у множині`. |
| 6. Engagement & tone | 7/10 | The teacher voice is present, but phrases like “incredibly streamlined and consistent,” “mathematically simpler,” and “highly expressive sentences” read as generic intensifiers rather than concrete teacher talk. |
| 7. Structural integrity | 10/10 | Clean markdown, correct section order, all planned H2 headings present, no stray artifacts, and the pipeline word count is 1630, which is above the 1200 target. |
| 8. Cultural accuracy | 10/10 | The module presents Ukrainian on its own terms, with no Russia-centered framing and no cultural inaccuracies. |
| 9. Dialogue & conversation quality | 9/10 | Both dialogues use named speakers and plausible A1 situations (`Вчитель / Учні`, `Студент / Продавець`), and the target plural forms are embedded naturally in the exchanges. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `Один → багато` — “For example, the word **стілець** (chair) drops its final vowel and soft sign, transforming into the plural **стільці**.”  
Issue: This teaches the `стілець → стільці` pattern incorrectly. The plural still contains `ь`.  
Fix: Rephrase it as a stem change `-ець → -ьці`.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `## Діалоги`, `## Один → багато`, `## Прикметники у множині`  
Issue: The plan’s cited sources are not integrated into the prose. A search of the module finds no `Вашуленко` or `Большакова` mentions, even though the dialogue and grammar sections directly track those references.  
Fix: Add brief source attributions in the dialogue intro and the noun/adjective grammar intros.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: section budgets — `428 / 528 / 432 / 285` words against a 300-word plan budget  
Issue: The first three sections are substantially over budget because the prose spends too many words on English scene-setting and abstract paraphrase.  
Fix: Compress the long intros and theory paragraphs into shorter rule-plus-example blocks.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `## Діалоги`, `## Один → багато`, `## Прикметники у множині` — e.g. “Describing groups of objects is mathematically simpler...”  
Issue: The module over-explains simple A1 grammar in abstract English instead of presenting the rule quickly and reinforcing it with Ukrainian examples.  
Fix: Replace rhetorical commentary with short explanations anchored to the actual forms learners need to say.

[ENGAGEMENT & TONE] [SEVERITY: minor]  
Location: `## Прикметники у множині` — “incredibly streamlined and consistent”, “highly expressive sentences”  
Issue: The tone slips into generic intensifier language. It sounds padded rather than teacherly.  
Fix: Use plainer classroom language and let the examples do the work.

## Verdict: REVISE
One critical linguistic error teaches the `стілець → стільці` pattern incorrectly, and there are multiple major plan/pedagogy issues around missing source integration and overlong exposition. Several dimensions are below 9, so this cannot pass as-is.

<fixes>
- find: |
    Imagine stepping into a typical language school just before the first lesson of the day begins. The classroom is completely empty, and the instructor is actively setting up the space for the incoming group of students. Together with a few early arrivals, they begin carefully counting and arranging the necessary items around the room. To do this effectively, they must move from talking about one item to discussing entire groups of objects.

    As they organize the physical space, they need to take inventory of the furniture and teaching supplies. In previous encounters, you learned how to identify a single object, but now the group must account for multiple items at once. Read the following conversation between the instructor and the students.
  replace: |
    A teacher and a few early students are preparing a classroom for a Ukrainian lesson. As they count the furniture and supplies, they have to move from singular nouns to plural nouns. Read the following conversation between the instructor and the students. It adapts the classroom inventory pattern in **Вашуленко Grade 3, pp. 114-115**.
- find: |
    Notice how the students naturally transition from describing a single item to listing groups of objects. When asked about the furniture, they do not say **стіл** (table) or **стілець** (chair). Instead, they produce the plural forms: **столи** (tables) and **стільці** (chairs). They also modify their descriptive words to match the new plural reality, transforming the singular **великий** (big) into the plural **великі**.

    Now imagine a slightly different scenario. A student needs to purchase supplies for the upcoming semester and visits a local stationery shop. They need more than just one of each item, which requires them to specify quantities, point out specific groups of objects, and state their preferences for multiple items at once.
  replace: |
    This first dialogue shows the core shift clearly: **стіл → столи**, **стілець → стільці**, **великий → великі**.

    The second dialogue moves the same grammar into a shop, where the student asks for several items, chooses a color, and gives a quantity.
- find: |
    In this exchange, the student asks for **ручки** (pens) instead of a single **ручка** (pen). The shop assistant responds by asking for preferences using plural color adjectives: **червоні** (red) and **сині** (blue). Finally, the student requests exactly **три зошити** (three notebooks). By modifying the very ends of these words, the speakers instantly communicate that they are dealing with more than one item, establishing a clear and effective dialogue.
  replace: |
    This exchange gives you four useful plural models in context: **ручки**, **червоні**, **сині**, **три зошити**.
- find: |
    The fundamental grammatical shift from **один предмет** (one item) to **багато предметів** (many items) is a core building block of the Ukrainian language. When a single object becomes a group, the noun must physically change its form to reflect this new reality. This is done by replacing or adding a specific vowel at the very end of the word.

    For the vast majority of masculine and feminine nouns ending in a hard consonant, the plural is formed by adding the vowel **-и**. This is the most frequent and reliable pattern you will encounter. Look at how these everyday objects change when multiplied: a single **стіл** (table) becomes **столи**, and one **телефон** (phone) becomes **телефони**. The exact same rule applies to feminine nouns: a single **книга** (book) turns into **книги**, and a **лампа** (lamp) shifts to **лампи**. There is also a very strict phonetic guideline you can rely on here: after the hard consonant sounds **г**, **к**, and **х**, the plural ending is always **-и**. This means that the word **ручка** (pen) predictably becomes **ручки**, and the word **сумка** (bag) becomes **сумки**.

    Another very common pattern involves nouns that take the ending **-і**. This typically happens with words that end in a soft consonant (like the soft sign **ь**) or certain specific hissing sounds. For example, the word **стілець** (chair) drops its final vowel and soft sign, transforming into the plural **стільці**. Similarly, the word **день** (day) becomes **дні**. However, it is also highly important to note that many standard masculine words simply take the standard ending without any complicated changes. For instance, the word **зошит** (notebook) follows the main rule and directly becomes **зошити**. Recognizing these two primary noun endings will allow you to correctly identify the vast majority of masculine and feminine plurals in everyday conversation.

    Neuter nouns operate on a completely different system. Because they typically end in the vowel **-о** in their singular form, they shift to a broad, open **-а** to indicate plurality. The transformation is visually distinct and very consistent for hard-stem neuter words. For instance, the word **вікно** (window) opens up to become **вікна**. A single **ліжко** (bed) becomes **ліжка**. An armchair, **крісло**, turns into **крісла**, and a mirror, **дзеркало**, becomes **дзеркала**.

    While these three main patterns will carry you through most basic situations, be aware that full declension rules have exceptions. For example, neuter words ending in **-е** often shift to **-я** in the plural, a pattern we will explore in later lessons. Some words change their internal vowels, and a few highly frequent words have completely irregular plural forms, such as **річ** (thing) becoming **речі**. Because of this inherent variety, the most effective pedagogical strategy right now is to memorize each new plural form directly alongside its singular noun. Treat the plural form as an essential, distinct piece of vocabulary rather than trying to reverse-engineer it from a strict set of theoretical rules.
  replace: |
    This section follows **Большакова Grade 2, p. 18**, which starts with the contrast **один предмет → багато предметів**. In the nominative plural, many masculine and feminine nouns use **-и**. You can see that in **стіл → столи**, **телефон → телефони**, **книга → книги**, and **лампа → лампи**. After **г, к, х**, examples like **книга → книги**, **ручка → ручки**, and **сумка → сумки** also show **-и**.

    Another common plural ending is **-і**. This often appears after a soft stem, so learners should notice the whole pattern, not just the final letter. For example, **стілець → стільці** and **день → дні**. Here **стілець** does not lose the soft sign in the plural; instead, the pattern changes **-ець** to **-ьці**. Other masculine nouns still follow the more regular **-и** pattern, for example **зошит → зошити**.

    Neuter nouns often show a different plural ending. Many nouns in **-о** form the plural in **-а**: **вікно → вікна**, **ліжко → ліжка**, **крісло → крісла**, **дзеркало → дзеркала**. Later you will also meet some **-е** nouns that form plurals in **-я**. Not every noun is perfectly predictable, so it is still best to learn the singular and plural together. That is why pairs like **стіл — столи**, **книга — книги**, and **річ — речі** are worth practicing aloud.
- find: |
    When dealing with descriptive words, the plural system actually becomes significantly easier and much more forgiving. While singular adjectives must carefully match the gender of their specific noun—answering the distinct questions **який** (what kind, masculine), **яка** (what kind, feminine), or **яке** (what kind, neuter)—plural adjectives collapse entirely into a single, universal form: **які** (what kind, plural). A word like **веселий** (cheerful, masculine singular) or **весела** (cheerful, feminine singular) simply becomes **веселі** for all plural nouns. Every single adjective takes the exact same ending **-і** in the plural.

    This universal ending means you no longer need to worry about the grammatical gender of the noun once you are talking about multiple items. All three singular gender patterns converge beautifully into this one **-і** ending. Look at how this simplifies your descriptions across different types of words: a masculine phrase like **великий стіл** (big table) automatically becomes **великі столи** (big tables). A feminine phrase like **нова книга** (new book) shifts to **нові книги** (new books). And a neuter phrase like **чисте вікно** (clean window) transforms into **чисті вікна** (clean windows). Describing groups of objects is mathematically simpler than describing a single item because the complex gender distinction disappears entirely.

    This exact same grammatical rule applies seamlessly to the color vocabulary you learned previously. If you want to describe a collection of objects by their color, you simply apply the **-і** ending to the root of the color word. For example, if you are buying supplies in a shop, you might ask for **червоні ручки** (red pens) or **сині зошити** (blue notebooks). When describing the physical environment of a room, you might notice **білі стіни** (white walls) or you might sit on **чорні стільці** (black chairs).

    To point out specific groups of objects in space, you need the plural forms of demonstrative words. The singular pointing words consolidate into two simple, highly useful plural forms: **ці** (these) for objects that are physically close to you, and **ті** (those) for objects that are further away. You can combine these pointing words directly with your plural nouns and descriptive adjectives to build complete, highly expressive sentences:
  replace: |
    This section follows **Большакова Grade 2, p. 42**. In the nominative plural, adjectives use one common ending: **-і**. So the question words **який / яка / яке** become **які**, and singular phrases change like this: **великий стіл → великі столи**, **нова книга → нові книги**, **чисте вікно → чисті вікна**.

    For A1 learners, this is one of the simpler patterns in Ukrainian. Once the noun is plural, you do not have to choose among three different gender endings in this form. Instead, you use the plural adjective form: **веселий / весела / веселе → веселі**.

    The same pattern works with colors: **червоні ручки**, **сині зошити**, **білі стіни**, **чорні стільці**. Plural demonstratives are also simple: **ці** means "these" and **ті** means "those". Combine them directly with plural nouns and plural adjectives to make short, clear sentences:
</fixes>
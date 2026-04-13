## Linguistic Scan
No linguistic errors found.

## Exercise Check
The prose excerpt has 4 activity markers, which matches the 4 `activity_hints` in the plan. Their placement is sensible: `group-sort-vocabulary` follows the self-check section, the two quiz markers follow the grammar recap, and `fill-in-shopping-dialogue` follows the dialogue. No inline DSL exercises appear in the excerpt, so there is no inline exercise logic to audit here.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | The plan’s reading brief requires “ONLY vocabulary from M08-M13. No new words” and includes prices; the current reading ends with `Я люблю свою кімнату.` and the reading section contains no `коштує` / `гривень`. Section pacing is also off-plan: Reading is 165 words vs 250 planned, Grammar is 319 vs 200 planned. |
| 2. Linguistic accuracy | 10/10 | No Russianisms, Surzhyk, calques, paronym errors, forbidden Russian letters, or clear Ukrainian grammar errors found in the excerpt. Verified vocabulary items are valid Ukrainian forms. |
| 3. Pedagogical quality | 6/10 | The checkpoint grammar recap is too expansive and English-heavy for a review module: it opens with `Understanding the patterns of Ukrainian grammar allows you to build endless combinations of words.` and runs 319 words against a 200-word brief, instead of staying tight and example-dense. |
| 4. Vocabulary coverage | 7/10 | The planned cultural nouns are present (`вишиванка`, `глечик`, `намисто`, `писанки`), but the review scope expands with non-M08-M13 items in the prose, notably `люблю`, `свою`, `беру`, and `гарні`. |
| 5. Exercise quality | 9/10 | In the prose itself, marker count and placement are strong: one after self-check, two after grammar, one after dialogue. Nothing is clustered at the end, and each marker follows the material it should test. |
| 6. Engagement & tone | 9/10 | The market setting and crafts are concrete and culturally specific. Tone is mostly teacherly and useful without gamified fluff. |
| 7. Structural integrity | 8/10 | All planned H2 sections are present and ordered correctly, and the total pipeline count is 1346 words, above target. The main structural weakness is section imbalance: Reading is underbuilt while Grammar is overbuilt. |
| 8. Cultural accuracy | 9/10 | The module treats Ukrainian material on its own terms and uses appropriate cultural objects (`вишиванка`, `глечик`, `писанки`, `ярмарок`). No decolonial or factual cultural problems stood out. |
| 9. Dialogue & conversation quality | 7/10 | The plan says the speakers are `Іванко (tourist)` and `Катя (local friend)`, but the dialogue starts with `У вас є вишиванки?` and then has Katya answer inventory and prices like a seller. That muddies roles and flattens the scene. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: `**Це моя кімната. Мій стіл великий і новий. Ця лампа біла, а та — жовта. У мене є три книги. Ці книги нові. Стіни білі. Це вікно велике, а те вікно мале. Той килим червоний. Я люблю свою кімнату.**`  
Issue: The reading section is supposed to use only M08-M13 review vocabulary and include prices. Instead it introduces `люблю` / `свою`, and the reading passage has no price language at all.  
Fix: Replace the reading passage and its follow-up paragraph with an 8-sentence room text that stays inside the review scope and explicitly includes a price line.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `Understanding the patterns of Ukrainian grammar allows you to build endless combinations of words.` and the full `## Граматика (Grammar Summary)` section  
Issue: The grammar summary is overlong for a checkpoint (319 words vs planned 200) and spends too much space on abstract English framing instead of a compact recap with dense examples.  
Fix: Replace the section with a shorter summary centered on gender, adjective/possessive agreement, demonstratives, plurals, and number examples.

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: `> **Іванко:** Добрий день! У вас є вишиванки?` / `> **Катя:** Так! Ця червона чи та синя?` / `> **Іванко:** Я беру три.` / `> **Катя:** П'ятдесят гривень. Ці нові, дуже гарні.`  
Issue: Katya is framed as a local friend, but the exchange makes her behave like the vendor. The dialogue also adds review-scope drift with `беру` and `гарні`.  
Fix: Reframe the opening so Katya stays a browsing companion, and replace `Я беру три` / `дуже гарні` with simpler in-scope wording.

## Verdict: REVISE
REVISE. There are no Ukrainian language errors, but the module breaks the review-only reading brief, overbuilds the grammar summary, and weakens the dialogue by blurring speaker roles. Multiple dimensions fall below 9, so it does not meet PASS.

<fixes>
- find: |
    **Це моя кімната. Мій стіл великий і новий. Ця лампа біла, а та — жовта. У мене є три книги. Ці книги нові. Стіни білі. Це вікно велике, а те вікно мале. Той килим червоний. Я люблю свою кімнату.**
  replace: |
    **Це моя кімната. Мій стіл великий і новий. Це вікно велике, а те вікно мале. У мене є три книги. Ці книги нові. Цей зошит червоний. Та книга синя. Той зошит коштує сто гривень.**

- find: |
    *(This is my room. My table is big and new. This lamp is white, and that one is yellow. I have three books. These books are new. The walls are white. This window is big, and that window is small. That carpet is red. I love my room.)*
  replace: |
    *(This is my room. My table is big and new. This window is big, and that window is small. I have three books. These books are new. This notebook is red. That book is blue. That notebook costs one hundred hryvnias.)*

- find: |
    Read the text again and notice how it reviews A1.2 patterns. **моя кімната** shows a possessive, **великий і новий** shows adjective agreement, **ця/та/це/те** review demonstratives, and **три книги** plus **ці книги** review numbers and plurals. Use the text as a model and describe your own room in 4-5 short sentences.
  replace: |
    Read the text again and notice how it reviews A1.2 patterns. **моя кімната** and **мій стіл** show possessives, **великий і новий** shows adjective agreement, **це/те/той/та/ці** review demonstratives, and **три книги** plus **той зошит коштує сто гривень** review numbers and prices. Read it one more time and answer aloud: Which object is big? Which object is small? Which object costs one hundred hryvnias? Which things are plural? Use the text as a model and describe your own room in 4-5 short sentences.

- find: |
    Understanding the patterns of Ukrainian grammar allows you to build endless combinations of words. The first core pattern is noun gender. The gender of a Ukrainian noun dictates the shape of the words around it. You can identify masculine words by their consonant endings, such as **брат** (brother) or **стіл** (table). Feminine words typically end in **-а** or **-я**, like **сестра** (sister) and **книга** (book). Neuter words almost always end in **-о** or **-е**, as seen in **вікно** (window) and **море** (sea).

    The second pattern is adjective agreement. Adjectives must change their endings to match the gender of the noun they describe. You must also pay attention to hard stems and soft stems. Hard-stem adjectives use the endings **-ий**, **-а**, and **-е**. This creates combinations like **великий стіл** (big table) and **велика книга** (big book). Soft-stem adjectives, which are less common, use the endings **-ій**, **-я**, and **-є**. A classic example is **синій зошит** (dark blue notebook) or **синя лампа** (dark blue lamp).

    The third pattern involves demonstratives. When you want to point at objects, you contrast proximity using the words for "this" (here) versus "that" (there). Use **цей** (this masculine), **ця** (this feminine), or **це** (this neuter) for nearby objects. Use **той** (that masculine), **та** (that feminine), or **те** (that neuter) for objects farther away. If you are pointing at items on a table, you might contrast **цей глечик** (this jug) with **та вишиванка** (that embroidered shirt).

    The final pattern is forming plurals. You have learned the nominative plural endings for basic nouns, such as turning **стіл** into **столи** (tables), **книга** into **книги** (books), and **вікно** into **вікна** (windows). There is a golden rule for adjectives when describing groups: in the plural, adjectives always take the **-і** ending, regardless of gender. This makes plural agreement incredibly simple, resulting in phrases like **великі столи** (big tables) and **нові книги** (new books).
  replace: |
    Use this section as a quick checkpoint, not as new theory. Test noun gender with **він / вона / воно**: **стіл** is masculine, **книга** is feminine, and **вікно** is neuter. At this level, the familiar endings still help: consonant for many masculine nouns, **-а / -я** for many feminine nouns, and **-о / -е** for many neuter nouns.

    Next, match adjectives and possessives to the noun: **великий стіл, велика книга, велике вікно; мій стіл, моя книга, моє вікно.** Hard-stem adjectives usually end in **-ий**, while soft-stem adjectives like **синій** use **-ій**.

    Then review demonstratives: **цей / ця / це** point to something near you, and **той / та / те** point to something farther away. Say **цей глечик**, but **та вишиванка**.

    Finally, review plural patterns you already know: **стіл → столи, книга → книги, вікно → вікна.** In the plural, adjectives take **-і**: **великі столи, нові книги.** Numbers here stay vocabulary items: **три книги, сто гривень, двісті гривень.**

- find: |
    > **Іванко:** Добрий день! У вас є вишиванки? *(Good afternoon! Do you have embroidered shirts?)*
    > **Катя:** Так! Ця червона чи та синя? *(Yes! This red one or that blue one?)*
    > **Іванко:** Та синя. Скільки вона коштує? *(That blue one. How much does it cost?)*
    > **Катя:** Двісті гривень. *(Two hundred hryvnias.)*
  replace: |
    > **Іванко:** Катя, ця червона чи та синя? *(Katya, this red one or that blue one?)*
    > **Катя:** Та синя. *(That blue one.)*
    > **Іванко:** Добрий день! Скільки вона коштує? *(Good afternoon! How much does it cost?)*
    > **Катя:** Двісті гривень. *(Two hundred hryvnias.)*

- find: |
    > **Катя:** П'ятдесят гривень. Ці нові, дуже гарні. *(Fifty hryvnias. These are new, very beautiful.)*
  replace: |
    > **Катя:** П'ятдесят гривень. Ці нові. *(Fifty hryvnias. These are new.)*

- find: |
    > **Іванко:** Я беру три. А той глечик? *(I will take three. And that jug?)*
  replace: |
    > **Іванко:** Добре. Три писанки. А той глечик? *(Good. Three decorated eggs. And that jug?)*
</fixes>
## Linguistic Scan
Four issues found:
1. **Calque:** «Давайте уважно розглянемо» — «Давайте + дієслово» is a Russian grammatical calque («давайте рассмотрим»). Correct Ukrainian form is the 1st person plural imperative: «Уважно розгляньмо».
2. **Calque:** «приймати важливі рішення» — a widely known calque from Russian «принимать решение». The natural Ukrainian idiom is «ухвалювати рішення».
3. **Awkward phrasing:** «ми найчастіше звертаємо першу увагу» — unnatural word order and phrasing. Better: «ми найперше звертаємо увагу».
4. **False Tokenizer Flag:** `язкової` and `обов` were flagged as NOT IN VESUM, but these are just the word `обов’язкової` split by the apostrophe.

## Exercise Check
**Markers present:**
- `<!-- INJECT_ACTIVITY: match-up-match-portrait-lexis-to-body-categories -->` (After body lexicons)
- `<!-- INJECT_ACTIVITY: quiz-character-valence-... -->` (After character traits)
- `<!-- INJECT_ACTIVITY: fill-in-complete-a-portrait-description-... -->` (After family relationships)
- `<!-- INJECT_ACTIVITY: group-sort-sort-relationship-vocabulary-into-categories -->` (After dialogue)

**Issues found:**
- **Missing markers:** The `free-write` and `role-play` markers from the plan are COMPLETELY MISSING from the text. The writer replaced the `free-write` and `role-play` activities with manual bullet-point instructions at the end of the text. This breaks the activity injection pipeline. 

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | The module completely skips Section 6 «Опис людини: як писати портрет». It omits the composition structure (Зачин, основна частина, кінцівка), the artistic devices (епітети, порівняння, зменшувально-пестливі слова), and the required vocabulary word «портретна деталь». The H2 heading for Section 7 is also missing. |
| 2. Linguistic accuracy | 8/10 | Found two distinct calques («давайте розглянемо», «приймати рішення») and one instance of awkward phrasing («звертаємо першу увагу»). The rest of the Ukrainian text is grammatically correct and correctly handles complex morphology. |
| 3. Pedagogical quality | 6/10 | CRITICAL FLAW: The self-check at the end asks the learner to write a text «обов'язково використовуючи правильну тричастинну структуру шкільного твору-опису (зачин, основна частина, кінцівка)». This structure was never taught in the text because Section 6 was skipped. Testing concepts before teaching them is a pedagogical failure. |
| 4. Vocabulary coverage | 8/10 | Most required and recommended vocabulary is covered beautifully in context. However, the required term «портретна деталь» and the recommended term «кохання» are missing entirely. |
| 5. Exercise quality | 7/10 | Four of the six `<!-- INJECT_ACTIVITY: -->` markers are well-placed. However, the `free-write` and `role-play` markers are missing, causing the pipeline to lose these exercises. |
| 6. Engagement & tone | 10/10 | Excellent tone. The writer acts as an encouraging teacher and provides beautiful, culturally rooted explanations (e.g., explaining how «внутрішній світ» reflects in «зовнішність»). |
| 7. Structural integrity | 6/10 | The word count is 3628 (below the 4000 target). Section 6 is entirely missing, and the Section 7 H2 header is missing. |
| 8. Cultural accuracy | 10/10 | Flawless. Explains the profound cultural connection between «рід», «родина», and «Батьківщина», and correctly outlines Ukrainian family trees (e.g., свекруха vs теща). |
| 9. Dialogue & conversation quality | 10/10 | The dialogue at the Vinnytsia wedding is fantastic. It features natural multi-turn conversation with named speakers and culturally appropriate introductions. |

## Findings
[Dimension 7] [Critical]
Location: Entire text (after "Знайомство і представлення").
Issue: Word count is 3628 (below 4000 target). Section 6 «Опис людини: як писати портрет» from the plan is completely missing from the text, causing a ~400 word deficit.
Fix: Add the missing section using `insert_after` immediately after the «Знайомство і представлення» section.

[Dimension 1] [Critical]
Location: Entire text.
Issue: The plan points for «Опис людини: як писати портрет» (Composition structure, Художні засоби) and the required vocabulary «портретна деталь» are missing. 
Fix: Handled by the `insert_after` fix that adds the missing section.

[Dimension 3] [Critical]
Location: "* Опишіть зовнішність вашого найкращого друга або подруги. Напишіть від п'яти до семи розгорнутих речень, обов'язково використовуючи правильну тричастинну структуру шкільного твору-опису (зачин, основна частина, кінцівка)."
Issue: The exercise asks the learner to use the «тричастинну структуру шкільного твору-опису», which was never taught in the module. Testing concepts before teaching them is a pedagogical failure.
Fix: Handled by the `insert_after` fix that teaches this exact structure prior to the self-check.

[Dimension 5] [Major]
Location: End of the module.
Issue: The `<!-- INJECT_ACTIVITY: free-write... -->` and `<!-- INJECT_ACTIVITY: role-play... -->` markers are missing. 
Fix: Handled by the `insert_after` fix, which includes the two missing markers at their correct locations.

[Dimension 7] [Minor]
Location: "Тепер настав час для самостійної перевірки ваших знань."
Issue: The H2 heading `## Підсумок: людина у словах` from the plan is missing before the final section.
Fix: Add the missing heading using find/replace.

[Dimension 2] [Major]
Location: "Давайте уважно розглянемо, як саме ця портретна лексика працює на практиці"
Issue: «Давайте + дієслово» is a grammatical calque from Russian («давайте рассмотрим»). In Ukrainian, the 1st person plural imperative («розгляньмо») should be used.
Fix: Replace with "Уважно розгляньмо, як саме ця портретна лексика працює на практиці".

[Dimension 2] [Major]
Location: "Їй властиво дуже швидко приймати важливі рішення"
Issue: «приймати рішення» is a direct calque of the Russian «принимать решение». The correct Ukrainian idiom is «ухвалювати рішення».
Fix: Replace "приймати важливі рішення" with "ухвалювати важливі рішення".

[Dimension 2] [Minor]
Location: "ми найчастіше звертаємо першу увагу на вік (age) та зріст (height)."
Issue: «звертаємо першу увагу» is awkward phrasing. «Найперше звертаємо увагу» is natural Ukrainian.
Fix: Replace with "ми найперше звертаємо увагу на вік (age) та зріст (height)."

## Verdict: REVISE
The writer completely skipped an entire 600-word pedagogical section, missing key plan structures, required vocabulary, and activity markers. Crucially, the module tests the learner on a concept (the three-part portrait structure) that it forgot to teach. The fixes below correct the calques, insert the missing section, and restore the pipeline markers.

<fixes>
- find: "Давайте уважно розглянемо, як саме ця портретна лексика працює на практиці"
  replace: "Уважно розгляньмо, як саме ця портретна лексика працює на практиці"
- find: "ми найчастіше звертаємо першу увагу на вік (age) та зріст (height)."
  replace: "ми найперше звертаємо увагу на вік (age) та зріст (height)."
- find: "Їй властиво дуже швидко приймати важливі рішення"
  replace: "Їй властиво дуже швидко ухвалювати важливі рішення"
- insert_after: "Згадайте наш найважливіший інструмент для звертання — **кличний відмінок** *(vocative case)*."
  text: "\n\n<!-- INJECT_ACTIVITY: role-play-introduce-a-friend-to-a-colleague-using-formal-register-then-informally -->\n\n## Опис людини: як писати портрет\n\nЩоб ваші розповіді про людей звучали справді літературно і глибоко, важливо знати класичну структуру українського **твору-опису зовнішності людини**. Згідно з академічною традицією, такий портрет завжди має чітку тричастинну структуру. Перша частина — це **зачин** *(introduction)*. Тут ви коротко пояснюєте, хто саме ця людина і за яких обставин ви з нею познайомилися. Друга, найбільша частина — це **основна частина** *(main body)*. У ній ми послідовно описуємо те, що найперше впадає в очі, потім переходимо до зросту, постави та статури. Далі детально аналізуємо риси обличчя, волосся та погляд. Насамкінець описуємо стиль одягу. Третя частина — це **кінцівка** *(conclusion)*, де ми формулюємо наше загальне враження від особистості та характеру цієї людини.\n\nЩоб текст не був схожий на сухий поліцейський протокол, українські письменники майстерно використовують яскраві **художні засоби** *(artistic devices)*. По-перше, це красиві **епітети** — художні означення, які створюють емоційний образ. Наприклад: «сивий, як голуб», «увесь білий-білий», «чистий, аж світиться». По-друге, ми часто використовуємо **порівняння** *(comparisons)*: «її очі, як сині волошки», «він стрункий, наче тополя». По-третє, українській мові дуже властиві **зменшувально-пестливі слова** *(diminutives)*, які додають тексту ніжності: замість звичайних слів ми кажемо «оченята», «рученьки», «кучерики». І нарешті, найвищим пілотажем у написанні портрета є влучна **портретна деталь** *(portrait detail)*. За визначенням українських мовознавців, це зображення лише однієї, але надзвичайно прикметної і яскравої риси зовнішності, яка моментально розкриває характер персонажа (наприклад, глибокий шрам, незвичайна родимка або особлива, дуже щира усмішка).\n\nПодивімося, як усе це працює разом, на прикладі адаптованого літературного уривка:\n\n> «Моя бабуся Марія — найсвітліша людина в моєму житті *(зачин)*. Вона невисока на зріст, тендітна, але має напрочуд рівну і горду поставу. Найперше, що впадає в очі — це її сиве, як срібло, волосся, завжди охайно зібране на потилиці. У неї добре, кругле обличчя, вкрите дрібною мережею зморшок, які розповідають про довге і складне життя. Але найголовніша її портретна деталь — це великі, ясні очі, які завжди світяться теплом і безмежною любов'ю. Одягнена вона зазвичай у просту, але дуже гарно вишиту сорочку *(основна частина)*. Коли я дивлюся на неї, я відчуваю неймовірний спокій і абсолютну довіру *(кінцівка)*».\n\nСпробуйте використати ці художні засоби та чітку структуру, коли будете писати свої власні тексти. Це зробить вашу українську мову живою, багатою та надзвичайно емоційною.\n\n<!-- INJECT_ACTIVITY: free-write-write-a-structured-portrait-of-a-real-or-fictional-person -->"
- find: "Тепер настав час для самостійної перевірки ваших знань."
  replace: "## Підсумок: людина у словах\n\nТепер настав час для самостійної перевірки ваших знань."
</fixes>
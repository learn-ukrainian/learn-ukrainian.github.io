

Now I have all the data I need. Here is the full adversarial review:

---

## Linguistic Scan

**Russianisms:** None found. All 623 verified words exist in VESUM. Proper nouns (Олена, Марк, Оксана, Ігор) correctly flagged as not-in-VESUM — these are valid proper names.

**Surzhyk:** None found.

**Calques:** 
- "Це звучить чудово" (Марк's dialogue line) — [NEEDS RAG VERIFICATION] Potential calque of English "That sounds wonderful" / Russian "Это звучит замечательно." Ukrainian "звучати" primarily means "to produce sound," not "to seem/appear." More natural: "Це чудово!" or "Як гарно!" However, this usage is increasingly common in modern Ukrainian speech, and appearing in dialogue makes it more defensible. Flagging as **minor**.

**Paronyms:** None found.

**Russian characters (ы, э, ё, ъ):** None found.

**Grammar/case claims — all verified correct:**
- Locative feminine -я/-а → -і: correct (кухня→на кухні, спальня→у спальні)
- Locative masculine -он/-ор → -і: correct (балкон→на балконі, коридор→у коридорі)
- "з" + Gen for material (з дерева), "з" + Instr for accompaniment (з вікнами): correct
- Partitive Genitive (чаю, кави): correct
- Motion vs position (за стіл Acc vs за столом Instr): correct
- "дякувати" + Dat, "допомагати" + Dat: correct
- "після" + Gen, "перед" + Instr: correct
- Instrumental for transport (автобусом): correct

**Preposition usage на/у with rooms:** The module states «на кухні», «на балконі» vs «у вітальні», «у спальні», «у коридорі» — this is correct and follows Ukrainian convention.

## Exercise Check

**Marker inventory:**
1. `<!-- INJECT_ACTIVITY: fill-in, Complete a description of a home with the correct case forms for room and furniture nouns -->` — after Section 1 ✓
2. `<!-- INJECT_ACTIVITY: quiz, Choose the correct case form in daily routine sentences (time expressions, prepositions, verbs) -->` — after Section 2 ✓
3. `<!-- INJECT_ACTIVITY: match-up, Match daily activities with the correct time of day and appropriate case construction -->` — after Section 2 ✓
4. `<!-- INJECT_ACTIVITY: error-correction, Find and correct grammar errors in sentences involving case usage in home/routine contexts -->` — after Section 3 ✓

**Assessment:**
- All 4 plan `activity_hints` have corresponding markers: fill-in (8), quiz (8), match-up (8), error-correction (6) ✓
- Markers placed AFTER relevant teaching sections ✓
- Distribution: 1 after §1, 2 after §2, 1 after §3 — reasonable spread ✓
- Each marker tests language skill (case forms), not content recall ✓

No exercise issues found.

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | **Covered well:** All 4 content_outline sections present. Dialogue in §1 covers rooms + furniture + cases (Nom, Gen, Loc). §2 covers monologue + daily verbs + time expressions + weekday/weekend contrast. §3 covers hospitality + case synthesis. §4 has guided task + checklist + model answer. **Missing:** Plan §1 lists "кабінет" in room vocabulary — absent from content. Plan §1 lists "полиця" in furniture vocabulary (PULS confirms A2 level) — absent from content. Plan §2 lists "під час роботи (Gen.)" as a time expression — absent. Plan §3 point 4 lists "для гостей (Gen.)" and "з цукром (Instr.)" as case-in-action examples — both absent. These are explicit plan sub-points not covered. |
| 2. Linguistic accuracy | 9/10 | All Ukrainian forms verified against VESUM (623/623 pass). Grammar explanations are factually correct: Locative endings, Genitive for absence/quantity, Instrumental for transport/accompaniment, partitive Genitive, motion vs position distinction. No Russianisms, no surzhyk, no calques confirmed. One minor potential calque: "Це звучить чудово" (see Linguistic Scan). |
| 3. Pedagogical quality | 8/10 | **Strengths:** Excellent PPP flow — each section opens with a natural situation (dialogue/monologue), then extracts the grammar pattern, then provides multiple examples. The "з" + Gen vs "з" + Instr distinction (§1) is a pedagogical highlight with clear minimal pair. The motion/position distinction "за стіл" vs "за столом" (§3) is well done. Partitive Genitive explanation is clear. **Weakness:** Example sentences in §1 after the dialogue ("Олена готує смачний обід на кухні. Вона міцно спить у спальні кожної ночі.") break from the narrative context — Olena is mid-video-tour, yet suddenly we get standalone habitual sentences. This disconnects the situation from the pattern practice. |
| 4. Vocabulary coverage | 8/10 | **Required vocab present:** помешкання ✓, кімната ✓, кухня ✓, спальня ✓, вітальня ✓, меблі ✓, розпорядок дня ✓, вставати ✓, снідати ✓, лягати спати (in summary only — not contextualized in §2). **Recommended present:** балкон ✓, коридор ✓, килим ✓, пригощатися ✓, господар ✓. **Missing from plan room list:** кабінет. **Missing from plan furniture list:** полиця. Both are A2-level words per PULS. "Лягати спати" appears only in the Підсумок, never used in §2's narrative — it should be naturally embedded in the daily routine monologue. |
| 5. Exercise quality | 9/10 | All 4 activity types from plan present with correct markers. Well-placed after teaching content. Each tests case usage (language skill), not content recall. |
| 6. Engagement & tone | 7/10 | **Adjective padding is pervasive.** Nearly every noun carries 1-3 modifiers, creating an unnaturally dense, LLM-generated feel. Examples: "великий м'який **диван**" → "два дуже зручні **крісла**" → "теплий і пухнастий **килим**" → "велика сучасна **картина**" → "просторий і світлий **офіс**" → "розумні і приємні **колеги**" → "новий міцний **стіл**" → all in rapid succession. **Repetitive filler:** "із задоволенням" appears 3× ("Олена із задоволенням продовжує", "Ігор із задоволенням п'є", "Там вони із задоволенням обідають"). **"Дуже" overuse** throughout. The word count is 2652 vs 2000 target — the module is 33% over target, and much of the excess is this adjective padding rather than additional teaching content. |
| 7. Structural integrity | 9/10 | Clean markdown. All 4 sections + Підсумок present and correctly ordered. H2 headings match plan section titles. Word count 2652 is above the 2000 target (acceptable — over is better than under). No stray tags or formatting artifacts. |
| 8. Cultural accuracy | 10/10 | Shoe removal at door with капці (not Russicism "тапочки") ✓. Bringing гостинці when visiting ✓. Host offers food/drink insistently ✓. "Пригощайтеся" ✓. No "like Russian but..." framing. Ukrainian presented entirely on its own terms. |
| 9. Dialogue & conversation quality | 8/10 | Named speakers throughout (Олена/Марк, Оксана/Ігор) ✓. Realistic situations: video tour of apartment, visiting friends for dinner ✓. Culturally appropriate hospitality ✓. §3 dialogue is the strongest — natural flow with shoe removal, gift giving, offering food. **Weakness:** §1 dialogue is somewhat one-directional (Олена shows, Марк reacts with "Ого!", "Класно!", "Дуже затишно"). Марк's responses are mostly enthusiastic filler rather than substantive engagement. |

## Findings

**[PLAN ADHERENCE] [MAJOR]**
Location: Section 1 — room vocabulary list in plan says "кухня, спальня, вітальня, ванна кімната, коридор, балкон, кабінет"
Issue: "Кабінет" (study/office) is absent from the entire module. Plan explicitly lists it as a room to teach.
Fix: Add "кабінет" naturally into the apartment tour in §1.

**[PLAN ADHERENCE] [MAJOR]**
Location: Section 1 — furniture vocabulary list in plan says "диван, крісло, стіл, стілець, шафа, ліжко, полиця, дзеркало, килим"
Issue: "Полиця" (shelf, PULS A2) is absent from the entire module. Plan explicitly lists it.
Fix: Add "полиця" naturally into the home description.

**[VOCABULARY COVERAGE] [MAJOR]**
Location: Section 2 — daily routine monologue
Issue: "Лягати спати" appears only in the Підсумок summary, never used naturally in §2's daily routine narrative where it belongs. The plan's "daily actions" list includes it.
Fix: Insert "лягати спати" into Ігор's evening routine in §2.

**[PLAN ADHERENCE] [MINOR]**
Location: Section 2 — time expressions
Issue: Plan lists "під час роботи (Gen.)" as a time expression to teach. Not present in module.
Fix: Add naturally to §2.

**[PLAN ADHERENCE] [MINOR]**
Location: Section 3 — "Cases in action" sub-point
Issue: Plan lists "для гостей (Gen.)" and "з цукром (Instr.)" — both absent from §3 content.
Fix: Integrate into the dinner scene dialogue/prose.

**[ENGAGEMENT] [MAJOR]**
Location: Throughout, worst in §1 and §2
Issue: Pervasive adjective padding creates unnatural, LLM-generated prose. Almost every noun has 1-3 adjectives stacked. "Надзвичайно сильно" is a double intensifier. "Із задоволенням" appears 3×. Module is 33% over word target, largely from padding rather than teaching content.
Fix: Trim redundant adjectives and filler. Targeted replacements below.

**[ENGAGEMENT] [MINOR]**
Location: §1, Марк's dialogue — "Це звучить чудово."
Issue: Potential calque of "That sounds wonderful." More natural Ukrainian: "Це чудово!" or "Як гарно!"
Fix: Replace with natural Ukrainian expression.

## Verdict: REVISE

The module has strong pedagogical foundations — grammar explanations are accurate, case distinctions are well-taught (especially "з" Gen/Instr and motion/position), cultural content is authentic, and exercise placement is correct. However, it has two systematic issues requiring fixes: (1) missing plan vocabulary items (кабінет, полиця, лягати спати in context), and (2) pervasive adjective padding that hurts naturalness and engagement. Neither issue requires a rewrite — targeted fixes can address both.

<fixes>
- find: "А в кутку стоїть новий торшер, який дає приємне світло ввечері."
  replace: "А в кутку стоїть торшер, який дає приємне світло ввечері. Біля стіни є книжкова полиця з моїми улюбленими книжками."
- find: "Покажи мені, будь ласка, інші кімнати у твоєму новому домі."
  replace: "А чи є у тебе окремий кабінет для роботи?\n> — **Олена:** Кабінету, на жаль, немає. Але я маю маленький письмовий стіл у спальні. Ходімо, покажу тобі інші кімнати."
- find: "Ось тут стоїть великий м'який **диван** *(sofa)*. А поруч є два дуже зручні **крісла** *(armchairs)*. На підлозі лежить теплий і пухнастий **килим** *(carpet)*."
  replace: "Ось тут стоїть великий м'який **диван** *(sofa)*. А поруч є два зручні **крісла** *(armchairs)*. На підлозі лежить теплий **килим** *(carpet)*."
- find: "На стіні висить велика сучасна картина. Її намалювала моя талановита сестра."
  replace: "На стіні висить картина. Її намалювала моя сестра."
- find: "Це звучить чудово."
  replace: "Як гарно!"
- find: "Олена із задоволенням продовжує показувати свою нову квартиру. Вона докладно розповідає про свої нові **меблі** *(furniture)* та різні матеріали."
  replace: "Олена продовжує показувати квартиру. Вона розповідає про свої **меблі** *(furniture)* та матеріали, з яких вони зроблені."
- find: "На світлій кухні стоїть новий міцний стіл **з дерева** *(of wood — Genitive)*."
  replace: "На кухні стоїть міцний стіл **з дерева** *(of wood — Genitive)*."
- find: "Це дуже простора кімната **з великими чистими вікнами** *(with large clean windows — Instrumental)*."
  replace: "Це простора кімната **з великими вікнами** *(with large windows — Instrumental)*."
- find: "У маленькій спальні стоїть **зручне ліжко** *(comfortable bed)*. Поруч стоїть висока і **велика шафа** *(large wardrobe)* для одягу. Олена також нещодавно купила гарне кругле дзеркало з дерев'яною рамою. Марку надзвичайно сильно подобається нове помешкання його подруги Олени."
  replace: "У спальні стоїть **зручне ліжко** *(comfortable bed)*. Поруч стоїть **велика шафа** *(large wardrobe)* для одягу. Олена також нещодавно купила кругле дзеркало з дерев'яною рамою. Марку дуже подобається нове помешкання Олени."
- find: "Він щиро каже, що це ідеальне і затишне місце для спокійного життя. Олена повністю погоджується, адже вона дуже довго шукала саме таку ідеальну квартиру."
  replace: "Він щиро каже, що це затишне місце для життя. Олена погоджується — вона довго шукала саме таку квартиру."
- find: "Ігор має дуже чіткий і організований **розпорядок дня** *(daily routine)*."
  replace: "Ігор має чіткий **розпорядок дня** *(daily routine)*."
- find: "Там він довго **вмивається** *(washes his face)* холодною водою. Потім він іде в спальню і швидко **одягається** *(gets dressed)* у новий діловий костюм. Ігор завжди дуже ретельно **готується** *(prepares)* до свого нового робочого дня."
  replace: "Там він **вмивається** *(washes his face)* холодною водою. Потім він іде в спальню і **одягається** *(gets dressed)*. Ігор завжди ретельно **готується** *(prepares)* до робочого дня."
- find: "Ігор із задоволенням п'є міцну каву **вранці** *(in the morning)*. Він дуже багато і наполегливо працює **вдень** *(in the afternoon)*. Ігор спокійно відпочиває вдома зі своєю родиною **увечері** *(in the evening)*. А пізно **вночі** *(at night)* він просто міцно спить у своєму ліжку."
  replace: "Ігор п'є каву **вранці** *(in the morning)*. Він багато працює **вдень** *(in the afternoon)*. Ігор відпочиває вдома з родиною **увечері** *(in the evening)*. А **вночі** *(at night)* він міцно спить."
- find: "Ігор завжди ретельно вмивається **перед роботою** *(before work)*. Маленькі діти обов'язково миють руки **перед сном** *(before sleep)*."
  replace: "Ігор завжди ретельно вмивається **перед роботою** *(before work)*. Маленькі діти обов'язково миють руки **перед сном** *(before sleep)*. Ігор часто слухає музику **під час роботи** *(during work — Genitive)*."
- find: "Він працює у просторому і світлому **офісі** *(office)* на десятому поверсі."
  replace: "Він працює в **офісі** *(office)* на десятому поверсі."
- find: "Ігор працює там зі своїми розумними і приємними **колегами** *(colleagues)*."
  replace: "Ігор працює там зі своїми **колегами** *(colleagues)*."
- find: "Там вони із задоволенням **обідають** *(have lunch)*. Іноді Ігор не має багато вільного часу на повноцінний гарячий обід."
  replace: "Там вони разом **обідають** *(have lunch)*. Іноді Ігор не має часу на повноцінний обід."
- find: "Спочатку він ретельно **прибирає пилососом** *(vacuums)* новий м'який килим у просторій вітальні."
  replace: "Спочатку він **прибирає пилососом** *(vacuums)* килим у вітальні."
- find: "Потім він іде на світлу кухню і починає **мити посуд** *(wash the dishes)* після спільної сімейної вечері."
  replace: "Потім він іде на кухню і починає **мити посуд** *(wash the dishes)* після сімейної вечері."
- find: "Увечері Ігор також повинен акуратно **прасувати одяг** *(iron clothes)* на завтрашній робочий день. Це його цілком звичайні і щоденні обов'язки у будні дні."
  replace: "Увечері Ігор також **прасує одяг** *(irons clothes)* на завтра. О пів на одинадцяту він зазвичай **лягає спати** *(goes to bed)*. Це його звичайні обов'язки у будні."
- find: "А в неділю він з радістю їде в гості до своїх батьків у село."
  replace: "А в неділю він їде в гості до батьків у село."
- find: "О, дуже дякуємо! Це так приємно і несподівано."
  replace: "О, дуже дякуємо! Це так приємно. Будь ласка, заходь далі. Ми приготували каву з цукром і тістечка для гостей."
</fixes>

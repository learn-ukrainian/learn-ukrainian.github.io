All verification complete. Here is my full adversarial review:

---

## Linguistic Scan

**Russianisms:** None found. All Ukrainian vocabulary verified against VESUM (134/134 content words confirmed, 6 proper nouns/fragments correctly flagged as not-in-dictionary).

**Surzhyk:** None found.

**Calques:** None found. The tip about **ходімо** vs **давай підемо** is explicitly confirmed by Антоненко-Давидович ("Часто забувають, що українська мова має в наказовому способі... форму 1–ї особи множини – читаймо, робімо. Російська мова, не маючи цієї форми, користується описовою конструкцією типу давайте читать") AND by three Grade 7 textbooks (Заболотний: "У творенні форм наказового способу не використовуємо частки давай, давайте"; Litvinova: "Форми наказового способу не утворюють за допомогою слова давати"; Avramenko: "Для творення форм наказового способу не використовуємо частки давай(те)").

**Paronyms:** None found.

**Russian characters (ы, э, ё, ъ):** None found.

**Gender/case verification:**
- "Сторінку двадцять три" — accusative of сторінка (f) ✓
- "Дай мені меню" — dative мені ✓, indeclinable меню ✓
- "Офіціанте" — vocative of офіціант (m) ✓ (VESUM confirmed)
- "Олесю" — vocative of Олесь (m) ✓

**Imperative forms verified against VESUM (all confirmed):** скажіть, пишіть, говоріть, ходіть, дивіться, ідіть, сядьте, читайте, слухайте, відкрийте, принесіть, покажіть, запитуйте, подивіться, візьміть, їжте, дайте, напишіть, сідайте, прочитай, подивись, ходімо, сідай, тістечко, офіціанте, тихо, подивіться.

**Factual claims verified:**
- "Ukrainian writes ь after д in imperative forms (confirmed by Авраменко, Grade 7)" — Grade 7 Avramenko textbook confirms: "У дієсловах наказового способу пишемо м'який знак у кінці слова та складу після д, т, з, с, ц, л, н: лізь, лізьте, будь, будьте..." ✓
- "If you open any Ukrainian textbook by Заболотний, every page says Робіть вправу! or Спишіть речення!" — Confirmed by RAG search of Grade 5 Заболотний (exercises 269, 270 etc. use exactly these imperative patterns) ✓

**No linguistic errors found.**

## Exercise Check

**Activity markers found (4):**
1. `<!-- INJECT_ACTIVITY: fill-in-imperative-forms -->` — after "Як утворити?" formation section, tests ти/ви form creation ✓
2. `<!-- INJECT_ACTIVITY: quiz-correct-imperative -->` — after irregular verbs list, tests choosing correct imperative ✓
3. `<!-- INJECT_ACTIVITY: group-sort-ty-vy -->` — in Підсумок, tests ти vs ви sorting ✓
4. `<!-- INJECT_ACTIVITY: fill-in-context-ty-vy -->` — in Підсумок, tests contextual register choice ✓

**Marker-to-plan mapping:**
| Plan hint | Marker | Match |
|-----------|--------|-------|
| fill-in (10 items): Form imperative | fill-in-imperative-forms | ✓ |
| quiz (8 items): Choose correct | quiz-correct-imperative | ✓ |
| group-sort (10 items): ти vs ви | group-sort-ty-vy | ✓ |
| fill-in (6 items): Context ти/ви | fill-in-context-ty-vy | ✓ |

**Placement:** Markers 1-2 appear after the relevant teaching content. Markers 3-4 are in the Summary, which tests cumulative knowledge — pedagogically sound for a review section.

**Count:** 4 markers = 4 plan hints. Full coverage. ✓

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | All four content_outline sections covered with correct topics. Both dialogues from plan implemented faithfully (classroom ви-forms, café ти-forms). All required vocabulary (читати, писати, слухати, дивитися, говорити, дати, сказати, іти) and all recommended vocabulary (відкрити, сісти, показати, запитати, підручник, сторінка, речення) used naturally in prose. All 4 activity markers match plan hints. **Deduction:** Summary claims "direct a volleyball warm-up" but no volleyball dialogue exists — the volleyball practice was in `dialogue_situations` but not in `content_outline`, and the writer correctly followed the outline. The false claim in the summary needs removal. |
| 2. Linguistic accuracy | 10/10 | All 30+ imperative forms verified against VESUM — every one confirmed. Formation rules are correct for A1 simplification level. Soft-sign rule after д cited to Авраменко Grade 7, confirmed by RAG. The ходімо tip confirmed by Антоненко-Давидович AND three Grade 7 textbooks. No Russianisms, surzhyk, calques, or paronyms. Gender/case correct throughout (сторінку acc.f, офіціанте voc.m, Олесю voc.m). |
| 3. Pedagogical quality | 9/10 | Excellent PPP flow: dialogues present imperatives in context → rules explain the pattern → exercises practice. Multiple examples per point (8 ти-forms, full ви-form derivation table, 4 irregular verbs). Textbook pedagogy referenced (Заболотний, Авраменко). Cultural note about imperatives not being rude is essential and well-placed. Politeness escalation ladder (Дай → Дай, будь ласка → Дайте, будь ласка → Пане Іване, дайте, будь ласка) is excellent. **Minor deduction:** The ви-formation rule states "if the ти-form ends in -й, add -те; if it ends in -и, change to -іть" but then lists дивись → дивіться and сядь → сядьте without noting these don't follow the stated two-pattern rule. A learner applying the rule mechanically wouldn't know how to handle -сь or -ь endings. |
| 4. Vocabulary coverage | 10/10 | All 8 required verbs appear naturally in dialogues AND formation tables. All 7 recommended words (відкрити, сісти, показати, запитати, підручник, сторінка, речення) appear in context — not as bare lists. Additional high-value words introduced naturally: тістечко, офіціант, словник, погода, меню. |
| 5. Exercise quality | 10/10 | All 4 plan activity hints matched with correctly-named markers. Placement is logical — formation exercises after teaching, cumulative exercises in summary. The fill-in-context exercise (Олено, ___ книжку! / Пане Іване, ___ книжку!) tests register-switching, which is the core skill. Group-sort (ти vs ви) tests form recognition. |
| 6. Engagement & tone | 9/10 | No motivational openers, no meta-commentary, no gamified language. Dialogues are specific and culturally grounded. The ти/ви switch mid-dialogue (Олесь to waiter: принесіть) is a natural, clever teaching moment. The politeness escalation ladder is engaging. **Deduction:** "Here are the essential imperatives you now know" is mildly tell-not-show. The false volleyball claim ("direct a volleyball warm-up") promises something the module doesn't deliver. |
| 7. Structural integrity | 10/10 | Four H2 sections match plan exactly: Діалоги → Наказовий спосіб → Як утворити? → Підсумок. Clean markdown. Word count 1263 ≥ 1200 target. No stray tags or formatting artifacts. :::tip block correctly formatted. |
| 8. Cultural accuracy | 10/10 | Decolonized: ходімо presented as "uniquely Ukrainian" with Russian lacking this form — not "like Russian but with -мо." The textbook reference to Заболотний and Авраменко grounds this in Ukrainian pedagogy. The note about imperatives not being rude addresses a real English-speaker misconception without overcorrecting. |
| 9. Dialogue & conversation quality | 10/10 | Two multi-turn dialogues with named speakers (Вчителька/Учень/Учениця; Олесь/Дарина). Natural situations: classroom instruction, café with friends. Register contrast demonstrated organically (ти between friends, ви to class, ви to waiter). The waiter moment is particularly effective — Олесь switches register mid-conversation. Culturally appropriate: "Дякую, Олесю!" with vocative. |

## Findings

**[PLAN ADHERENCE / ENGAGEMENT] [SEVERITY: minor]**
Location: Підсумок section, paragraph 1: "You can give instructions in the classroom, order at a café, and direct a volleyball warm-up."
Issue: The module claims the learner can "direct a volleyball warm-up" but no volleyball dialogue or vocabulary was included. The volleyball practice was in the plan's `dialogue_situations` field but NOT in the `content_outline` — the writer correctly followed the outline but then falsely claimed volleyball in the summary.
Fix: Remove the volleyball claim. Replace with something the module actually teaches.

**[PEDAGOGICAL QUALITY] [SEVERITY: minor]**
Location: "Як утворити?" section, ви-form rule: "The rule: if the ти-form ends in -й, add -те; if it ends in -и, change to -іть:"
Issue: The stated rule covers -й and -и endings, but the examples immediately following include дивись → дивіться (-сь ending) and сядь → сядьте (-ь ending) without noting these are exceptions. A learner applying the two-pattern rule mechanically would be confused by forms not ending in -й or -и.
Fix: Add a brief note after the examples acknowledging these two special cases.

## Verdict: REVISE

Two minor findings — one factual claim (volleyball) and one pedagogical clarity gap (formation rule exceptions). No linguistic errors. No critical or major issues. All dimensions ≥9. The fixes are small and precise.

<fixes>
- find: "You can give instructions in the classroom, order at a café, and direct a volleyball warm-up."
  replace: "You can give instructions in the classroom, order at a café, and make polite requests to strangers."
- find: "- дивись → **дивіться**, сядь → **сядьте**, іди → **ідіть**"
  replace: "- іди → **ідіть**\n\nTwo special cases: reflexive **дивись** adds **-ся** → **дивіться**, and soft-sign **сядь** simply adds **-те** → **сядьте**."
</fixes>

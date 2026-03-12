# Дослідження: Numerals and Case Agreement

## State Standard Reference

**§4.2.1.3** (lines 1235–1242): "Числівник: відмінково-родові форми порядкових числівників із закінченнями -ий, -а, -е: *десятий, десятого; десята, десятої; десяте, десятого*; відмінково-родові форми порядкових числівників із закінченнями -ій, -я, -є: *третій, третього; третя, третьої; третє, третього*; відмінково-родові форми кількісного числівника один: *один, одного, одному, одним, на одному (однім); одна, одної, одній, одною, на одній*."

**§4.2.2.2.1** (lines 1271–1272): "позначення кількості та міри в поєднанні з кількісними числівниками: *Ми маємо вісімдесят гривень. Треба їсти багато фруктів.*"

**Alignment**: The Standard explicitly requires (a) ordinal numeral gender/case declension and (b) cardinal numeral один's full paradigm at A2. The Genitive case section directly mandates quantity expressions with cardinal numerals. The three-zone agreement model (один / два–чотири / п'ять+) is the practical implementation of §4.2.2.2.1. The module covers all required Standard content and extends it to the most common A2 daily-life contexts (prices, ages, times).

**Note**: The Standard does not enumerate the два/дві gender distinction or the 11–14 trap as separate items at A2 — these are implied by the everyday quantity expressions requirement and are included in multiple Grade 6 NUS textbooks (Golub 2023, Litvinova 2023) as core material.

---

## Vocabulary Frequency

| Word | Frequency / IPM (GRAC) | Key collocations / Notes |
|------|------------------------|--------------------------|
| один | 941,052 / 464.96 | один раз, один день, одна людина — extremely high; baseline for Zone 1 |
| два | 740,918 / 366.08 | два роки, два рази, два місяці — very high |
| рік | 689,120 / 340.49 | один рік / два роки / п'ять років — critical for age expressions |
| три | (expect ~280K) | три дні, три роки — high; verify at build |
| скільки | 213,067 / 105.27 | скільки коштує, скільки років, скільки зупинок — core question word |
| п'ять | 239,593 / 118.38 | п'ять хвилин, п'ять гривень — marks Zone 3 entry |
| гривня | 16,063 / 7.94 | одна гривня / дві гривні / п'ять гривень — key for Zone paradigm drill; lower raw freq because compound currency expressions use inflected forms |

**Source**: GRAC corpus (2B tokens), queried 2026-03-12.

---

## Cultural Hooks

**1. Двоїна — the ancient dual number that explains Zone 2 (двоїна, Wikipedia)**

Ukrainian preserved двоїна (dual number) better than any other Eastern Slavic language. Двоїна was a third grammatical number (singular / dual / plural) inherited from Proto-Indo-European via Proto-Slavic. In Ukrainian, numerals два, три, чотири triggering Nominative Plural — rather than Genitive Singular as in some other Slavic languages — is a direct trace of dual-number morphology still alive in the language.

Critical decolonized framing: The 1933 Soviet spelling reform explicitly suppressed двоїна. Deputy Commissar of Education Andrii Khvylia stated the reform aimed "to remove the wedge between Ukrainian and Russian" in grammar. Двоїна was banned alongside the letter ґ and other distinctly Ukrainian features. Ukrainian uniquely preserved the stress-based trace of двоїна: **два бра́ти** (dual-origin stress) vs. **всі брати́** (plural stress) — functional differentiation that survives in standard modern Ukrainian. In 1934, a university lecturer was fired for giving a lecture about двоїна.

**2. Гривня — all three zones in one everyday word (currency context)**

The Ukrainian hryvnia (гривня) provides a natural three-zone paradigm in a single lexical item that learners encounter immediately. *Одна гривня* (Zone 1, Nom. sg.), *дві гривні* (Zone 2, Nom. pl.), *п'ять гривень* (Zone 3, Gen. pl. with zero ending). The name *гривня* itself descends from a medieval term for a gold ingot shaped like a neck collar (*грива* — mane), connecting modern currency to Kyivan Rus economic history. This provides a memorable cultural anchor across all three agreement zones.

---

## Common Learner Errors

1. **два/дві gender confusion**: *\*два пляшки → дві пляшки* (f.) — English has no grammatical gender; learners default to invariant `два`. Grade 6 textbooks (Litvinova 2023, §51) explicitly drill this as a priority error. Compound forms trigger the same error: *\*двадцять два книги → двадцять дві книги*.

2. **The 11–14 trap (over-applying the last-digit rule)**: *\*одинадцять друзі → одинадцять друзів* — Learners who correctly learn the "last digit" rule for compound numerals misapply it to 11–14. These are always Zone 3 regardless of ending. Glazova (Grade 11) explicitly addresses this: teens 11–20 always govern Genitive Plural.

3. **Zone 1/Zone 3 conflation in oblique cases**: *\*про два учня → про двох учнів* — In oblique cases, the noun and numeral align in the same case (both take Gen/Dat/Instr forms). Learners sometimes keep the nominative zone logic in non-nominative contexts. Karaman (Grade 10, §68) names this "parallel usage in oblique cases" and treats it as an advanced error.

---

## Cross-References

- **Builds on**:
  - `a2-025` (Numerals and Nouns) — basic cardinal/ordinal introduction
  - A1 basic numerals (один–десять), A2 Genitive Plural endings
  - A2 modules on Genitive case (zero endings: книг, міст; -ів ending: друзів)

- **Prepares for**:
  - `a2-027` (If I Were) — conditional mood; age/time expressions recur
  - A2 shopping contexts — price expressions (скільки коштує?) require all three zones
  - B1 collective numerals (двоє, троє, п'ятеро) — extends Zone 2 logic

---

## Textbook Source Notes

- **Golub 2023, Grade 6, §61** (tier 1 — NUS): "Узгодження числівників з іменниками" — primary classroom source; includes schema of three agreement zones.
- **Litvinova 2023, Grade 6, §51** (tier 1 — NUS): Explicitly notes два, три, чотири + Nominative Plural; flags that *два/три/чотири* do **not** combine with 4th-declension nouns (use collective numerals instead — двоє телят).
- **Glazova 2019, Grade 11**: "При числівниках п'ять і тих, що позначають наступні числа, іменники вживають у формі родового відмінка множини: *п'ять будинків, десять дерев, двадцять сім відсотків.*"
- **Karaman 2018, Grade 10, §68**: Three declension types (I: один; II: 2,3,4; III: 5–20, 30, 50–80); oblique cases require numeral+noun agreement in same case: *двох будинків, трьом учням*.
- **Avramenko 2019, Grade 11**: "Складні випадки узгодження числівника" — fractional numerals trigger Genitive singular (out of scope for A2, but confirms that three-zone logic is the standard A2 frame).

---

## Notes for Content Writing

- **Decolonized framing**: Present двоїна as evidence of Ukrainian's archaic richness, **not** as a deficiency or oddity. Phrase: "Ukrainian kept a three-way number system long after other languages simplified to binary." Never mention Russian as a comparison baseline; if cross-linguistic comparison aids learners, use Polish (which also lost двоїна by the 15th century, unlike Ukrainian).
- **The 11–14 trap** needs a dedicated callout box — it is the single most consistent error in the textbook literature.
- **Oblique cases section** (plan §5): Karaman's framework (noun + numeral agree in same case in oblique) is the key pedagogical frame. Keep examples short: *двох книг, двом учням, двома ручками*.
- **євро is indeclinable**: When using *десять євро* as an example, flag that євро does not change form (unlike гривня/гривні/гривень). This is a real learner stumbling block in shopping contexts.
- **одні + pluralia tantum**: *одні двері, одні штани* — this is counterintuitive (singular meaning, plural form) and worth a dedicated mini-note in the один section.
- **Stress as Zone signal**: The бра́ти/брати́ stress distinction is a beautiful pedagogical hook — use it in the двоїна cultural sidebar. It shows the system is not arbitrary but historically motivated.

## Multimedia Resources
- (none encountered — discover phase will handle video sourcing)

## Resource Discovery


### Blog Articles
- [Grammar point: numeral / noun agreement in Ukrainian](https://www.ukrainianlessons.com/fmu7/) (ukrainianlessons.com)
- [Dobra Forma: Ordinal Numerals (Gender and Number in Nominative)](https://opentext.ku.edu/dobraforma/chapter/16-3/) (dobraforma)
- [At the grocery store + Genitive case](https://www.ukrainianlessons.com/episode46/) (ukrainianlessons.com)
- [Food festivals + Genitive case](https://www.ukrainianlessons.com/episode47/) (ukrainianlessons.com)
- [Syrnyky recipe + Genitive case](https://www.ukrainianlessons.com/episode49/) (ukrainianlessons.com)

### Textbook References (RAG)

**Grade 4, Сторінка 6** ():
6
ЯК ЧИТАЮТЬ КНИЖКИ?
Люди читають книжки по-різному. Одні швидко,
інші — повільно, а деякі так швидко, ніби «ковтають» 
сторінки.
Швидкість читання значною мірою залежить від того, 
що і з якою метою ми читаємо. Скажімо, підручник із 
математики та збірку казок ти, очевидно, читаєш по-
різному. Текст задачі, наприклад, треба прочитати не 
поспішаючи кілька разів, щоб зрозуміти кожне слово, 
запам’ятати дані, розібратися у змісті запитання. Без 
цього задачу не розв’яжеш. Казку ж ти читаєш зовсім


**Grade 3, Сторінка 142** ():
142
Досліди, скількома 
способами 
можна 
прочитати числовий 
вираз.
Я — дослідник
Я — дослідниця
Навчаюся читати числові вирази
70 + 25
80 – 25
Сума чисел сімдесят і двадцять  
п’ять.
Сімдесят збільшити на двадцять  
п’ять.
Перший доданок сімдесят, другий — 
двадцять п’ять.
До сімдесяти додати двадцять п’ять.
Різниця чисел вісімдесят і двадцять п’ять.
Вісімдесят зменшити на двадцять п’ять.
Зменшуване вісімдесят, від’ємник —  
двадцять п’ять.
Від вісімдесяти відняти двадцять п’ять.
Правильно утв


**Grade 5, Сторінка 103** ():
До ре­чі, ри­му­ван­ня мо­же від­бу­ва­ти­ся і в ін­ший спо­сіб: нап­рик­лад, 
пер­ший ря­док ри­му­єть­ся з тре­тім, а дру­гий — із чет­вер­тим, як у 
та­ко­му урив­ку. Розвиваємо компетентності
Теорія літератури





**Grade 6, Сторінка 241** ():
§ 51. Узгодження числівників з іменниками  
241
два зошити, двадцять чотири учні, сімдесят чо-
тири відсотки.
Але: два селянина, три громадянина (Р. в. одн.), 
оскільки ці іменники мають суфікс -ин-.
3. Числівники від п’яти до двадцяти і тридцять ви-
магають форми родового відмінка множини: п’ять 
зошитів, десять учнів, сто двадцять сім банків.
Зверніть увагу! Числівники два, три, чотири не 
сполучаємо з  іменниками ІV відміни. Для позначення 
їхньої кількості уживають збірні числівники (троє 
т


**Grade 6, Сторінка 152** ():
152
1.	Прочитайте слова й словосполучення та виконайте завдання.
один → перше місце — золота медаль
два → друге місце — срібна медаль
три → третє місце — бронзова медаль
А.	
Які числівники вказують на кількість, а які — на порядок при лічбі?
Б.	 На які питання вони відповідають? 
           Групи числівників 
за значенням 
за будовою
кількісні (скільки?): один, два-
надцять, тридцять п’ять
прості  
(один корінь)
шість,
сімнадцятий
порядкові (котрий?): перший, 
дванадцятий, тридцять п’ятий
складе


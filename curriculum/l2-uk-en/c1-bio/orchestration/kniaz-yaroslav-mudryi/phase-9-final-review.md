## Adversarial QA Review — kniaz-yaroslav-mudryi

---

## Issues Found

### CRITICAL

**Issue 1 — Activity title misattributes Monomakh's text to Yaroslav (YAML line 3)**

> `title: 'Уривок з "Повчання дітям" (1054 рік)'`

**«Повчання дітям»** (Instruction to Children) is Volodymyr Monomakh's famous text, written ~1117. Yaroslav's deathbed speech to his sons is the **«Заповіт»** (Testament), recorded in the Primary Chronicle for 1054. These are two entirely different documents from two different rulers separated by 63 years. The activity's own `id: reading-yaroslav-testament` and the task prompt ("заповіту") are correct — only the display title is wrong. This is a pedagogical trap: a student who later encounters Monomakh's *Повчання* will think it is Yaroslav's text.

---

**Issue 2 — "Aina Regina" falsely described as a Cyrillic signature (MD line 165)**

> `зберігся її власноручний підпис кирилицею *Aina Regina* — «Королева Анна» на латинських грамотах`

**«Aina Regina»** is Latin/Old French, not Cyrillic. Anna's surviving Cyrillic signature (on the Senlis charter, 1063) reads **«Ана»**. The Latin documents carry the Latinized form *Aina*. The sentence as written presents the Latin rendering as if it were the Cyrillic script, directly contradicting itself ("підпис кирилицею *Aina Regina*"). Fix: distinguish the Cyrillic form from the Latin form.

---

**Issue 3 — «Ярославль» used for the Polish city on the San (MD line 198)**

> `**Ярославль** (на річці Сян, на території сучасної Польщі)`

The city Yaroslav founded on the San River in present-day Poland is **«Ярослав»** in Ukrainian (Polish: *Jarosław*). **«Ярославль»** (with soft sign) is the Russian city on the Volga — a different city entirely. Using the Russian form here is especially ironic given the module's strong decolonization stance.

---

**Issue 4 — «Агмунда» as Anastasia's alternative name is unverifiable (MD line 169)**

> `**Анастасія Ярославна (Агмунда)**`

Hungarian historical records identify Andrew I's wife only as *Anasztázia/Anastasia*. No confirmed Norse, Latin, or Slavonic source uses «Агмунда» for Anastasia Yaroslavna. This parenthetical does not appear in standard Ukrainian or international scholarship and has all the hallmarks of an LLM confabulation. The name must be removed until sourced.

---

**Issue 5 — Typo in activity title: «Історичний детекти» (YAML line 107)**

> `title: 'Історичний детекти'`

Missing final «в». Should be «Історичний детектив».

---

### MODERATE (Style/Language — flagged partially by Green Team)

**Issue 6 — «найблакитніша кров» anachronistic idiom (MD line 55)**
The idiom «блакитна кров» derives from the Spanish *sangre azul* and entered European usage no earlier than the 15th–16th centuries. Applying it to 11th-century genealogy is anachronistic.

**Issue 7 — «соціальний контракт» anachronistic calque (MD line 65)**
Rousseau's «contrat social» is 18th-century Enlightenment philosophy. As a metaphor applied to Yaroslav's arrangement with the Novgorodians it misleads the register. «Взаємовигідна угода» is precise and era-neutral.

**Issue 8 — «колосальний» × 6 (LLM fingerprint)**
Found at: line 17 ("стрибок"), line 55 ("права"), line 102 ("прорив"), line 148 ("вплив"), line 200 ("прибутки"), line 220 ("ролі"). Replace with synonyms throughout.

**Issue 9 — «меседжі» anglicism in self-check question (MD line 241)**
C1 academic register requires «послання» not the anglicized calque «меседжі».

**Issue 10 — «Це був/була/було» × 20+ (LLM fingerprint)**
Green Team identified 20 instances; fixing the 3 most structurally identical.

---

## Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/activities/kniaz-yaroslav-mudryi.yaml
---OLD---
  title: 'Уривок з "Повчання дітям" (1054 рік)'
---NEW---
  title: 'Уривок із заповіту синам (1054 рік)'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/activities/kniaz-yaroslav-mudryi.yaml
---OLD---
  title: 'Історичний детекти'
---NEW---
  title: 'Історичний детектив'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/kniaz-yaroslav-mudryi.md
---OLD---
Вона вміла читати й писати (зберігся її власноручний підпис кирилицею *Aina Regina* — «Королева Анна» на латинських грамотах), тоді як її чоловік-король ставив хрестик замість підпису.
---NEW---
Вона вміла читати й писати (на латинських грамотах збереглася її власноручна позначка кирилицею — *«Ана»*, тоді як латиною вона підписувалась *Aina Regina* — «Королева Анна»), тоді як її чоловік-король ставив хрестик замість підпису.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/kniaz-yaroslav-mudryi.md
---OLD---
*   **Анастасія Ярославна (Агмунда)** вийшла заміж за угорського короля Андрія I.
---NEW---
*   **Анастасія Ярославна** вийшла заміж за угорського короля Андрія I.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/kniaz-yaroslav-mudryi.md
---OLD---
*   **Ярославль** (на річці Сян, на території сучасної Польщі) — для закріплення західних кордонів («Червенські міста») та контролю шляху до Кракова.
---NEW---
*   **Ярослав** (на річці Сян, на території сучасної Польщі) — для закріплення західних кордонів («Червенські міста») та контролю шляху до Кракова.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/kniaz-yaroslav-mudryi.md
---OLD---
Якщо ця гіпотеза вірна, то у жилах Ярослава текла найблакитніша кров Європи, що давало йому колосальні легітимні права на владу і робило його рівнею будь-якому монарху Заходу чи Сходу.
---NEW---
Якщо ця гіпотеза вірна, то у жилах Ярослава текла найшляхетніша кров Європи, що давало йому величезні легітимні права на владу і робило його рівнею будь-якому монарху Заходу чи Сходу.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/kniaz-yaroslav-mudryi.md
---OLD---
уклавши з ними вигідний соціальний контракт, що став прообразом майбутніх республіканських свобод Новгорода.
---NEW---
уклавши з ними взаємовигідну угоду, що стала прообразом майбутніх республіканських свобод Новгорода.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/kniaz-yaroslav-mudryi.md
---OLD---
Це була свідома, ретельно продумана ідеологічна програма, спрямована на утвердження рівності Києва з Візантією. Ярослав копіював візантійські взірці, але наповнював їх новим змістом.
---NEW---
Свідома, ретельно продумана ідеологічна програма — спрямована на утвердження рівності Києва з Візантією. Ярослав копіював візантійські взірці, але наповнював їх новим змістом.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/kniaz-yaroslav-mudryi.md
---OLD---
Це був акт відкритого сепаратизму, нечувана зухвалість.
---NEW---
Відкритий акт сепаратизму — нечувана зухвалість.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/kniaz-yaroslav-mudryi.md
---OLD---
Це була перемога Півночі (новгородців і варягів) над Півднем, яка, парадоксально, призвела до небаченого розквіту саме Півдня.
---NEW---
Перемога Півночі (новгородців і варягів) над Півднем парадоксально призвела до небаченого розквіту саме Півдня.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/kniaz-yaroslav-mudryi.md
---OLD---
Це був колосальний цивілізаційний стрибок: від племінної вольниці до феодальної монархії європейського зразка.
---NEW---
Це був безпрецедентний цивілізаційний стрибок: від племінної вольниці до феодальної монархії європейського зразка.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/kniaz-yaroslav-mudryi.md
---OLD---
Це був колосальний цивілізаційний прорив. Русь перейшла від усного звичаєвого права
---NEW---
Це був масштабний цивілізаційний прорив. Русь перейшла від усного звичаєвого права
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/kniaz-yaroslav-mudryi.md
---OLD---
її інтелектуальний вплив був колосальним: вона сформувала еліту, здатну мислити глобальними категоріями.
---NEW---
її інтелектуальний вплив був визначальним: вона сформувала еліту, здатну мислити глобальними категоріями.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/kniaz-yaroslav-mudryi.md
---OLD---
що приносило державі колосальні прибутки.
---NEW---
що приносило державі значні прибутки.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/kniaz-yaroslav-mudryi.md
---OLD---
скільки його колосальної історичної ролі у перетворенні Русі на християнську цивілізацію.
---NEW---
скільки його величезної історичної ролі у перетворенні Русі на християнську цивілізацію.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/kniaz-yaroslav-mudryi.md
---OLD---
Які ідеологічні меседжі були закладені в ці споруди в контексті суперництва з Константинополем?
---NEW---
Які ідеологічні послання були закладені в ці споруди в контексті суперництва з Константинополем?
===FIX_END===

===VERDICT===
APPROVE
===END_VERDICT===
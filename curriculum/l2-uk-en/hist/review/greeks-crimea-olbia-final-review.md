## Adversarial QA Review — greeks-crimea-olbia (hist-003)

Reading the actual file contents before making any judgments.

---

## Issues Found

### Issue 1 — Wrong Word (не існує як дієприкметник)
**Location:** Section "Боспорське царство та Тіра"
**Text:** «Золоті прикраси, знадені там, досі вважаються вершиною ювелірного мистецтва античності»
**Problem:** «Знадені» derives from «знадити» (to lure/entice) — semantically nonsensical here. This is either a typo or hallucinated form. The correct word is «знайдені» (found, from «знайти»).
**Fix:** «знайдені»

---

### Issue 2 — Case Government Error (Genitive, not Dative)
**Location:** Section "Херсонес Таврійський: Держава присяги," hora paragraph
**Text:** «адже аналогів такій збереженості немає ніде в світі»
**Problem:** «Аналог» governs Genitive («аналог чого?»). «Такій збереженості» is Dative. Must be Genitive «такої збереженості».
**Fix:** «аналогів такої збереженості»
*(Green Team identified but fix not applied)*

---

### Issue 3 — Passive Voice Weakening Agency
**Location:** Section "Читання: Ольвія — демократія в степу," founding paragraph
**Text:** «Місце було обрано ідеально: стрімкий берег»
**Problem:** Passive construction removes the colonists as agents. Active voice strengthens the historical narrative.
**Fix:** «Місце обрали ідеально: стрімкий берег»
*(Green Team identified but fix not applied)*

---

### Issue 4 — Editorial Moralizing Injection
**Location:** Section "Читання: Ольвія — демократія в степу," trade list
**Text:** «Також вивозили хутро, мед, віск, солону рибу та, на жаль, рабів.»
**Problem:** «На жаль» is a modern editorial intrusion into a factual list. Historical narrative describes trade goods; moral commentary belongs in analysis sections, not enumeration.
**Fix:** Remove «на жаль»
*(Green Team identified but fix not applied)*

---

### Issue 5 — Anachronistic Naming (Historical Precision)
**Location:** Section "Занепад античного світу"
**Text:** «Херсонес (у середні віки відомий як Херсон або Корсунь)»
**Problem:** «Херсон» is the Byzantine Greek name; «Корсунь» is the Old Ruthenian name. Lumping both under «у середні віки» without distinguishing their origins conflates two different cultural contexts and risks confusion with the modern city of Kherson (founded 1778).
**Fix:** «Херсонес (у візантійських джерелах — Херсон, у руських — Корсунь)»
*(Green Team identified but fix not applied)*

---

### Issue 6 — Factual Error in Activity Explanation (Chersonesus Wine Export)
**Location:** True/False activity, item about wine as main export
**Text:** «Головним експортом було зерно; вино навпаки імпортували або виробляли для місцевих потреб (як у Херсонесі)»
**Problem:** The explanation directly contradicts the module content. The module states explicitly: «Головною спеціалізацією Херсонеса було виноробство. Виноград вирощували в промислових масштабах, а вино **експортували** по всьому Причорномор'ю.» Telling students Chersonesus produced wine «для місцевих потреб» creates a pedagogical trap — they will have just read the opposite.
**Fix:** Rewrite explanation to correctly state grain was the dominant export across most colonies, with Chersonesus as the wine-exporting exception.

---

## Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/hist/greeks-crimea-olbia.md
---OLD---
Золоті прикраси, знадені там, досі вважаються вершиною ювелірного мистецтва античності
---NEW---
Золоті прикраси, знайдені там, досі вважаються вершиною ювелірного мистецтва античності
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/hist/greeks-crimea-olbia.md
---OLD---
адже аналогів такій збереженості немає ніде в світі
---NEW---
адже аналогів такої збереженості немає ніде в світі
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/hist/greeks-crimea-olbia.md
---OLD---
Місце було обрано ідеально: стрімкий берег гарантував надійну оборону
---NEW---
Місце обрали ідеально: стрімкий берег гарантував надійну оборону
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/hist/greeks-crimea-olbia.md
---OLD---
Також вивозили хутро, мед, віск, солону рибу та, на жаль, рабів.
---NEW---
Також вивозили хутро, мед, віск, солону рибу та рабів.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/hist/greeks-crimea-olbia.md
---OLD---
Херсонес (у середні віки відомий як Херсон або Корсунь) перетворився на головний форпост Візантії в Криму.
---NEW---
Херсонес (у візантійських джерелах — Херсон, у руських — Корсунь) перетворився на головний форпост Візантії в Криму.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/hist/activities/greeks-crimea-olbia.yaml
---OLD---
    - statement: Головним експортним товаром грецьких міст було вино.
      correct: false
      explanation: Головним експортом було зерно; вино навпаки імпортували або виробляли для місцевих потреб (як у Херсонесі), але стратегічним ресурсом для Греції був хліб.
---NEW---
    - statement: Головним експортним товаром грецьких міст було вино.
      correct: false
      explanation: Головним експортом більшості причорноморських колоній було зерно. Вино в Ольвію та Боспор імпортували з материкової Греції в амфорах. Виняток становив Херсонес, який спеціалізувався на виноробстві й справді вивозив вино по всьому Причорномор'ю, але саме хліб залишався стратегічним ресурсом для всього грецького світу.
===FIX_END===

===VERDICT===
APPROVE
===END_VERDICT===
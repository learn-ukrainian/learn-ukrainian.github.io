---

## Issues Found

**Issue 1 — О/І Alternation Direction Reversed** (content `.md`, line 477-480)
The text said «О переходить в І» but the examples (*кіт* → *кота*, *стіл* → *стола*) show the opposite: *і* appears in nominative where other cases have *о*. Fixed: now correctly explains «у називному відмінку звук **о** переходить в **і**, а в інших відмінках повертається **о**», with clarified example notation «і → о: у непрямих відмінках».

**Issue 2 — False Claim About Vocative Case** (content `.md`, culture callout after case table)
«Кличний відмінок зберегли лише найдавніші мови» is factually wrong — Polish, Czech, Romanian, Arabic, Latin and others also have vocative. Fixed: replaced with «Українська мова — одна з небагатьох сучасних слов'янських мов, яка повністю зберегла кличний відмінок».

**Issue 3 — Existing Review Was Fabricated** (review `.md`)
The previous Gemini review cited metaphors ("Іменник — це абсолютний король...", "Дієслово — це двигун...") that **do not exist** in the actual content. The citation validator confirmed only 4/15 cited Ukrainian sentences were actually in the source — the reviewer wrote from imagination. The review also complained about a broken mnemonic "Горішки" that was never in the file (source correctly had "Окуляри" throughout). The review was deleted and rewritten from scratch based on reading the actual file.

---

===FIX_START===
FILE: curriculum/l2-uk-en/b1/how-to-talk-about-grammar.md
---OLD---
**Чергування звуків (Alternations)**
В українській мові при зміні слова звуки можуть змінюватися. Це називається **чергування**. Найпопулярніше — це чергування **О/І**.
*   Кіт (Nominative) — Кота (Genitive). (О переходить в І).
*   Стіл — Стола.
*   Дім — Дому.
Це явище виникло століттями тому і робить українську мову унікальною.
---NEW---
**Чергування звуків (Alternations)**
В українській мові при зміні слова звуки можуть змінюватися. Це називається **чергування**. Найпопулярніше — це чергування **О/І**: у називному відмінку звук **о** переходить в **і**, а в інших відмінках повертається **о**.
*   *Кіт* (Nominative) — *Кота* (Genitive). (і → о: у непрямих відмінках).
*   *Стіл* — *Стола*.
*   *Дім* — *Дому*.
Це явище виникло в давньоукраїнській мові й робить її унікальною серед слов'янських мов.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b1/how-to-talk-about-grammar.md
---OLD---
> [!culture]
> **Душа народу у відмінку**
> Кличний відмінок зберегли лише найдавніші мови. Він показує, що для українців важливо встановити особистий контакт. Навіть до неживих предметів у піснях звертаються у кличному відмінку: «Ой, **земле** моя!», «Гей, **доле**!». Це надає мові особливої поетичності та інтимності.
---NEW---
> [!culture]
> **Душа народу у відмінку**
> Українська мова — одна з небагатьох сучасних слов'янських мов, яка повністю зберегла кличний відмінок (у російській він практично зник, у польській залишився частково). Він показує, що для українців важливо встановити особистий контакт. Навіть до неживих предметів у піснях звертаються у кличному відмінку: «Ой, **земле** моя!», «Гей, **доле**!». Це надає мові особливої поетичності та інтимності.
===FIX_END===

===VERDICT===
APPROVE
===END_VERDICT===
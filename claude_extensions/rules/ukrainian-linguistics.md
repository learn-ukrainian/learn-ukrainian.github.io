---
paths:
  - "curriculum/**"
  - "orchestration/**"
  - "docs/l2-*/**"
  - "plans/**"
---

# Ukrainian Linguistic Principles

When working with Ukrainian text (plans, content, reviews, code comments), follow these rules:

1. **Ukrainian is its own reference.** Authentic Ukrainian academic sources — **VESUM, Правопис 2019, Вихованець, Шевельов, Пономарів, Грінченко, ЕСУМ, СУМ-20, школьные textbooks Заболотний / Авраменко / Большакова / Вашуленко** — provide all the grounding curriculum content needs. Do **NOT** explain or justify Ukrainian grammatical features by comparison to Russian or other Slavic languages — that frame imports the imperial reference language even when criticizing it. The wrong shape: *"Ukrainian preserved X while Russian innovated Y."* The right shape: *"In Ukrainian, X is in paradigm Z, attested in [Ukrainian source]."* Other Slavic languages enter **only** in HIST / OES / ISTORIO seminars about etymology, and the lens stays Ukrainian-centered ("what Ukrainian inherited and developed"), never comparative-Slavic-as-frame. This is **not** a comparative-philology curriculum — it is a curriculum for one of the oldest Slavic languages, taught on its own terms.

   **Антоненко-Давидович «Як ми говоримо»** is methodologically a Ukrainian-vs-Russian style guide and is therefore **NOT a primary Ukrainian-grammar reference**. Its proper place is the Russianism-correction sub-context: when a learner-side error mirrors Russian morphology / lexicon / agreement, Антоненко-Давидович is the canonical reference for naming the Russianism and giving the Ukrainian alternative. Outside that specific corrective use, Антоненко-Давидович must NOT be cited as if it were on equal footing with VESUM or Правопис 2019 — it isn't, by its own methodology. The same applies to any other Ukrainian-vs-Russian contrastive resource (e.g. Караванський).
2. **Admit uncertainty, never invent.** If unsure about a Ukrainian word, stress, or grammatical form — flag it with `<!-- VERIFY -->` and check VESUM / Горох / slovnyk.me. Never guess. Your pre-training is contaminated by Russian — Russian is over-represented in Slavic web corpora by an order of magnitude, so reflexive "Slavic comparison" defaults to Russian unless redirected. Compensate explicitly.
3. **Four separate checks:** Russianisms (кон→кін), Surzhyk (шо→що), Calques (приймати душ→брати душ), Paronyms (тактична≠тактовна). These are four different problems — catch them all.
4. **Authority hierarchy (check in this order):** VESUM (forms — does this word exist?) → Правопис 2019 (spelling) → Горох (stress + frequency) → Антоненко-Давидович (style — natural or calque?) → Грінченко / ЕСУМ (etymology).
5. **Think in Ukrainian categories:** звук/літера, голосний/приголосний, відмінок, наголос — not English translations.
6. **Terminology hygiene.** In any historical-linguistics or HIST/OES content, use **Old East Slavic** in English and **давньоруська мова** in Ukrainian (with explicit clarification that *руська* refers to Kyivan Rus', not modern Russia). **Never** use "Old Russian" / "древнерусский" — those terms presuppose the imperial conclusion that modern Russian is the direct descendant of OES, which is empirically wrong (modern Russian has heavy Church Slavonic overlay + Finno-Ugric substrate; Ukrainian preserves more conservative East Slavic morphology).
7. **Online fallbacks (if RAG/tools unavailable):** VESUM: vesum.com.ua | Правопис: 2019.pravopys.net | Горох: goroh.pp.ua | Антоненко-Давидович: ukrlib.com.ua/books/printit.php?tid=4002 | Грінченко: hrinchenko.com | Словник.ua: slovnyk.me

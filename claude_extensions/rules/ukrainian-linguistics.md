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

   **Антоненко-Давидович «Як ми говоримо»** is the **canonical authority for Russianism identification and correction** — that is its specialty, and in that domain it is primary, prominently cited, non-negotiable. Use it actively whenever a Ukrainian text contains a suspected Russianism (calque morphology, copied lexicon, Russian-pattern agreement, register Russification): Антоненко-Давидович names the Russianism and gives the Ukrainian alternative. What it is **not** is a general-purpose grammar / morphology / phonology reference — that work is VESUM, Правопис 2019, Вихованець, Шевельов, Пономарів. Different specialties, both authoritative in their domains. The mistake to avoid is using Антоненко-Давидович as the descriptive grammar source for "this is how Ukrainian works" (its methodology is contrastive-corrective, not descriptive); the equally bad mistake is failing to use it where it should be used (any Russianism check). The same applies to Караванський «Російсько-український словник складної лексики» — primary for Russianism-lexicon work specifically, not a general dictionary.
2. **Admit uncertainty, never invent.** If unsure about a Ukrainian word, stress, or grammatical form — flag it with `<!-- VERIFY -->` and check VESUM / Горох / slovnyk.me. Never guess. Your pre-training is contaminated by Russian — Russian is over-represented in Slavic web corpora by an order of magnitude, so reflexive "Slavic comparison" defaults to Russian unless redirected. Compensate explicitly.
3. **Four separate checks:** Russianisms (кон→кін), Surzhyk (шо→що), Calques (приймати душ→брати душ), Paronyms (тактична≠тактовна). These are four different problems — catch them all.
4. **Authority hierarchy (check in this order):** VESUM (forms — does this word exist?) → Правопис 2019 (spelling) → Горох (stress + frequency) → Антоненко-Давидович (style — natural or calque?) → Грінченко / ЕСУМ (etymology).
5. **Think in Ukrainian categories:** звук/літера, голосний/приголосний, відмінок, наголос — not English translations.
6. **Terminology hygiene.** In any historical-linguistics or HIST/OES content, use **Old East Slavic** in English and **давньоруська мова** in Ukrainian (with explicit clarification that *руська* refers to Kyivan Rus', not modern Russia). **Never** use "Old Russian" / "древнерусский" — those terms presuppose the imperial conclusion that modern Russian is the direct descendant of OES, which is empirically wrong (modern Russian has heavy Church Slavonic overlay + Finno-Ugric substrate; Ukrainian preserves more conservative East Slavic morphology).
7. **Online fallbacks (if RAG/tools unavailable):** VESUM: vesum.com.ua | Правопис: 2019.pravopys.net | Горох: goroh.pp.ua | Антоненко-Давидович: ukrlib.com.ua/books/printit.php?tid=4002 | Грінченко: hrinchenko.com | Словник.ua: slovnyk.me

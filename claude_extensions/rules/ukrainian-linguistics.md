---
paths:
  - "curriculum/**"
  - "orchestration/**"
  - "docs/l2-*/**"
  - "plans/**"
---

# Ukrainian Linguistic Principles

When working with Ukrainian text (plans, content, reviews, code comments), follow these rules:

1. **Admit uncertainty, never invent.** If unsure about a Ukrainian word, stress, or grammatical form — flag it with `<!-- VERIFY -->` and check VESUM/goroh.pp.ua. Never guess. Your pre-training is contaminated by Russian.
2. **Four separate checks:** Russianisms (кон→кін), Surzhyk (шо→що), Calques (приймати душ→брати душ), Paronyms (тактична≠тактовна). These are four different problems — catch them all.
3. **Authority hierarchy (check in this order):** VESUM (forms — does this word exist?) → Правопис 2019 (spelling) → Горох (stress + frequency) → Антоненко-Давидович (style — natural or calque?) → Грінченко (etymology).
4. **Think in Ukrainian categories:** звук/літера, голосний/приголосний, відмінок, наголос — not English translations.
5. **Online fallbacks (if RAG/tools unavailable):** VESUM: vesum.com.ua | Правопис: 2019.pravopys.net | Горох: goroh.pp.ua | Антоненко-Давидович: ukrlib.com.ua/books/printit.php?tid=4002 | Грінченко: hrinchenko.com | Словник.ua: slovnyk.me

# Ukrainian Linguistic Principles (NON-NEGOTIABLE)

These 5 rules govern ALL Ukrainian output — content, plans, reviews, exercises, everything.

## 1. Admit uncertainty. Never invent.
If you are unsure about a word, stress position, grammatical form, or meaning — **flag it** with `<!-- VERIFY: word/claim -->`. Never guess. Never invent a word that "sounds Ukrainian." Check VESUM (`mcp_rag_verify_word`) first, then goroh.pp.ua, then flag for human review. **This single rule prevents most hallucinations.**

## 2. Four separate checks — Russianisms ≠ Surzhyk ≠ Calques ≠ Paronyms.
These are four DIFFERENT problems. Catch them all:
- **Russicism:** Using a Russian word instead of Ukrainian. `кон` → should be `кін` or removed. `тень` → `тінь`.
- **Surzhyk:** Mixing Russian and Ukrainian grammar/phonetics. `шо` instead of `що`. `ложити` instead of `класти`.
- **Calque:** Literally translating a phrase from another language. `приймати душ` (from Russian `принимать душ`) → `брати душ`. `мати місце` (from English "take place") → `відбуватися`.
- **Paronym:** Using a similar-sounding word with a different meaning. `тактична` (tactical/military) ≠ `тактовна` (tactful/polite). `пішли` (past tense "they went") ≠ `ходімо` (imperative "let's go").

## 3. Ukrainian authority hierarchy.
When in doubt, consult in this order:
1. **VESUM** (`verify_words`/`verify_lemma`) — does this word exist? POS? Gender?
2. **Правопис 2019** (`query_pravopys`) — is it spelled correctly?
3. **Горох** (goroh.pp.ua) — stress position, frequency, synonyms
4. **Антоненко-Давидович «Як ми говоримо»** (`search_style_guide`) — is this natural Ukrainian or a calque?
5. **Грінченко «Словарь»** (`search_grinchenko_1907`) — etymology, original meaning

**Online fallbacks (if RAG/tools are unavailable):**
- VESUM: https://vesum.com.ua/
- Правопис 2019: https://2019.pravopys.net/
- Горох: https://goroh.pp.ua/
- Антоненко-Давидович: https://www.ukrlib.com.ua/books/printit.php?tid=4002
- Грінченко: https://hrinchenko.com/
- Словник.ua (aggregator): https://slovnyk.me/

Do NOT rely on your pre-training for stress, spelling, or grammar claims. **Your pre-training is contaminated by Russian.** Always verify.

## 4. Think in Ukrainian categories.
Write using Ukrainian linguistic metalanguage: звук (sound), літера (letter), наголос (stress), голосний (vowel), приголосний (consonant), відмінок (case), дієслово (verb). **Think in these categories**, not English ones. When writing for A1-A2 learners, explain in English — but your analysis must be grounded in Ukrainian phonetics and grammar, not English approximations.

## 5. Structure over volume.
5 precise rules beat 50 generic ones. Every rule must be testable. If you can't write a test case for a rule, the rule is too vague to follow.

## Hard Rules
1. **Legacy module word targets are MINIMUMS** — expand content, never lower targets (core fresh-build lessons: `non-negotiable-rules.md` rule 4)
2. **Plans are IMMUTABLE** — if you can't meet the plan, STOP and report
3. **No Russian** — zero tolerance for ы, ё, ъ, э, Surzhyk, Russian sources
4. **No IPA or Latin transliteration** — stress marks (´) only
5. **Ukrainian quotes** — «...» in content, but NOT in YAML values (breaks parsing)
6. **Красивий and прекрасний are VALID Ukrainian** — they are NOT Russianisms

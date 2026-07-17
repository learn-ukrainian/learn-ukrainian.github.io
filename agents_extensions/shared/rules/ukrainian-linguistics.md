---
paths:
  - "curriculum/**"
  - "orchestration/**"
  - "docs/l2-*/**"
  - "plans/**"
---

# Ukrainian Linguistic Principles

When working with Ukrainian text (plans, content, reviews, code comments), follow these rules:

1. **Ukrainian is its own reference.** Authentic Ukrainian academic sources — **VESUM, Правопис 2019, Вихованець, Шевельов, Пономарів, Грінченко, ЕСУМ, СУМ-20, school textbooks Заболотний / Авраменко / Большакова / Вашуленко** — provide all the grounding curriculum content needs. Do **NOT** explain or justify Ukrainian grammatical features by comparison to Russian or other Slavic languages — that frame imports the imperial reference language even when criticizing it. The wrong shape: *"Ukrainian preserved X while Russian innovated Y."* The right shape: *"In Ukrainian, X is in paradigm Z, attested in [Ukrainian source]."* Other Slavic languages enter **only** in HIST / OES / ISTORIO seminars about etymology, and the lens stays Ukrainian-centered ("what Ukrainian inherited and developed"), never comparative-Slavic-as-frame. This is **not** a comparative-philology curriculum — it is a curriculum for one of the oldest Slavic languages, taught on its own terms.

   **Антоненко-Давидович «Як ми говоримо»** is the **canonical authority for Russianism identification and correction** — that is its specialty, and in that domain it is primary, prominently cited, non-negotiable. Use it actively whenever a Ukrainian text contains a suspected Russianism (calque morphology, copied lexicon, Russian-pattern agreement, register Russification): Антоненко-Давидович names the Russianism and gives the Ukrainian alternative. What it is **not** is a general-purpose grammar / morphology / phonology reference — that work is VESUM, Правопис 2019, Вихованець, Шевельов, Пономарів. Different specialties, both authoritative in their domains. The mistake to avoid is using Антоненко-Давидович as the descriptive grammar source for "this is how Ukrainian works" (its methodology is contrastive-corrective, not descriptive); the equally bad mistake is failing to use it where it should be used (any Russianism check). The same applies to Караванський «Російсько-український словник складної лексики» — primary for Russianism-lexicon work specifically, not a general dictionary.
2. **Admit uncertainty, never invent.** If unsure about a Ukrainian word, stress, or grammatical form — flag it with `<!-- VERIFY -->` and check VESUM / Горох / slovnyk.me. Never guess. Your pre-training is contaminated by Russian — Russian is over-represented in Slavic web corpora by an order of magnitude, so reflexive "Slavic comparison" defaults to Russian unless redirected. Compensate explicitly.
3. **Four separate checks:** Russianisms (кон→кін), Surzhyk (шо→що), Calques (приймати душ→брати душ), Paronyms (тактична≠тактовна). These are four different problems — catch them all.
4. **Authority hierarchy — first ask what KIND of question you have.** There is no single chain. Ukrainian's authorities are specialists, and stacking them in one line implies a general ranking that does not exist: VESUM has nothing to say about meaning, СУМ-20 has nothing to say about whether a form is a calque. Pick the row that matches the question, then **reach for the tool before the memory** — a tool answer is evidence, a remembered answer is a guess (§2). MCP tools are primary; the URLs in §7 are the fallback for when the `sources` server is unreachable, not a first resort.

   **Quick chain (humans, mnemonic only):** VESUM → Правопис 2019 → Горох → Антоненко-Давидович → Грінченко / ЕСУМ. That is a rough intuition for the shape of the evidence, **not** a procedure — for any actual question, use the facet table below.

   | Question you have | Primary (MCP tool) | Then | Web fallback (§7) |
   | --- | --- | --- | --- |
   | **Forms / existence / morphology** — does this word exist? what are its tags? | `verify_word`, `verify_words` (VESUM: 415K lemmas, ~6M forms; **empty result = the form does not exist**) | `query_ulif` with `sections=["paradigm"]` for the full declension / conjugation table | vesum.com.ua |
   | **Spelling** | `query_pravopys` (Правопис 2019) | — | 2019.pravopys.net |
   | **Stress (наголос)** | `query_sum20` — headwords carry the accent (`НОВИ́Й, а́, е́`) | `query_ulif` paradigm | Горох (goroh.pp.ua); a print орфоепічний словник / словник наголосів |
   | **Meaning** | `query_sum20` (СУМ-20 — the modern, post-Soviet baseline) | `search_slovnyk_me` / `query_slovnyk_me`; `search_grinchenko_1907` as the **historical witness** (pre-Soviet attestation) | slovnyk.me; hrinchenko.com |
   | **Frequency / usage / CEFR level** | `query_grac` (GRAC, 2bn tokens; `mode=frequency\|concordance\|collocations`) + `query_cefr_level` (PULS, 5.9K words, A1–C1) | — | Горох (goroh.pp.ua) |
   | **Russianism / calque / style** | **Антоненко-Давидович — query BOTH surfaces:** `search_style_guide` (342 structured headwords) **and** `search_text` with `source_file='antonenko-davydovych-yak-my-hovorymo'` (169 prose chunks) | `query_r2u` (Караванський, r2u.org.ua); then `check_russian_shadow` **under the override below**; then `search_ua_gec_errors` (UA-GEC human-annotated error→correction pairs) | ukrlib.com.ua/books/printit.php?tid=4002 |
   | **Paronyms** | **No MCP tool exists** — do not invent one. Nearest tool evidence is a sense contrast via `query_sum20` / `search_definitions` on both members of the pair | Гринчишин / Сербенська, «Словник паронімів» (print) | — |
   | **Etymology** | `search_esum` (ЕСУМ, vols 1–6, А–Я) | `search_grinchenko_1907` — **attestation, not origin**; it witnesses pre-Soviet usage, it does not explain where a word came from | Горох (goroh.pp.ua) |
   | **Is it heritage or Russianism?** | `search_heritage` (merges Грінченко + ЕСУМ + slovnyk.me + Антоненко evidence) | — | — |

   **Procedure — run every check in this order, no steps skipped:**

   1. **Map the question to its facet row** above. Two facets, two rows — run both.
   2. **Call that row's Primary MCP tool first.** Never memory, never web-first: a remembered answer is a guess (§2).
   3. **A miss is not evidence of absence.** On an empty or thin result, escalate along the row as documented: the **Then** tool, then a full-text sweep of the relevant source (`search_text` / `search_sources`). Escalate unless the row states the miss *is* the verdict — VESUM's empty result is the one such case, and only for form existence.
   4. **Only after row escalation is exhausted:** the §7 fallback URL, and the claim ships flagged `<!-- VERIFY -->`. Silence from the tools is never authoritative — not for existence, not for absence.

   Four things the table encodes that the old single chain got wrong — read them before using it:

   - **VESUM does not carry stress.** `verify_word` returns lemma, POS and morphological tags; there is no наголос in the result. Asking VESUM for stress and getting silence is not evidence of anything. Stress evidence is СУМ-20's accented headword.
   - **СУМ-20 covers volumes 1–16 (А–Р) only** — vols 17–20 (С–Я) are unpublished. For a С–Я headword `query_sum20` legitimately returns nothing, and that is a coverage gap, **not** a verdict on the word. Fall through to `search_slovnyk_me`.
   - **`search_definitions` is СУМ-11, not СУМ-20** — Soviet-era, ~5.6% of entries ideologically framed (#1659). Check `sovietization_risk` on every row; when it is `> 0`, prefer `query_sum20` / Грінченко and never reproduce the definition verbatim.
   - **The Антоненко structured index alone is a known failure mode.** A phrase absent from the 342 keyed entries may still be condemned in the prose body; retrieving only the structured index collapsed review F1 once already (the H1 prompt bug). Query both surfaces, every time.

   **Heritage override (`check_russian_shadow`).** A shadow hit is a *suspicion*, never a verdict, and authentic Ukrainian is what it most often flags. The production rule (`scripts/audit/hramatka_qg_rules.py`) fires russianism only on **VESUM-absent ∧ russian-shadow ∧ ¬heritage** — so heritage evidence *beats* shadow suspicion outright, VESUM attestation short-circuits ahead of it, and proper nouns and borrowings are excluded. Where VESUM is unavailable the rule declines to accuse at all. Apply the same order by hand: `search_heritage` **before** rejecting any unfamiliar Ukrainian-looking word. The load-bearing case is `кобета` / `кобіта` — regional Lviv Ukrainian with СУМ-20 attestation, not a Russianism, and a bare shadow check gets it backwards.
5. **Think in Ukrainian categories:** звук/літера, голосний/приголосний, відмінок, наголос — not English translations.
6. **Terminology hygiene.** In any historical-linguistics or HIST/OES content, use **Old East Slavic** in English and **давньоруська мова** in Ukrainian (with explicit clarification that *руська* refers to Kyivan Rus', not modern Russia). **Never** use "Old Russian" / "древнерусский" — those terms presuppose the imperial conclusion that modern Russian is the direct descendant of OES, which is empirically wrong (modern Russian has heavy Church Slavonic overlay + Finno-Ugric substrate; Ukrainian preserves more conservative East Slavic morphology).
7. **Online fallbacks (if RAG/tools unavailable):** VESUM: vesum.com.ua | Правопис: 2019.pravopys.net | Горох: goroh.pp.ua | Антоненко-Давидович: ukrlib.com.ua/books/printit.php?tid=4002 | Грінченко: hrinchenko.com | Словник.ua: slovnyk.me

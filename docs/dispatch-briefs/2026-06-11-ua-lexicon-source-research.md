# RESEARCH (no code) — find authentic Ukrainian lexicographic sources for the Word Atlas

We are sourcing dictionaries to populate our Word Atlas (Лексикон). **HARD CONSTRAINT — decolonization:**
**authentic Ukrainian sources ONLY.** NO Russian dictionaries. NO English-auto-translated data — our
current synonym source (`ukrajinet` WordNet, auto-translated from English WordNet) returns antonyms
(`чудово`→`жахливо`) and wrong-sense pollution (`одягатися`→`бити`), so it is UNUSABLE. The user has
seen, in Ukrainian language & literature workbooks, that comprehensive Ukrainian dictionaries of every
kind exist — find them.

## Most-needed (in priority order)
1. A real **Ukrainian SYNONYM dictionary** (compiled by Ukrainian lexicographers, not translated).
2. **Antonym** dictionary.
3. **Phraseology / idioms** (we have Фразеологічний but want to verify best source).
4. Anything else clean: thesaurus, word-formation (словотвір), paronyms, dialect.

## For EACH source, report
title · author/editor · year · publisher · type · **where to obtain** (open dataset / digitized site /
scrapeable / API / dump / GitHub) · **LICENSE** · data format · est. entry count.

## Seed list to VERIFY (obtainability + license) and EXPAND (find more + the data behind them)
- Synonyms: Караванський «Практичний словник синонімів української мови»; «Словник синонімів української
  мови» (А.А. Бурячок та ін., 2 т., Інститут української мови НАН України, 1999–2000); Деркач «Короткий
  словник синонімів української мови».
- Antonyms: Полюга «Словник антонімів української мови».
- Idioms: СФУМ «Словник фразеологізмів української мови» (Білоноженко та ін.).
- Online portals that may expose structured data or be scrapeable: `goroh.pp.ua`, `slovnyk.ua`,
  `sum.in.ua`, `r2u.org.ua` (e2u/r2u — but exclude the Russian side), `slovotvir.org.ua`,
  `lcorp.ulif.org.ua` (ВЕСУМ/ULIF), `slovnyk.me`. Plus any **GitHub repos** of open Ukrainian dictionary
  data, and academic/NAN releases.

## Output
A ranked table: source → obtainability → license → fit (synonym/antonym/idiom). **Then name the single
best path to a clean Ukrainian SYNONYM dataset** (the #1 blocker), with the concrete next step to obtain it.
Cite URLs. This is analysis only — no code, no commits.

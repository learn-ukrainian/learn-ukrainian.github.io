# Dispatch brief — Word Atlas synonyms done RIGHT (supersedes #2895) + salvage cleanup

PR #2895's WordNet synonyms were **polluted** and must NOT ship: `кава→Java/chocolate/умбра`,
`мама→хризантема/ma`, `стілець→electric chair`, `дім→home plate`, `чудово→жахливо (antonym)`.
Re-implement synonyms with **sense-correct filtering**, and KEEP #2895's good gloss/entity cleanup.

## Files
- Edit: `scripts/lexicon/enrich_manifest.py`
- Regenerate: `starlight/src/data/lexicon-manifest.json` (use its documented regen command; do NOT hand-edit JSON)
- The 63 lexicon lemmas are the test set.

## Hard quality gate (the PR FAILS if any of these appear)
After regeneration, these MUST hold (quote raw grep/inspection in the PR):
- `кава` synonyms contain NO `Java`, `Шоколад`, `умбра`, color names, or any Latin-letter token.
- `мама` contains NO `хризантема`, Latin binomials, or `ma`.
- `стілець` contains NO `electric chair`/`стілець смерті`/`hot seat`.
- `чудово` contains NO antonyms (`жахливо`).
- NO synonym anywhere contains Latin letters `[A-Za-z]`.
- Every emitted synonym is a real everyday Ukrainian word of the lemma's **A1 sense**.

## Approach (implementer chooses, but must pass the gate)
1. **Evaluate cleaner sources first**: try `mcp__sources__search_synonyms` / R2U / curated Вікісловник
   before raw `ukrajinet`. If a curated source gives clean results, prefer it.
2. If using `ukrajinet` (WordNet, 122K): gather candidates from synsets containing the lemma
   (whole-token), then filter HARD:
   - drop any token with Latin letters; drop multi-word phrases > 2 words; drop the lemma + duplicates;
   - **sense-disambiguate**: keep a candidate only if its synset gloss (`text`) is semantically
     consistent with the lemma's own `Значення` definition. A per-lemma LLM filter is acceptable
     (pass lemma + its gloss + candidates → keep only true same-sense everyday synonyms). Whatever the
     method, the gate above is the contract.
   - cap at 6; **NEVER fabricate** — only emit words that were real candidates.
3. **Antonyms**: no clean source exists → omit entirely (state so in the PR).

## Salvage from #2895 (keep these — they were correct)
- `clean_gloss`: strip the pedagogical `" — chunk"` annotation from glosses (greetings).
- `clean_html_entities`: unescape double-escaped entities (`&amp;nbsp;`→space, `&lt;`→`<`).
- Verify `grep -c chunk lexicon-manifest.json` = 0 and `grep -c '&amp;\|&lt;\|&gt;'` = 0.

## #M-4 verification (final report = command + cwd + raw output)
- Before/after synonym lists for `кава, мама, стілець, дім, чудово` (raw) — proving the gate holds.
- 3-lemma cross-check: each emitted synonym appears in its source row (sqlite/MCP output raw).
- chunk=0, entities=0 greps raw.
- `npm run build:full --prefix starlight` final line raw; `npm test --prefix starlight` + any `tests/test_lexicon*` pytest final line raw.

## Numbered steps
1. Confirm `pwd` is the dispatch worktree.
2. Evaluate sources; implement sense-correct synonyms + keep the gloss/entity cleanup.
3. Regenerate the manifest.
4. Run the full quality gate + #M-4 verification.
5. `.venv/bin/ruff check scripts/lexicon/enrich_manifest.py`.
6. Commit (conventional + `X-Agent` trailer): `feat(lexicon): sense-correct synonyms + gloss/entity cleanup [#2882, supersedes #2895]`.
7. `git push -u origin <branch>`; `gh pr create` with the raw gate evidence. **DO NOT merge** — it goes to review first.

# MCP / local semantic spot-checks

The `mcp__sources__search_esum` tool was lazy-loaded during the bake-off. It advertises
PoC scope for volume 1 only, so direct MCP ESUM checks were used on volume 1 samples and
the local `data/processed/esum_vol{N}.jsonl` rows were used for volumes 2-6.

## `search_esum("Аглая", volume=1)`

- Result: lemma `аглая`, volume 1, page 45.
- Key content: `Аглая, Аглаіда`; borrowings from Greek; cites Russian, Belarusian,
  Bulgarian, Old Church Slavonic, Greek forms and sources.
- Matches sample: `samples/vol1/p0045/evidence.md`.

## `search_esum("вас", volume=1)`

- Result 1: lemma `вас`, volume 1, page 335.
- Key content: genitive plural `вас`; compares Russian, Belarusian, Bulgarian,
  Old Russian, Polish, Upper/Lower Sorbian, Czech, Slovak, Serbo-Croatian,
  Slovene, Old Church Slavonic, Proto-Slavic, Prussian, Sanskrit, Avestan, Latin.
- Matches sample: `samples/vol1/p0335/evidence.md`.

## `search_heritage("смух")`

- Result: `смух` has Grinchenko and ESUM evidence; ESUM says `смух` / `смушок`
  means young lamb/sheepskin/fur and is probably borrowed through Polish, with
  Polish `smuch` / `smuszek` traced to German `Schmasche`.
- Semantic guard: this corroborates that the quarantined Gemini-2.5 page
  `vol5_p0469.md` inventing Czech `smutek` and Sanskrit `smarati` as cognates
  for `сму́шок` is not supported by the deployed ESUM-backed witness.

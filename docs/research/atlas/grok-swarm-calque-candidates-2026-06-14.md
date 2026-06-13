# grok-swarm §6 calque candidates — Claude triage (2026-06-14)

Source: grok 4-agent purist swarm (verify-shaped, Антоненко + UA-GEC F/Calque, heritage-gated).
Raw: `grok-swarm-calque-candidates-2026-06-14.json` (20 entries).

> **✅ INTEGRATED (2026-06-14, Claude-curated):** the curation below was
> heritage-/UA-GEC-/VESUM-verified live and landed in
> `scripts/lexicon/calque_corrections.py`: ✅ phrasals → `PHRASAL_CALQUES`;
> ⚠️ polysemes → new `SENSE_RESTRICTED_CALQUES` bucket. **Two ✅ items were
> demoted on verification:** `дійсно` (authentic adverb — Antonenko p053 "є в
> українській мові") and `відносно` (authentic "порівняно"; UA-GEC offers it
> AS a correction) were DROPPED, not flagged. ❓ suspects all dropped. Test:
> `tests/test_calque_corrections.py` pins the drops against re-introduction.

The swarm did well (canonical purist corrections, not hallucinated). But 6 entries are
**polysemes — authentic Ukrainian words that are calques ONLY in one sense** — and would
over-flag correct usage if added blanket (the блискучий-class lesson applied to polysemy).
Each of those needs a sense-qualifier in the dataset (or a sense-scoped note the §6 renderer respects).

## ✅ SOLID — integrate as-is (canonical, unambiguous)
- `дійсно → справді`
- `в дійсності → насправді`
- `відносно → стосовно / щодо`
- `по відношенню → стосовно / щодо`
- `точка зору → погляд`
- `з моєї точки зору → на мою думку`
- `Ні в якому разі → аж ніяк`
- `прийшла в голову → спала на думку` ; `в голову прийшли → спали на гадку`

## ⚠️ NEEDS SENSE-QUALIFIER — authentic word, calque only in a specific sense (DO NOT blanket-flag)
- `вірний` — authentic = loyal/faithful (вірний друг ✓); calque only for "correct" → правильний/слушний
- `дійсний` — authentic = valid/current (дійсний член ✓); calque only for "real" → справжній
- `відношення` — authentic in math/technical (✓); calque for "relationship/attitude" → стосунок/ставлення
- `рахувати` — authentic = to count (✓); calque for "consider" → вважати
- `виглядає` — authentic = looks/appears (✓); calque only for "seems" → здається
- `По-моєму` — **questionable flag**: по-моєму is acceptable Ukrainian ("in my opinion"); verify before adding

## ❓ SUSPECT — verify or drop (likely UA-GEC context artifacts)
- `ніяк → здається` — DROP unless verified; ніяк = "in no way", the →здається mapping is a context artifact
- `з приводу → стосовно` — debatable; «з приводу» is used in standard Ukrainian — verify the calque claim
- `вроде → здається`, `кажись → здається` — these are Russian/Surzhyk insertions (fine to flag as Surzhyk, type=surzhyk not calque)

## Integration plan (next session)
1. Heritage-gate each ⚠️/❓ form via `mcp__sources__search_heritage` + `check_russian_shadow` (confirm the curation above).
2. Add the ✅ set + sense-qualified ⚠️ set to `calque_corrections.py` (new `SENSE_RESTRICTED_CALQUES` bucket for polysemes, so the §6 renderer warns only in the calque sense).
3. Drop/verify the ❓ set. PR referencing #3098.

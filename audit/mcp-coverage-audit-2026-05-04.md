# MCP Source-Table Coverage Audit (#1660)

**Date:** 2026-05-04
**Scope:** Verify each MCP `sources` tool's actual indexed count against
canonical source size, document systematic exclusions, and update tool
descriptions so reviewer prompts can interpret empty results correctly.

## Method

Counts pulled directly from `data/sources.db` via:

```sql
SELECT 'sum11', COUNT(*) FROM sum11 UNION ALL
SELECT 'grinchenko', COUNT(*) FROM grinchenko UNION ALL
SELECT 'frazeolohichnyi', COUNT(*) FROM frazeolohichnyi UNION ALL
SELECT 'ukrajinet', COUNT(*) FROM ukrajinet UNION ALL
SELECT 'balla_en_uk', COUNT(*) FROM balla_en_uk UNION ALL
SELECT 'style_guide', COUNT(*) FROM style_guide UNION ALL
SELECT 'puls_cefr', COUNT(*) FROM puls_cefr;
```

Proper-noun exclusion probes:

```sql
SELECT word FROM grinchenko WHERE word IN ('Київ','Львів','Україна','Шевченко','Дніпро','Сибір');
SELECT word FROM sum11 WHERE word IN ('Київ','Львів','Україна','Шевченко','Дніпро','Сибір');
```

## Coverage table

| Tool | Source | Indexed | Canonical | Coverage | Notes |
|---|---|---|---|---|---|
| `search_style_guide` | Антоненко-Давидович «Як ми говоримо» | 279 | 600+ | ~46% | INCOMPLETE — issue #1663 tracks full ingest. Re-dispatch needed (segmenter broken on prior run). |
| `search_definitions` | СУМ-11 (1970–1980) | 127,069 | ~127K | ~100% | Excludes proper nouns (toponyms, person names). 5.6% Sovietized (#1659 flagged). |
| `search_grinchenko_1907` | Грінченко (1907) | 67,275 | ~67K | ~100% | Excludes proper nouns. NOT etymology — lexicographic. |
| `search_esum` | ЕСУМ vol 1 (А–Г) | 1,923 | 6 vols | ~17% by volume, А–Г scope | PoC only. Vols 2-6 follow up. |
| `search_idioms` | Фразеологічний | 24,683 | ~25K | ~99% | Single-source — cross-validate via `search_literary`. |
| `search_synonyms` | Ukrajinet WordNet | 122,441 | 122K | 100% by count | **Quality caveat:** auto-MT from English WordNet, not curated. Audit pending #1657 Tier 3. |
| `translate_en_uk` | Балла EN→UK | 78,704 | ~79K | ~100% | One-way only. UK→EN not built. |
| `query_cefr_level` | PULS (puls.peremova.org) | 5,939 | A1–C1 | Bounded — C2 not covered | Vocabulary list, not pedagogy. |

## Systematic exclusion: proper nouns

Probe results for `('Київ','Львів','Україна','Шевченко','Дніпро','Сибір')`:

- **Грінченко:** 0 found (toponyms + person names absent).
- **СУМ-11:** 1 found (`Україна` only — country name as common-noun-like
  entry; 5/6 absent).

**Implication for reviewer prompts:** when a query for a proper noun
returns empty in either dictionary, this is the expected result, not
evidence the word is non-Ukrainian. Tool descriptions now state this
explicitly.

## Sovietization breakdown (СУМ-11)

From `audit/sum11_sovietization_scan_2026-05-04.md` (#1659):

- **127,069 entries scanned**
- **7,152 flagged (5.63%)** — 755 high-risk (`sovietization_risk=2`),
  6,397 low-risk (`sovietization_risk=1`)
- Top high-risk lemmas: `прапор` (9 keywords), `революційний` (9),
  `партійний` (8), `школа` (7), `центр` (7).

Until СУМ-20 ingestion unblocks (#1667, license-blocked), reviewers must
treat `sovietization_risk > 0` results as caution flags, not as
authoritative definitions.

## Reproducibility

Re-run with the SQL block above. Drift detection: hook this audit into
CI (TODO, separate issue) so a Dependabot upgrade or schema migration
that drops rows is caught before it ships.

## Action items shipped this PR

1. Updated tool descriptions in `.mcp/servers/sources/server.py` for
   `search_style_guide`, `search_definitions`, `search_grinchenko_1907`,
   `search_idioms`, `search_synonyms`, `translate_en_uk`,
   `query_cefr_level`. Each now states actual indexed count, canonical
   source size, coverage percent, and known systematic exclusions.
2. Audit report committed at this path for reproducibility.
3. Cross-references: #1659 (Sovietization), #1658 (Грінченко rename),
   #1667 (СУМ-20 unblock), #1663 (Антоненко full ingest re-dispatch),
   #1662 (ЕСУМ vols 2-6).

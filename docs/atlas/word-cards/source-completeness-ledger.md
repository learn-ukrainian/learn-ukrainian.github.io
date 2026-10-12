# Phase 1 Hashed Source-Completeness Acceptance Ledger

- **Schema:** `source-completeness-ledger.v1`
- **Phase:** 1. Inventory and complete source data
- **Created:** 2026-10-12T21:57:09Z
- **Parent Issues:** #8977, #9401, #10513

## 1. Database File Digests

| Database | Path | Size (MB) | SHA-256 Digest |
|---|---|---|---|
| `sources.db` | `data/sources.db` | 5987.92 MB | `c1442255f0f89a545724e0cb50fc5a02f7e59b1c6774cb144dccd740562643df` |
| `vesum.db` | `data/vesum.db` | 1927.84 MB | `f640772e73b02dfcaf8e219938d22d2d91c9877294291b2f7f4145b3d7b20035` |
| `sum20_slovnyk_staging.db` | `data/sum20_slovnyk_staging.db` | 866.02 MB | `32e77a09e004a7ad740fa8acd350d0f5a743cb13f751e9d134ffcec5db595194` |

## 2. Partition: Verified-Complete

| Source ID | Edition | Counts | Snapshot ID | Custody |
|---|---|---|---|---|
| `vesum` | VESUM morphological dictionary v2 | forms_all: 6,970,759, forms_view: 6,632,807 | `vesum@53923150073b4fc7` | `data/vesum.db` |
| `ulif_checked` | Український лінгвістичний портал (ULIF) checked harvest | entries: 262,812 | `ulif@ulif-dictua-v2/2026-09-22..2026-09-27` | `data/sources.db:ulif_dictua_entries` |
| `sum20_slovnyk_staging` | СУМ-20 (Словник української мови у 20 томах) Slovnyk.me complete mirror | articles: 164,838 | `sum20@slovnyk_me_20261012` | `data/sum20_slovnyk_staging.db:sum20_slovnyk_articles` |
| `puls_cefr` | PULS Ukrainian CEFR vocabulary specification | total_rows: 5,939, by_level: {'A1': 962, 'A2': 1386, 'B1': 2164, 'B2': 1194, 'C1': 233} | `puls@sources.db/puls_cefr` | `data/sources.db:puls_cefr` |
| `frazeolohichnyi` | Фразеологічний словник української мови | total_rows: 24,683 | `frazeolohichnyi@sources.db` | `data/sources.db:frazeolohichnyi` |
| `grinchenko` | Словарь української мови (Б. Грінченко, 1907–1909) | total_rows: 67,275 | `grinchenko@sources.db` | `data/sources.db:grinchenko` |
| `wiktionary` | Ukrainian Wiktionary parsed extract | total_rows: 50,278 | `wiktionary@sources.db` | `data/sources.db:wiktionary` |
| `esum_etymology` | Етимологічний словник української мови (ЕСУМ, томи 1–6) | total_rows: 36,177 | `esum@sources.db` | `data/sources.db:esum_etymology` |
| `pedagogical_and_literary_corpora` | Ukrainian School Textbooks (Gr 1-11) & Literary Corpus | textbook_chunks: 54,127, literary_chunks: 137,723 | `textbooks_literary@sources.db` | `data/sources.db:textbooks,literary_texts` |

## 3. Partition: Missing

| Source ID | Edition | Available Counts | Gap Reason | Remediation |
|---|---|---|---|---|
| `sum20_official` | СУМ-20 Official Portal (sum20ua.com) | articles: 100, senses: 168 | `crawl_blocked_cloudflare_403` | Substituted by `sum20_slovnyk_staging` mirror (164,838 articles) |

## 4. Partition: Quarantined

| Source ID | Edition | Rows | Restriction |
|---|---|---|---|
| `sum11` | Словник української мови в 11 томах (СУМ-11, 1970–1980) | total_rows: 127,069 | Sovietization contrast and Russification detection ONLY (Rule #M-6 / #8990) |
| `ulif_legacy_unverified` | ULIF legacy unverified crawl (parser 1.0) | total_rows: 6,455 | Legacy parser defects (6,446 not_found, 3 ok) |

## 5. Partition: Genuinely-Absent (Named Field Gaps)

| Field Gap | Named Field | Lexical Universe Effect |
|---|---|---|
| modern_slang_and_neologisms | `etymology_unattested` | Unrecorded in academic 20th-century dictionaries |
| uncalibrated_cefr_levels | `cefr_unresolved` | Words outside the 5,939 PULS calibrated vocabulary set |
| unattested_collocations | `collocations_unrecorded` | Collocations without textbook or literary citations |

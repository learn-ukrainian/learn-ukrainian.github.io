# Polonism + anglicism eval expansion — scoping (#4288)

- status: **FLEET-REVIEWED scoping** (agy research 2026-07-05 · codex + cursor design reviews 2026-07-05,
  findings folded). Gates fixture-building; fixtures are a later PR with their own review.
- parent: #2156 (schema is source-language-agnostic: `source_lang: ru | pl | en | …` — note the tag is OUR
  annotation layer; UA-GEC carries NO source_lang annotations, research-verified 2026-07-05)

## 0. Scope boundary (resolves the open question, both reviewers concurring)

**Syntactic/phraseological EN calques («робити сенс», «мати ідею») are #2156 items** — standard-register
contact contamination with `source_lang: en`, scored by the existing calque axis. **#4288 owns ONLY the
lexical-borrowing boundary**: harmful unadapted borrowing vs accepted borrowing vs heritage-integrated
stratum vs term of art. Fixture routing enforces this (eval_axis guard, §3) so no item appears in both sets.

## 1. The core definitional problem

- **Polonisms** are largely HISTORICAL, integrated strata (western-UA lexicon: «кобіта», «філіжанка») —
  heritage vocabulary, NOT defects. **Etymological source ≠ live contact source (codex):** a word of Polish
  ORIGIN is never a `source_lang: pl` defect by ancestry alone; only live modern-contact borrowing/calquing
  can be. Every pl item must carry `contact_type: historical_integrated | modern_contact`.
- **Anglicisms** split: (a) terms of art, (b) accepted borrowings (Правопис 2019 codifies adaptation),
  (c) harmful unadapted lexical dumps where an attested UA word is in living use.

**Decision rule for `harmful_calque` gold (v2 — loosened per codex):** conjunctive core — (1) an attested UA
equivalent exists in LIVING USE (VESUM/СУМ-20/term-base, tool-verified), (2) the borrowing is unadapted OR
displaces the equivalent in its own register/domain, (3) no exemption (quotation, brand/code name, term of
art, established professional usage) — PLUS mandatory evidence fields that make the judgment reviewable
instead of binary: `domain`, `register`, `date_or_period`, `normative_source`, `usage_status
(displacing | coexisting | receding)`. Items where the rule is arguable go to gold ONLY with
`annotation_confidence: high` after adjudication; the rest are contrastive negatives.

## 2. Taxonomy

`harmful_calque | accepted_borrowing | heritage_integrated | term_of_art` — `term_of_art` kept distinct from
`accepted_borrowing` in gold (helps reviewer prompts; can merge in scoring if IAA demands).

## 3. Schema + storage (cursor two-layer pattern — same as #4287)

- Canonical `ua_contact_quality_evidence.v1` finding envelope untouched; gold in wrapper
  `borrowed_lexicon_fixture.v1` + `finding.metadata.eval_gold` (`borrowing_status`, `contact_type`,
  `equivalent_attestation`, `eval_axis: borrowed_lexicon`).
- `equivalent_uk` rides the already-validated `suggested_replacement[]`; its tool proof in
  `metadata.eval_gold.equivalent_attestation`.
- New profile `borrowed_lexicon_eval`; storage `data/borrowed-lexicon-gold/`; thin
  `BorrowedLexiconFixtureAdapter`; ingest fails on missing attestations; ingest lint = no id/excerpt-hash
  overlap with #2156 or #4287 gold. New metric block, cost-matrix scored (false-harmful-on-heritage
  penalized hardest).

## 4. Data sources (agy web-grounded research 2026-07-05; licenses re-verified at build time)

| source | content | labels | access | use |
|---|---|---|---|---|
| UA-GEC | GEC corpus | **no source_lang annotations** | CC BY 4.0 (re-verify) | not a pl/en gold source; our annotation layer only |
| LT-Ukranian-calques (grayodesa) | LanguageTool calque→correct rules | calque pairs | open source (verify license file) | EN-axis candidate mining |
| ukr-check-core (vitalinguist) | calque-pair dictionaries | calque mappings | open source (verify) | EN-axis candidate mining |
| Правопис 2019 | adaptation rules (no polonism inventory) | — | public (`query_pravopys` wired) | accepted_borrowing codification anchor |
| UK Wiktionary borrowing categories | terms-borrowed-from-pl/en | etymological origin | CC BY-SA 3.0 | headword + category + URL citations only (no bulk entry scrapes); positives for accepted/heritage — with the §1 caveat: Wiktionary gives ETYMOLOGY, so every scraped positive still needs the `contact_type` judgment |

**Research-confirmed consequence:** the pl axis has NO usable labeled calque data → v1 pl =
Wiktionary-cited positives + hand-curated fixture-only negatives; it is primarily a FALSE-POSITIVE test of
reviewers (does the system condemn «філіжанка»?). The EN axis mines the two rule repos for candidates, each
hand-verified before gold.

## 5. Fixture sizing + IAA

pl: 30–50 items, negative-weighted. en: 50–80 lexical-boundary items (syntactic calques excluded → #2156).
Same IAA pilot gate as #4287: 20–30 items, two annotators, adjudication, label freeze before the full build.

## 6. Build order

Scoping (this doc) → shared schema PR (profiles + wrappers + adapters for both #4287/#4288) → IAA pilots →
fixture builds → scorer wiring. Machinery prerequisites (#4306/#4307/#4308) already merged. Non-goals
honored: no ru-track rewrite, no leaderboard before the taxonomy is defensible, no proprietary text in git.

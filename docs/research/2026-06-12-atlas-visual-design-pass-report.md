# Word Atlas Visual-Design Pass Report

Date: 2026-06-12
Branch: `codex/atlas-visual-design-pass`
Scope: close live lemma-page visual gaps against `docs/poc/word-atlas/detail.html`, `landing.html`, and `heritage-defense.html`.

## Per-Gap Status

| Gap | Status | Notes |
| --- | --- | --- |
| Stress marks | Done | `scripts/lexicon/enrich_manifest.py` now loads `ukrainian-word-stress` lazily and emits `enrichment.stress` for the lemma header plus stressed morphology display forms. Forms with no trustworthy stress data are omitted gracefully and render unchanged. |
| Multi-source definitions | Done | Enrichment emits separate `definition_cards` for `Грінченко 1907`, live `СУМ-20` where covered by the public А-Р data, and `СУМ-11`. The render uses PoC-style `def-card` + `src-pill` cards and keeps the СУМ-11 sovietization risk/keywords on the card. Empty sources are omitted. |
| Editorial banners | Done | The Astro page now renders large `editorial-warn` / `editorial-success` sections. Green success appears for non-russianism entries with pre-Soviet attestation. Red/amber warning appears for russianisms and for shown СУМ-11 definition risk. |
| CEFR badge | Done | `puls_cefr` exact lookup emits `enrichment.cefr`; the header shows `CEFR {level}` when known and omits the badge when unknown. |
| Literary attestations | Done with strict gate | `literary_attestation` uses FTS only as a candidate source, then requires an exact whole-token match in the returned text. Clean hits render in a purple `source-box`; noisy or non-exact hits are omitted entirely. |
| Paradigm table width | Done | Paradigm tables are constrained and left-aligned (`44rem` noun/general, `48rem` verb blocks) so the table no longer occupies only a narrow strip inside a wide card. |

## Visual Proof (#M-4)

Built HTML marker counts from `starlight/dist/lexicon/{lemma}/index.html`:

| Lemma | Stress `́` | `src-pill` | `editorial-` | `CEFR` | `source-box` | Rendered sections/badges |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `вікно` | 23 | 3 | 3 | 2 | 2 | Header stress `вікно [вікно́]`, CEFR A1 badge, green editorial success banner, three definition cards, literary source box, stressed morphology table. |
| `міроприємство` | 0 | 0 | 4 | 0 | 0 | Large red russianism editorial warning with norm alternatives. No definition or literary cards were shown because no clean cards/hits were available. |

Additional visual QA used local Playwright against `astro preview`; the in-app Browser connector was unavailable in this session. The `вікно` paradigm table measured 704px wide inside a 1152px content card, matching the intended balanced PoC proportions.

## Validation

- `.venv/bin/python -m scripts.lexicon.build_data_manifest`
- `.venv/bin/python scripts/lexicon/enrich_manifest.py`
- `cd starlight && npm ci`
- `cd starlight && npm run build`
- `env -u AGENT_NO_TELEMETRY_FOOTER .venv/bin/pytest -k 'lexicon or manifest or atlas'`
  - Result: 127 passed, 8308 deselected, 1 xfailed.
- `.venv/bin/pytest tests/test_lexicon_enrich_manifest.py tests/test_atlas_conformance.py tests/test_lexicon_build_manifest.py`
  - Result: 31 passed.
- `.venv/bin/ruff check scripts/lexicon/enrich_manifest.py tests/test_lexicon_enrich_manifest.py`
  - Result: all checks passed.

Note: the runtime exported `AGENT_NO_TELEMETRY_FOOTER=1`, which suppresses Monitor API telemetry and makes the broad `-k 'lexicon or manifest or atlas'` selector fail in `tests/test_monitor_api_telemetry.py`. Unsetting that inherited flag lets the test exercise its own telemetry setup and pass.

# Dispatch brief — Word Atlas §8 deterministic conformance gates

**Owner lane:** Word Atlas (Claude). **Epic:** #2985 item 2. **Agent:** codex (gpt-5.5, xhigh).
**Mode:** danger + worktree. **No auto-merge.** **/code-review** after (load-bearing quality gate).

## Goal
Turn the design's §8 quality floors (`docs/best-practices/word-atlas-design.md` §8) into a
**deterministic validator + pytest** so "the Atlas follows the design" is ENFORCED on every PR
(via the existing required `Test (pytest)` check), not a manual review. No LLM in the path; no new
CI workflow needed (a pytest over the committed manifest is enough).

## Inputs (all deterministic, local)
- `starlight/src/data/lexicon-manifest.json` — the artifact under test. Entry shape:
  `{lemma, url_slug, gloss, pos, ipa, primary_source, course_usage[], enrichment?, heritage_status?}`.
  `enrichment` sections: `morphology{...,source}`, `meaning{definitions[],source,...}`,
  `attestation{text,source}`, `etymology{text,source}`, `sources[]`.
  `heritage_status`: `{classification, attestations[], is_russianism, russian_shadow,
  sovietization_risk, calque_warning}`. attestation rows: `{source, ref, detail?}`.
- `data/vesum.db` (SQLite, 967MB) — for lemma-in-VESUM. Use the same lookup other code uses
  (grep for how `verify_word`/vesum.db is queried; `scripts/lexicon/heritage_classifier.py` likely
  touches it). Single connection, read-only.
- `curriculum/l2-uk-en/curriculum.yaml` — module catalog for cross-link integrity.

## Gates to implement (design §8 — map each to a manifest check)
New module `scripts/audit/validate_atlas_conformance.py` exposing `validate(manifest, *, vesum, curriculum) -> list[Violation]` (Violation = `{gate, lemma, detail}`), plus a `__main__` CLI that prints violations and exits nonzero if any.

1. **lemma_in_vesum** — every SINGLE-WORD lemma (`" " not in lemma`) must exist in VESUM. Multi-word
   phrase entries (greetings like «До побачення») are EXEMPT (not VESUM lemmas) — skip them, but
   assert they're genuinely multi-word (don't let a typo'd single word slip through as "phrase").
2. **provenance_per_section** — every PRESENT enrichment section (`meaning`/`attestation`/
   `etymology`/`morphology`) MUST have a non-empty `source`. Violation if a section exists without one.
3. **section_omitted_not_empty** — the manifest MUST NOT carry an empty section object (e.g.
   `meaning` present but `definitions` empty, or `morphology` with no `forms`/`paradigm`). The render
   already omits empties (#2980); this gate locks the manifest invariant that feeds it.
4. **heritage_evidence_required** — if `heritage_status.classification` is a non-standard authentic
   status (`archaism`/`authentic-archaism`/`historism`/`dialect`/`borrowing`) OR an explicit
   `is_russianism=false` authenticity claim, then `attestations` MUST include ≥1 pre-Soviet source
   (`grinchenko_1907` or `esum`). Unsupported authenticity claim = violation. (`standard`/`unknown`
   need no attestation.)
5. **sovietization_must_be_flagged** — if any definition is sourced from СУМ-11 with a sovietization
   risk, `heritage_status.sovietization_risk` MUST be ≥1 (so the render shows the red warning).
   Implement against whatever per-source risk the manifest carries; if the current manifest carries
   risk only at `heritage_status.sovietization_risk`, assert the invariant holds and document it.
6. **cross_link_integrity** — every `course_usage` `{track, slug}` MUST resolve to a real module in
   `curriculum.yaml`. Broken cross-link = violation.
7. **wiki_summary_attributed** — if a `wikipedia` section exists (none yet), it MUST carry `url` +
   a freshness date. Implement the check now so it's ready when the section lands; it's a no-op today.

## Tests — `tests/test_atlas_conformance.py`
- **Real-manifest gate (the enforcement):** load the committed `lexicon-manifest.json` and assert
  `validate(...)` returns ZERO violations. This makes the existing `Test (pytest)` CI check fail if
  any future manifest regresses the design. (If the CURRENT manifest already violates a gate, FIX the
  data/generator or narrow the gate with a documented reason — do NOT weaken a gate to pass; surface it.)
- **Per-gate unit tests:** synthetic mini-manifests that each trip exactly one gate (missing source,
  empty section, authentic-without-attestation, broken course slug, unflagged sovietization) and one
  clean fixture that passes all. Use a tiny fake vesum/curriculum (inject via params; don't open the
  967MB db in unit tests — only the real-manifest test may, and even then cache/limit lookups).
- Keep VESUM lookups fast: the real-manifest test does ≤63 single-word lookups; use one connection.

## #M-4 — verifiable claims (quote raw)
| Claim | Check |
|---|---|
| Validator runs clean on current manifest | `.venv/bin/python -m scripts.audit.validate_atlas_conformance` → exit 0 + "0 violations" |
| Each gate fires on a violation | per-gate unit test names in pytest output |
| Suite green | `.venv/bin/pytest tests/test_atlas_conformance.py` final summary line raw |
| ruff clean | `.venv/bin/ruff check scripts/audit/validate_atlas_conformance.py tests/test_atlas_conformance.py` |

## Steps
1. `git worktree add` off `origin/main`.
2. `scripts/audit/validate_atlas_conformance.py` (validate() + Violation + CLI).
3. `tests/test_atlas_conformance.py` (real-manifest gate + per-gate unit tests + clean fixture).
4. Run validator on the real manifest. **If it finds real violations, report them** — they're design
   bugs to fix, not gate-weakening excuses. (Expected: current manifest passes, since #2980 fixed
   omit-empty/provenance; if heritage_evidence trips, investigate.)
5. `.venv/bin/pytest tests/test_atlas_conformance.py`; `.venv/bin/ruff check`.
6. Commit: `feat(audit): deterministic Word Atlas §8 conformance gates [#2985]`.
7. `git push -u origin <branch>`; `gh pr create` with raw evidence. **NO auto-merge.**

## Gotchas
- This is Python in `scripts/` + a test → pytest before push (#M-7), which you're doing.
- Do NOT weaken a gate to make CI pass — a gate that passes by being lax is worse than none (#M-11).
- Don't open `data/vesum.db` in the fast unit tests (inject a fake); only the real-manifest test may.
- Don't touch `codex/2888-a2-*` (A2 lane). graphql may 401 → REST. Required check = `Test (pytest)`.

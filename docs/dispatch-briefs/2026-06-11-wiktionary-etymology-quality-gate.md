# Dispatch brief — Harden #2970: Wiktionary etymology ingest quality gate

**Branch:** `codex/word-atlas-wiktionary-etym` (amend the OPEN PR #2970 — do NOT open a new PR).
**Agent:** codex (gpt-5.5, xhigh). **Mode:** danger + worktree. **No auto-merge.** Issue #2882.

## Why this fix (verified by Claude 2026-06-11 against the shipped table)
The ingest stores template-stripped text WITHOUT validating it's clean prose. Result in
`data/sources.db wiktionary_etymology` (11 rows) — quality scan:
```
звук         'Від звати Від звати Від зов'            (duplicated fragments)
йти          'Від ? 3 Дієслова'                       (empty-template + category leak)
ключ         'Від uk Від uk Від uk Від be Від ru'     (lang-param leak)
молоко       'Від Від ? 6 6 Предметні слова Напої…'   (category + empty-template leak)
потім        'Від uk Від uk Від uk'                   (lang-param leak)
книга        'Від від праслов’янського *kъnъ Від'     (truncated/duplicated)
комп'ютер    'Від англ. дієсл. to compute — "обчислити"'  ✓ CLEAN
кава         'Запозичено з арабської…'                ✓ CLEAN
стіл         'Від psl *stolъ, від якого також…'       ✓ CLEAN (psl = praslov.)
приголосний  'Похідне утворення від голос, див'       ✓ CLEAN
робота       'Від слова раб… Тобто раб це людина що робить роботу…'  (informal/circular ramble)
```
Precedence (Goroh→ЕСУМ→Wiktionary) currently shadows most, so only `комп'ютер` (good) and
`робота` (low-quality) surface in the manifest. But **the garbage rows live in the shared
`sources.db` and WILL surface in roadmap E** when vocab broadens past these 52 lemmas. Green
tests + a coverage bump are necessary-but-not-sufficient (MEMORY #M-11): the artifact is partly broken.

## The fix — a strict ingest quality gate (PRIMARY deliverable)
Add a validation function (e.g. `is_clean_etymology(text: str) -> bool`) applied **before** any row
is written to `wiktionary_etymology`. A row is REJECTED (skipped, not stored) if the cleaned text:
1. Contains markup/template residue: `{{`, `}}`, `[[Категорія`, `Категорія:`, `довжина слова`,
   `Предметні слова`, `мова=`, or other leaked template/category tokens.
2. Matches an "empty-template" pattern: contains `Від ?`, or a bare `Від <2-letter-code>` where the
   code is a language tag (`uk|be|ru|pl|cs|sh|bg|chu`) **not** part of real prose (heuristic: a token
   that is ONLY `Від` + a 2-letter lang code with no Cyrillic lexical content following).
3. Has high token repetition (e.g. unique/total tokens < 0.5 over >3 tokens) → duplicated fragments.
4. Is shorter than a small min (e.g. < 15 chars of real content) after cleaning.
5. Has no real lexical Ukrainian/etymon content (must contain at least one Cyrillic word of len ≥3
   that is not `Від`/a lang code, OR a recognised etymon marker like `*`, `псл`, `psl`, `запозич`).
**Better to store NO row than a garbage row.** Log each rejected lemma + reason to stdout so the
drop set is auditable.

Expected outcome after re-ingest: the 4–6 garbage/fragmentary rows (`йти`, `ключ`, `молоко`,
`потім`, and likely `звук`, `книга`) are dropped; `комп'ютер`, `кава`, `стіл`, `приголосний`
survive. Manifest single-word coverage net effect: `комп'ютер` remains the one Wiktionary-unique
surfaced etymology (the others are shadowed by Goroh/ЕСУМ anyway).

## `робота` — drop it
`робота`'s text ("…Тобто раб це людина що робить роботу. Або робота це те що робить раб…") is an
informal, circular Wiktionary editor ramble — not curriculum-grade. Make the gate reject it
(e.g. flag circular/colloquial markers, or simply require the etymology to not restate the headword
≥2×). If a clean heuristic can't catch it without false-positives, add `робота` to a small explicit
`_LOW_QUALITY_SKIP` denylist with a comment. Net: `робота` should NOT surface; it can stay uncovered
(it's a derived noun whose real etymology needs base-reduction — see follow-up).

## Secondary (nice-to-have, only if cheap): stripper hygiene
In `expand_templates`/`clean_wikitext`: render empty `{{етимологія|uk}}` / `{{етимологія:|uk}}`
to nothing (not "Від uk"/"Від ?"); strip `[[Категорія:…]]` and leaked category/`довжина слова`
residue; collapse duplicated identical sentences. This reduces reliance on the gate but the gate is
the load-bearing guarantee — do the gate first.

## Steps
1. `git worktree add` off `origin/main`; `git checkout codex/word-atlas-wiktionary-etym` (amend the PR).
   Rebase onto current `origin/main` first (it advanced: #2969 + #2854 merged).
2. Add `is_clean_etymology()` gate + wire into the ingest insert path; add the `робота` handling.
3. Re-run the ingest against the **already-pinned/cached `20260601` dump** (do not re-download if the
   dump is cached in the worktree; reuse the pin). This should DROP the garbage rows from
   `wiktionary_etymology` (make the ingest idempotent-replace so re-running cleans prior garbage —
   `DELETE`/`INSERT OR REPLACE` keyed by `requested_lemma`, or `DROP`+rebuild the table).
4. Regenerate `starlight/src/data/lexicon-manifest.json`.
5. Tests: extend `tests/test_wiktionary_etymology_ingest.py` with gate cases — assert each garbage
   sample above is REJECTED and each clean sample is ACCEPTED, and that `робота` is dropped.
6. `.venv/bin/pytest tests/test_wiktionary_etymology_ingest.py` + adjacent; `.venv/bin/ruff check`.
7. Commit on the branch (conventional): `fix(lexicon): quality-gate Wiktionary etymology ingest [#2882]`.
8. `git push` to update PR #2970. **NO auto-merge.**

## #M-4 — verifiable claims (quote raw)
| Claim | Check |
|---|---|
| Garbage dropped | `sqlite3 data/sources.db "SELECT requested_lemma,substr(etymology_text,1,40) FROM wiktionary_etymology ORDER BY 1"` → no lang-leak/markup rows |
| Clean kept | same query shows `комп'ютер`/`кава`/`стіл` clean |
| робота not surfaced | manifest `by source` shows `робота` NOT `Вікісловник` (NONE or shadowed) |
| Gate tested | pytest final summary line raw |
| Lint | ruff final line raw |

## Gotchas
- Re-ingest MUST clean prior garbage rows already in the shared `sources.db` (idempotent replace /
  rebuild), not just stop adding new ones — the 11 bad rows are already there.
- Don't touch `codex/2888-a2-*` (A2 lane). Only required CI check = `Test (pytest)`; graphql may 401 → REST.

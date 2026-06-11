# Word Atlas decolonization warnings visible — 2026-06-12

## Before

- `sum11` in `data/sources.db` had only `id, word, definition, text, source`.
- `classify_lemma("ленінізм")` and `classify_lemma("школа")` returned `classification=standard` with `sovietization_risk=0`.
- `classify_lemma("міроприємство")` already returned `classification=russianism`, `is_russianism=True`, alternative `захід`.
- The committed Atlas manifest had 63 entries and no Russianism/surzhyk seed pages, so no red warning badge could render on the live site.

## After

- `scripts/lexicon/migrate_sum11_sovietization.py` idempotently adds `sum11.sovietization_risk` and `sum11.sovietization_keywords`, then reuses `scripts/audit/sum11_sovietization_scan.py`.
- Local `data/sources.db` was migrated and populated: 127,069 rows scanned, 7,152 flagged.
- `classify_lemma("ленінізм")` returns `classification=standard`, `sovietization_risk=2`.
- `classify_lemma("школа")` returns `classification=standard`, `sovietization_risk=2`; it is not labeled a Sovietism.
- The Atlas detail page renders:
  - red word-level badges only for `russianism`/`sovietism`/`surzhyk` classifications;
  - amber source caveats only on `enrichment.meaning` when the displayed meaning is a Soviet-flagged СУМ-11 fallback.

## Seed List

All seed entries are independently classified by `classify_lemma()` before inclusion.

| Lemma | Classification | `is_russianism` | Alternatives |
| --- | --- | --- | --- |
| `агенство` | `russianism` | `True` | `агенція` |
| `авось` | `russianism` | `True` | `ану ж`, `а може`, `може-таки` |
| `автозагар` | `russianism` | `True` | `автозасмага` |
| `всьо` | `russianism` | `True` | `все` |
| `діюча` | `russianism` | `True` | `чинна` |
| `міроприємство` | `russianism` | `True` | `захід` |
| `протиріччя` | `russianism` | `True` | `суперечність`, `сперечання`, `супротивність` |
| `слідуючий` | `russianism` | `True` | `наступний`, `черговий`, `дальший` |

## Rendered Counts

- Red heritage badge pages in `starlight/dist/lexicon`: 8
- Amber СУМ-11 source-caveat pages in `starlight/dist/lexicon`: 8

Red pages:

```text
starlight/dist/lexicon/автозагар/index.html
starlight/dist/lexicon/міроприємство/index.html
starlight/dist/lexicon/протиріччя/index.html
starlight/dist/lexicon/авось/index.html
starlight/dist/lexicon/агенство/index.html
starlight/dist/lexicon/слідуючий/index.html
starlight/dist/lexicon/всьо/index.html
starlight/dist/lexicon/діюча/index.html
```

Amber pages:

```text
starlight/dist/lexicon/готовий/index.html
starlight/dist/lexicon/рід/index.html
starlight/dist/lexicon/ключ/index.html
starlight/dist/lexicon/дім/index.html
starlight/dist/lexicon/прокидатися/index.html
starlight/dist/lexicon/збиратися/index.html
starlight/dist/lexicon/навчатися/index.html
starlight/dist/lexicon/стіна/index.html
```

## Command Log

### Initial worktree check

Command:

```bash
git status --short --branch
```

Cwd:

```text
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/atlas-moat-visible
```

Output:

```text
## codex/atlas-moat-visible...origin/main
?? node_modules
```

### Pre-migration schema check

Command:

```bash
sqlite3 data/sources.db 'PRAGMA table_info(sum11);'
```

Cwd:

```text
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/atlas-moat-visible
```

Output:

```text
0|id|INTEGER|0||1
1|word|TEXT|1||0
2|definition|TEXT|1|''|0
3|text|TEXT|1|''|0
4|source|TEXT|0|''|0
```

### Migration and scan

Command:

```bash
.venv/bin/python scripts/lexicon/migrate_sum11_sovietization.py --db data/sources.db
```

Cwd:

```text
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/atlas-moat-visible
```

Output:

```text
schema actions: add sovietization_risk, add sovietization_keywords, ensure idx_sum11_sovietization
Updating 127069 rows (7152 flagged)...
Scanned 127,069 rows. Flagged 7,152 (5.63% — 755 high, 6,397 low).
```

### Two-tier classifier verification

Command:

```bash
.venv/bin/python - <<'PY'
from scripts.lexicon.heritage_classifier import classify_lemma
for lemma in ['ленінізм', 'школа', 'міроприємство']:
    status = classify_lemma(lemma)
    alts = [a.get('ref') for a in status.get('attestations', []) if a.get('source') == 'standard_alternative']
    print(f"{lemma}: classification={status.get('classification')} is_russianism={status.get('is_russianism')} sovietization_risk={status.get('sovietization_risk')} alternatives={alts}")
PY
```

Cwd:

```text
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/atlas-moat-visible
```

Output:

```text
ленінізм: classification=standard is_russianism=False sovietization_risk=2 alternatives=[]
школа: classification=standard is_russianism=False sovietization_risk=2 alternatives=[]
міроприємство: classification=russianism is_russianism=True sovietization_risk=0 alternatives=['захід']
```

### Seed classifier verification

Command:

```bash
.venv/bin/python - <<'PY'
from scripts.lexicon.build_data_manifest import SURZHYK_TO_AVOID_SEEDS
from scripts.lexicon.heritage_classifier import classify_lemma
for seed in SURZHYK_TO_AVOID_SEEDS:
    lemma = str(seed['lemma'])
    status = classify_lemma(lemma)
    alts = [a.get('ref') for a in status.get('attestations', []) if a.get('source') == 'standard_alternative']
    print(f"{lemma}: classification={status.get('classification')} is_russianism={status.get('is_russianism')} alternatives={alts}")
PY
```

Cwd:

```text
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/atlas-moat-visible
```

Output:

```text
агенство: classification=russianism is_russianism=True alternatives=['агенція']
авось: classification=russianism is_russianism=True alternatives=['ану ж', 'а може', 'може-таки']
автозагар: classification=russianism is_russianism=True alternatives=['автозасмага']
всьо: classification=russianism is_russianism=True alternatives=['все']
діюча: classification=russianism is_russianism=True alternatives=['чинна']
міроприємство: classification=russianism is_russianism=True alternatives=['захід']
протиріччя: classification=russianism is_russianism=True alternatives=['суперечність', 'сперечання', 'супротивність']
слідуючий: classification=russianism is_russianism=True alternatives=['наступний', 'черговий', 'дальший']
```

### Manifest rebuild

Command:

```bash
.venv/bin/python -m scripts.lexicon.build_data_manifest
```

Cwd:

```text
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/atlas-moat-visible
```

Output:

```text
Wrote starlight/src/data/lexicon-manifest.json: 138 lemmas across 3 modules (built=121, plan_only=9).
```

Command:

```bash
.venv/bin/python scripts/lexicon/enrich_manifest.py
```

Cwd:

```text
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/atlas-moat-visible
```

Output:

```text
enriched 88/138 lexicon entries from VESUM + Грінченко/СУМ + Горох/ЕСУМ/Вікісловник
single-word etymology 49/113
```

### Tests

Command:

```bash
.venv/bin/python -m pytest tests/ -k 'lexicon or manifest or atlas or heritage or sovietization' -q
```

Cwd:

```text
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/atlas-moat-visible
```

Output:

```text
FAILED tests/test_monitor_api_telemetry.py::test_manifest_json_adds_structured_telemetry_when_enabled
KeyError: '_telemetry'
```

Note: this Codex session had `AGENT_NO_TELEMETRY_FOOTER=1`, which globally disables the telemetry field that this unrelated `manifest`-selected test asserts.

Command:

```bash
env -u AGENT_NO_TELEMETRY_FOOTER .venv/bin/python -m pytest tests/ -k 'lexicon or manifest or atlas or heritage or sovietization' -q
```

Cwd:

```text
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/atlas-moat-visible
```

Output:

```text
========= 153 passed, 8268 deselected, 1 xfailed, 3 warnings in 38.65s =========
```

### Ruff

Command:

```bash
.venv/bin/ruff check scripts/audit/sum11_sovietization_scan.py scripts/audit/validate_atlas_conformance.py scripts/lexicon/build_data_manifest.py scripts/lexicon/enrich_manifest.py scripts/lexicon/heritage_classifier.py scripts/lexicon/migrate_sum11_sovietization.py tests/test_atlas_conformance.py tests/test_lexicon_build_manifest.py tests/test_lexicon_enrich_manifest.py tests/test_sum11_sovietization_scan.py
```

Cwd:

```text
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/atlas-moat-visible
```

Output:

```text
All checks passed!
```

### Starlight install and build

Command:

```bash
npm ci
```

Cwd:

```text
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/atlas-moat-visible/starlight
```

Output:

```text
added 617 packages, and audited 618 packages in 6s
found 0 vulnerabilities
```

Command:

```bash
npm run build
```

Cwd:

```text
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/atlas-moat-visible/starlight
```

Output:

```text
> starlight@0.0.1 build
> astro build

[etymology] Skipping full ESUM dynamic routes. Set BUILD_ETYMOLOGY_ROUTES=1 for the full reference build.
01:00:53 [build] 296 page(s) built in 15.24s
01:00:53 [build] Complete!
```

### Dist badge counts

Command:

```bash
rg -l 'atlas-heritage-pill--russism' starlight/dist/lexicon | wc -l
```

Cwd:

```text
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/atlas-moat-visible
```

Output:

```text
8
```

Command:

```bash
rg -l 'atlas-source-caveat' starlight/dist/lexicon | wc -l
```

Cwd:

```text
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/atlas-moat-visible
```

Output:

```text
8
```

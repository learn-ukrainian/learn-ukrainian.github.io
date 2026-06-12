# Word Atlas Synonym Sense Fix Report

Date: 2026-06-12

Worktree:

```text
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/atlas-synonym-sense-fix
```

## Manifest Rebuild

Command:

```bash
.venv/bin/python scripts/lexicon/enrich_manifest.py
```

Raw output:

```text
enriched 92/138 lexicon entries from VESUM + Грінченко/СУМ + Горох/ЕСУМ/Вікісловник + slovnyk.me
single-word etymology 49/113
```

## M-4 Quality Gate

Command:

```bash
.venv/bin/python - <<'PY'
import json, unicodedata
from pathlib import Path
manifest = json.loads(Path('starlight/src/data/lexicon-manifest.json').read_text(encoding='utf-8'))
def norm(value):
    text = unicodedata.normalize('NFD', str(value or ''))
    text = ''.join(ch for ch in text if ch not in {'\u0300','\u0301'})
    return unicodedata.normalize('NFC', text).casefold()
targets = ['вода','голосний','вставати','місто','привіт','чудово','батько','вчитель','абетка','актор','вранці','добре']
by_norm = {norm(entry.get('lemma')): entry for entry in manifest['entries']}
print('synonym_entry_count', sum(1 for e in manifest['entries'] if ((e.get('sections') or {}).get('synonyms') or {}).get('items')))
print('idiom_entry_count', sum(1 for e in manifest['entries'] if ((e.get('sections') or {}).get('idioms') or {}).get('items')))
print('idiom_text_missing_count', sum(1 for e in manifest['entries'] for item in (((e.get('sections') or {}).get('idioms') or {}).get('items') or []) if not item.get('text')))
print('sample_synonyms')
for target in targets:
    entry = by_norm.get(target)
    if not entry:
        print(f'{target}: <missing>')
        continue
    items = (((entry.get('sections') or {}).get('synonyms') or {}).get('items') or [])
    print(f'{target}: {", ".join(items) if items else "<omitted>"}')
print('idiom_samples')
shown = 0
for entry in manifest['entries']:
    for item in (((entry.get('sections') or {}).get('idioms') or {}).get('items') or []):
        text = item.get('text')
        if text:
            print(f'{norm(entry.get("lemma"))}: {text}')
            shown += 1
            if shown == 5:
                raise SystemExit
PY
```

Raw output:

```text
synonym_entry_count 20
idiom_entry_count 46
idiom_text_missing_count 0
sample_synonyms
вода: <omitted>
голосний: <omitted>
вставати: зводитися, підводитися, підхоплюватися
місто: <omitted>
привіт: вітання, привітання, уклін, поклін
чудово: чудесно, блискуче
батько: тато, отець, татусь, татко
вчитель: педагог, викладач, вихователь, навчитель
абетка: алфавіт, азбука
актор: артист, лицедій, виконавець
вранці: зранку, ранком, рано
добре: непогано, незле, гаразд
idiom_samples
привіт: ні одвіту, ні привіту, перев. зі сл. нема, не мати і т. ін., жарт
батько: іди (собі) к бісовому батькові (к нечистій матері), лайл
вода: багато (чимало) води сплило (спливло, упливло, утекло і т. ін. )
вона: бери його (її, їх і т. ін. ) лиха година, лайл
вставати: (аж) волосся піднімається (підіймається, встає, лізе і т. ін. ) / піднялося (встало, полізло і т. ін. ) вгору (догори) у кого і без додатка
```

Result: 20 words now carry synonym sections. The requested 12-word sample has 0 wrong-sense synonym emissions; omitted entries are intentional omit-empty cases where the course sense is not confidently matched.

## Validation

Commands and raw outputs:

```bash
cd starlight
npm ci
```

```text
added 617 packages, and audited 618 packages in 6s
found 0 vulnerabilities
```

```bash
cd starlight
npm run build
```

```text
[build] 296 page(s) built in 16.23s
[build] Complete!
```

```bash
env -u AGENT_NO_TELEMETRY_FOOTER .venv/bin/python -m pytest tests/ -k 'lexicon or manifest or atlas' -q
```

```text
123 passed, 8306 deselected, 1 xfailed, 3 warnings in 20.71s
```

```bash
env -u AGENT_NO_TELEMETRY_FOOTER .venv/bin/ruff check scripts/lexicon/enrich_manifest.py scripts/wiki/slovnyk_me.py tests/test_lexicon_enrich_manifest.py tests/test_slovnyk_me_tool.py
```

```text
All checks passed!
```

Note: the shell had `AGENT_NO_TELEMETRY_FOOTER=1` set, which makes `tests/test_monitor_api_telemetry.py` fail under the broad `-k manifest` selector. The selector passes when that guard is unset for the command. A full-repo `ruff check` also reports existing unrelated violations under `docs/reports/` and `plans/`; the changed files are ruff-clean.

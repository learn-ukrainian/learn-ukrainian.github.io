# Word Atlas v2 Scale Feasibility Spike — 2026-06-11

## Verdict

**GO for Astro static rendering at the measured v2-spike scale.** The current A1+A2+B1 curriculum-vocab ∩ `puls_cefr` scope produced 1,149 lemmas, and `astro build` emitted 1,305 HTML pages in 13.25s Astro-reported build time / 14.79s wall-clock.

This is **not** evidence that the earlier ~3-5K lemma estimate is real. The measured intersection is much smaller than expected. Static rendering is fine for this observed v2 set, but the 4.5K-page risk remains an extrapolation until the source set actually reaches that size.

## Four Numbers

1. **Lemma count:** 1,149 lemmas after A1+A2+B1 curriculum vocabulary is intersected with single-word `puls_cefr` rows at levels A1/A2/B1.
2. **Static build:** `astro build` completed in 13.25s reported / 14.79s wall-clock and emitted 1,305 `*.html` files.
3. **Moat visibility:** 0/1,149 lemmas received a non-`standard` heritage badge or russianism/sovietization/calque signal. Classification breakdown was `standard=1148`, `unknown=1`.
4. **Enrichment coverage:** morphology 1,109/1,149 (96.52%), meaning 1,087/1,149 (94.60%), etymology 447/1,149 (38.90%), non-empty heritage classification 1,149/1,149 (100.00%).

## Surprises

- The measured lemma count is far below the §9 ~3-5K estimate. Current data dropped 581 multi-word phrases and 1,008 single-word curriculum lemmas not present in A1/A2/B1 `puls_cefr`.
- The decolonization moat still does not fire on this scaled dataset. `classify_lemma` marked 1,148 entries `standard` and 1 `unknown`; no russianism, sovietization, calque, dialect, borrowing, historism, or archaism badge surfaced.
- Astro emitted two duplicate-route warnings for stressed/unstressed duplicate lemmas: `/lexicon/джерело` and `/lexicon/молоко`. The build still succeeded, but full v2 should normalize or dedupe stress variants before shipping the live manifest.
- Enrichment runtime was 67.63s wall-clock for 1,149 lemmas. That is acceptable for a build-time artifact, but a true 4.5K run would need a measured follow-up after the source set is expanded.

## Validation

- `env -u AGENT_NO_TELEMETRY_FOOTER .venv/bin/python -m pytest tests/ -k 'lexicon or manifest or atlas or heritage' -q` passed: `141 passed, 8274 deselected, 1 xfailed, 3 warnings in 35.56s`.
- `.venv/bin/ruff check scripts/lexicon/build_data_manifest.py` passed: `All checks passed!`.
- Note: the same pytest selector failed once under the delegate shell because `AGENT_NO_TELEMETRY_FOOTER=1` suppresses `_telemetry` in an unrelated selected monitor API test. Removing only that inherited override made the selector green.

## Evidence

### 1. Lemma Count

Command:

```bash
cwd=/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/word-atlas-v2-scale-spike
.venv/bin/python -m scripts.lexicon.build_data_manifest --scope v2-spike
```

Raw output:

```text
Wrote starlight/src/data/lexicon-manifest.v2-spike.json: 1149 lemmas across 218 modules (from_built=338, from_plan=811, dropped_not_in_puls=1008, dropped_multi_word=581).
```

### 2. Static Build

Command:

```bash
cwd=/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/word-atlas-v2-scale-spike/starlight
npm ci
```

Raw output:

```text
added 617 packages, and audited 618 packages in 7s
found 0 vulnerabilities
```

Command:

```bash
cwd=/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/word-atlas-v2-scale-spike/starlight
/usr/bin/time -p npm run build
```

Raw output:

```text
22:50:50 [build] 1305 page(s) built in 13.25s
real 14.79
user 17.67
sys 2.33
```

Command:

```bash
cwd=/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/word-atlas-v2-scale-spike/starlight
find dist -name '*.html' | wc -l
```

Raw output:

```text
1305
```

### 3. Moat Visibility

Command:

```bash
cwd=/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/word-atlas-v2-scale-spike
.venv/bin/python -c "import json; from collections import Counter; p='starlight/src/data/lexicon-manifest.v2-spike.json'; m=json.load(open(p, encoding='utf-8')); entries=m['entries']; total=len(entries); pct=lambda n: (n/total*100 if total else 0); morph=sum(1 for e in entries if (e.get('enrichment') or {}).get('morphology')); meaning=sum(1 for e in entries if (e.get('enrichment') or {}).get('meaning')); etym=sum(1 for e in entries if (e.get('enrichment') or {}).get('etymology')); heritage=sum(1 for e in entries if (e.get('heritage_status') or {}).get('classification')); nonstd=[e for e in entries if (lambda h: h and (h.get('classification') not in ('standard','unknown','') or h.get('is_russianism') or h.get('sovietization_risk') or h.get('calque_warning')))(e.get('heritage_status') or {})]; classes=Counter((e.get('heritage_status') or {}).get('classification') or 'empty' for e in nonstd); russian=sum(1 for e in nonstd if (e.get('heritage_status') or {}).get('is_russianism')); soviet=sum(1 for e in nonstd if (e.get('heritage_status') or {}).get('sovietization_risk')); calque=sum(1 for e in nonstd if (e.get('heritage_status') or {}).get('calque_warning')); print(f'coverage total={total} morphology={morph}/{total} ({pct(morph):.2f}%) meaning={meaning}/{total} ({pct(meaning):.2f}%) etymology={etym}/{total} ({pct(etym):.2f}%) heritage_nonempty={heritage}/{total} ({pct(heritage):.2f}%)'); print('heritage_nonstandard total={}/{} ({:.2f}%) russianism={} sovietization={} calque={} classifications={}'.format(len(nonstd), total, pct(len(nonstd)), russian, soviet, calque, dict(sorted(classes.items()))))"
```

Raw output:

```text
heritage_nonstandard total=0/1149 (0.00%) russianism=0 sovietization=0 calque=0 classifications={}
```

Command:

```bash
cwd=/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/word-atlas-v2-scale-spike
.venv/bin/python -c "import json; from collections import Counter; m=json.load(open('starlight/src/data/lexicon-manifest.v2-spike.json', encoding='utf-8')); c=Counter((e.get('heritage_status') or {}).get('classification') or 'empty' for e in m['entries']); print('heritage_classifications ' + ' '.join(f'{k}={v}' for k, v in sorted(c.items())))"
```

Raw output:

```text
heritage_classifications standard=1148 unknown=1
```

### 4. Enrichment Coverage

Command:

```bash
cwd=/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/word-atlas-v2-scale-spike
/usr/bin/time -p .venv/bin/python -c "from pathlib import Path; import scripts.lexicon.enrich_manifest as e; e.MANIFEST = Path('starlight/src/data/lexicon-manifest.v2-spike.json').resolve(); e.main()"
```

Raw output:

```text
enriched 1123/1149 lexicon entries from VESUM + Грінченко/СУМ + Горох/ЕСУМ/Вікісловник
single-word etymology 447/1149
real 67.63
user 40.98
sys 17.99
```

Command:

```bash
cwd=/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/word-atlas-v2-scale-spike
.venv/bin/python -c "import json; from collections import Counter; p='starlight/src/data/lexicon-manifest.v2-spike.json'; m=json.load(open(p, encoding='utf-8')); entries=m['entries']; total=len(entries); pct=lambda n: (n/total*100 if total else 0); morph=sum(1 for e in entries if (e.get('enrichment') or {}).get('morphology')); meaning=sum(1 for e in entries if (e.get('enrichment') or {}).get('meaning')); etym=sum(1 for e in entries if (e.get('enrichment') or {}).get('etymology')); heritage=sum(1 for e in entries if (e.get('heritage_status') or {}).get('classification')); nonstd=[e for e in entries if (lambda h: h and (h.get('classification') not in ('standard','unknown','') or h.get('is_russianism') or h.get('sovietization_risk') or h.get('calque_warning')))(e.get('heritage_status') or {})]; classes=Counter((e.get('heritage_status') or {}).get('classification') or 'empty' for e in nonstd); russian=sum(1 for e in nonstd if (e.get('heritage_status') or {}).get('is_russianism')); soviet=sum(1 for e in nonstd if (e.get('heritage_status') or {}).get('sovietization_risk')); calque=sum(1 for e in nonstd if (e.get('heritage_status') or {}).get('calque_warning')); print(f'coverage total={total} morphology={morph}/{total} ({pct(morph):.2f}%) meaning={meaning}/{total} ({pct(meaning):.2f}%) etymology={etym}/{total} ({pct(etym):.2f}%) heritage_nonempty={heritage}/{total} ({pct(heritage):.2f}%)'); print('heritage_nonstandard total={}/{} ({:.2f}%) russianism={} sovietization={} calque={} classifications={}'.format(len(nonstd), total, pct(len(nonstd)), russian, soviet, calque, dict(sorted(classes.items()))))"
```

Raw output:

```text
coverage total=1149 morphology=1109/1149 (96.52%) meaning=1087/1149 (94.60%) etymology=447/1149 (38.90%) heritage_nonempty=1149/1149 (100.00%)
```

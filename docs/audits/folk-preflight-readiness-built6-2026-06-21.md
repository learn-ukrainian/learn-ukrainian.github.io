# FOLK Preflight Readiness Audit - 6 Built Modules

Date: 2026-06-21
Prompt: `docs/prompts/orchestrators/folk/preflight-readiness-audit-orchestrator.md` v0.2
Scope: six built FOLK modules and their plans.

## Verdict

Not ready for production. Four built modules have a reading-deficit under the v0.2 FOLK floor because the gate-safe corpus already holds at least four verified primary texts and the plan/site surface fewer than `min(4, available)`. Two modules need source acquisition because the current corpus search found no standalone gate-safe primary text rows for the module topic. One plan also mislabels secondary scholarship as `type: primary`.

Blockers: 7

## Module Summary

| Module | Corpus-available primary texts | Surfaced plan/site readings | Deficit? | Mislabeled scholarly refs | Copyright decisions |
| --- | ---: | ---: | --- | --- | --- |
| `koliadky-shchedrivky` | 6 verified | 3 | Yes - needs at least 1 more surfaced reading | none found | 3 hosted existing, 3 hosted candidates, 1 omit failed verifier |
| `dumy-nevilnytski-lytsarski` | 5 verified, with curation needed for strict cycle fit | 0 | Yes - needs 4 surfaced readings | 3 refs retag to `type: scholarly` | 5 hosted candidates, 2 current external resources linked-only, 1 omit/reading-needed for unverified onsite Marusia text |
| `kalendarna-obriadovist-zvychai` | 4 verified | 0 | Yes - needs 4 surfaced readings | none found | 4 hosted candidates, 1 current external resource linked-only, 2 omit failed verifier |
| `narodna-kultura-yak-systema` | at least 4 verified cross-genre candidates | 0 | Yes - needs curated anthology-style primary catalog | none found | 4 hosted cross-genre candidates, 1 current external resource linked-only |
| `narodni-viruvannia-mifolohiia-demonolohiia` | 0 standalone gate-safe rows found | 0 | No floor deficit; `reading-needed` | none found | 1 current external resource linked-only, literary/scholarly snippets excerpt-only or omit, 4 reading-needed slots |
| `zamovliannia-zaklynannia-prymovky` | 0 standalone gate-safe rows found | 0 | No floor deficit; `reading-needed` | none found | 1 current external resource linked-only, 2 encyclopedia/textbook formulas excerpt-only, 4 reading-needed slots |

Reading coverage counts: hosted 3 currently surfaced, 19 verified hostable candidate slots across the four corpus-supported modules; link-only 6 current external reading resources; excerpt-only 2 secondary-quoted formula snippets; omit 4 failed/non-primary candidates; needed 8 source-acquisition slots for the two corpus-empty modules.

## Findings

### FOLK-PREFLIGHT-001 - `koliadky-shchedrivky` under-surfaces current corpus

Severity: blocker

The plan/site surface three hosted readings, but current MCP evidence verifies six distinct `Народна творчість` carol/shchedrivka rows in `ukrlib-narod-dumy`. The floor is therefore `min(4, 6) = 4`; the built module is short by at least one surfaced primary reading. This supersedes any older exemplar note that treated the corpus as holding fewer distinct songs.

Copyright: the three surfaced readings are already hosted/public-domain. The three additional verified `ukrlib-narod-dumy` rows are hosted candidates. `У цьому дворку як у вінку` is omitted because verifier confidence is below threshold.

### FOLK-PREFLIGHT-002 - `dumy-nevilnytski-lytsarski` has no surfaced primary readings

Severity: blocker

The corpus verifies five `Народна творчість` duma-topic rows. Some are historical-song-like and need editorial curation for the strict "невільницькі та лицарські думи" focus, but availability is still at least four primary rows. The plan and built MDX surface zero primary readings.

Copyright: verified `ukrlib-narod-dumy` rows are hosted candidates. Existing Wikisource/Wikipedia resources are linked-only and do not satisfy the FOLK primary-reading floor by themselves. The onsite `duma-marusia-bohuslavka` reading is not surfaced here and failed `verify_quote` under `Народна творчість`, so it should be omitted from the gate-safe count until independently verified from a standalone primary source.

### FOLK-PREFLIGHT-003 - `kalendarna-obriadovist-zvychai` has no surfaced primary readings

Severity: blocker

The corpus verifies two spring-song rows and two harvest-song rows from `Народна творчість`, enough to trigger the floor. The plan and built MDX surface zero primary readings.

Copyright: all four verified `ukrlib-narod-dumy` rows are hosted candidates. The current Wikisource `Веснянки` resource is linked-only. `Жали женчики, жали` and `Нуте, нуте, до межі` are omitted because the verifier did not match them as standalone `Народна творчість` rows.

### FOLK-PREFLIGHT-004 - `narodna-kultura-yak-systema` lacks a primary-text catalog

Severity: blocker

This overview teaches folk culture as a system across genres. The corpus already verifies enough cross-genre primary rows to build an anthology-style catalog, but the plan and built MDX surface zero readings. Remediation should curate a deliberate set, not randomly reuse adjacent texts.

Copyright: verified public-domain rows from `ukrlib-narod-dumy` are hosted candidates; the current Wikipedia resource remains linked-only.

### FOLK-PREFLIGHT-005 - `narodni-viruvannia-mifolohiia-demonolohiia` is `reading-needed`

Severity: blocker

Searches found literary adaptations, wiki/textbook chunks, and scholarship about demonological figures, but no standalone `Народна творчість` primary row verified by `verify_quote`. Do not backfill this module with Lesia Ukrainka, Hotkevych, encyclopedia prose, or scholarly descriptions as primary text.

Copyright: current resources are linked-only. Literary or scholarly snippets may be excerpt-only for analysis, but they do not count toward the primary floor. Record four source-acquisition tasks for standalone gate-safe legend/bylychka/pereказ texts.

### FOLK-PREFLIGHT-006 - `zamovliannia-zaklynannia-prymovky` is `reading-needed`

Severity: blocker

Searches found formulas quoted inside encyclopedia/textbook chunks. `verify_quote` did not verify them under `Народна творчість`, so the current gate-safe count is zero. Do not host full texts from secondary/modern textbook quotations.

Copyright: the encyclopedia/textbook formulas are excerpt-only if used for discussion and should not be counted as primary readings. Record four source-acquisition tasks for standalone public-domain zamovliannia/zaklynannia/primovka texts.

### FOLK-PREFLIGHT-007 - `dumy-nevilnytski-lytsarski` mislabels scholarship as primary

Severity: blocker

Three references are tagged `type: primary` but are scholarly/secondary works and must be retagged `type: scholarly`: Чижевський, Костомаров, and Попович. They must not count toward the reading floor.

## Raw Evidence Appendix

### Plan Parse

Command:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
import yaml
for path in sorted(Path('curriculum/l2-uk-en/plans/folk').glob('*.yaml')):
    yaml.safe_load(path.read_text(encoding='utf-8'))
print('folk plans parse')
PY
```

Raw output:

```text
folk plans parse
```

### Surfaced Reading Evidence

Plan `readings:` grep across the six scoped plans:

```text
curriculum/l2-uk-en/plans/folk/koliadky-shchedrivky.yaml:118:1:readings:
```

Raw plan block for the only scoped plan with readings:

```text
   118	readings:
   119	- title: «Як ще не було початку світа»
   120	  title_en: When the world had no beginning
   121	  genre: Колядка
   122	  source: Народна творчість; корпус ukrlib-narod-dumy
   123	  source_url: https://www.ukrlib.com.ua/narod/printout.php?id=5&bookid=2
   124	  license: public_domain
   125	  hosting: host
   126	  reading_slug: koliadka-yak-shche-ne-bulo
   127	- title: «Ой сивая та і зозулечка»
   128	  title_en: Oh, the grey cuckoo
   129	  genre: Щедрівка
   130	  source: Народна творчість; корпус ukrlib-narod-dumy
   131	  source_url: https://www.ukrlib.com.ua/narod/printout.php?id=6&bookid=1
   132	  license: public_domain
   133	  hosting: host
   134	  reading_slug: shchedrivka-oi-syvaia-ta-i-zozulechka
   135	- title: «Щедрик, щедрик, щедрівочка»
   136	  title_en: Shchedryk, shchedryk, little swallow
   137	  genre: Щедрівка
   138	  source: Народна творчість; корпус ukrlib-narod-dumy; chunk d4848a7e_c0000
   139	  license: public_domain
   140	  hosting: host
   141	  reading_slug: shchedrivka-shchedryk-lastivochka
```

Built MDX reading links:

```text
site/src/content/docs/folk/koliadky-shchedrivky.mdx:135:59:- [«Як ще не було початку світа»](/readings/koliadka-yak-shche-ne-bulo/) — Колядка · When the world had no beginning
site/src/content/docs/folk/koliadky-shchedrivky.mdx:136:52:- [«Ой сивая та і зозулечка»](/readings/shchedrivka-oi-syvaia-ta-i-zozulechka/) — Щедрівка · Oh, the grey cuckoo
site/src/content/docs/folk/koliadky-shchedrivky.mdx:137:58:- [«Щедрик, щедрик, щедрівочка»](/readings/shchedrivka-shchedryk-lastivochka/) — Щедрівка · Shchedryk, shchedryk, little swallow
site/src/content/docs/folk/koliadky-shchedrivky.mdx:141:2:<PrimaryReading href="/readings/koliadka-yak-shche-ne-bulo/">
site/src/content/docs/folk/koliadky-shchedrivky.mdx:179:2:<PrimaryReading href="/readings/shchedrivka-oi-syvaia-ta-i-zozulechka/">
site/src/content/docs/folk/koliadky-shchedrivky.mdx:249:2:<PrimaryReading href="/readings/shchedrivka-shchedryk-lastivochka/">
site/src/content/docs/folk/koliadky-shchedrivky.mdx:498:57:- 📖 [«Ой сивая та і зозулечка»](/readings/shchedrivka-oi-syvaia-ta-i-zozulechka/) — Повний текст на сайті — щедрівка з формулою трьох теремів і родинної тріади.
site/src/content/docs/folk/koliadky-shchedrivky.mdx:499:64:- 📖 [«Як ще не було початку світа»](/readings/koliadka-yak-shche-ne-bulo/) — Повний текст на сайті — космогонічна колядка, яку модуль читає як первинне джерело.
```

Same grep against the other five scoped MDX files returned empty output.

Source module text-layer markers:

```text
curriculum/l2-uk-en/folk/koliadky-shchedrivky/module.md:5:1::::primary-reading
curriculum/l2-uk-en/folk/koliadky-shchedrivky/module.md:64:1::::primary-reading
curriculum/l2-uk-en/folk/koliadky-shchedrivky/module.md:99:1::::primary-reading
curriculum/l2-uk-en/folk/koliadky-shchedrivky/module.md:118:1::::myth-box
curriculum/l2-uk-en/folk/koliadky-shchedrivky/module.md:157:1::::myth-box
curriculum/l2-uk-en/folk/koliadky-shchedrivky/module.md:168:1::::primary-reading{reading="shchedrivka-shchedryk-lastivochka"}
curriculum/l2-uk-en/folk/koliadky-shchedrivky/module.md:202:1::::high-culture-bridge
```

```text
curriculum/l2-uk-en/folk/dumy-nevilnytski-lytsarski/module.md:29:1::::myth-box
curriculum/l2-uk-en/folk/dumy-nevilnytski-lytsarski/module.md:111:1::::myth-box
curriculum/l2-uk-en/folk/dumy-nevilnytski-lytsarski/module.md:150:1::::high-culture-bridge
curriculum/l2-uk-en/folk/kalendarna-obriadovist-zvychai/module.md:57:1::::high-culture-bridge
curriculum/l2-uk-en/folk/kalendarna-obriadovist-zvychai/module.md:114:1::::myth-box
curriculum/l2-uk-en/folk/kalendarna-obriadovist-zvychai/module.md:123:1::::myth-box
curriculum/l2-uk-en/folk/narodna-kultura-yak-systema/module.md:65:1::::high-culture-bridge
curriculum/l2-uk-en/folk/narodna-kultura-yak-systema/module.md:80:1::::myth-box
curriculum/l2-uk-en/folk/narodni-viruvannia-mifolohiia-demonolohiia/module.md:93:1::::high-culture-bridge
curriculum/l2-uk-en/folk/narodni-viruvannia-mifolohiia-demonolohiia/module.md:108:1::::myth-box
curriculum/l2-uk-en/folk/narodni-viruvannia-mifolohiia-demonolohiia/module.md:117:1::::myth-box
curriculum/l2-uk-en/folk/zamovliannia-zaklynannia-prymovky/module.md:75:1::::high-culture-bridge
curriculum/l2-uk-en/folk/zamovliannia-zaklynannia-prymovky/module.md:90:1::::myth-box
```

Role-reading resource grep:

```text
curriculum/l2-uk-en/folk/koliadky-shchedrivky/resources.yaml:42:3:- title: '«Як ще не було початку світа»'
curriculum/l2-uk-en/folk/koliadky-shchedrivky/resources.yaml:43:3:  role: reading
curriculum/l2-uk-en/folk/koliadky-shchedrivky/resources.yaml:44:3:  url: /readings/koliadka-yak-shche-ne-bulo/
curriculum/l2-uk-en/folk/koliadky-shchedrivky/resources.yaml:46:3:- title: '«Ой сивая та і зозулечка»'
curriculum/l2-uk-en/folk/koliadky-shchedrivky/resources.yaml:47:3:  role: reading
curriculum/l2-uk-en/folk/koliadky-shchedrivky/resources.yaml:48:3:  url: /readings/shchedrivka-oi-syvaia-ta-i-zozulechka/
curriculum/l2-uk-en/folk/dumy-nevilnytski-lytsarski/resources.yaml:22:3:- title: 'Українські народні думи — повний збірник першоджерел'
curriculum/l2-uk-en/folk/dumy-nevilnytski-lytsarski/resources.yaml:23:3:  role: reading
curriculum/l2-uk-en/folk/dumy-nevilnytski-lytsarski/resources.yaml:24:3:  url: https://uk.wikisource.org/wiki/Українські_народні_думи
curriculum/l2-uk-en/folk/dumy-nevilnytski-lytsarski/resources.yaml:28:3:- title: 'Думи'
curriculum/l2-uk-en/folk/dumy-nevilnytski-lytsarski/resources.yaml:29:3:  role: reading
curriculum/l2-uk-en/folk/dumy-nevilnytski-lytsarski/resources.yaml:30:3:  url: https://uk.wikipedia.org/wiki/Думи
curriculum/l2-uk-en/folk/kalendarna-obriadovist-zvychai/resources.yaml:21:3:- title: 'Веснянки'
curriculum/l2-uk-en/folk/kalendarna-obriadovist-zvychai/resources.yaml:22:3:  role: reading
curriculum/l2-uk-en/folk/kalendarna-obriadovist-zvychai/resources.yaml:23:3:  url: https://uk.wikisource.org/wiki/Веснянки
curriculum/l2-uk-en/folk/narodna-kultura-yak-systema/resources.yaml:8:3:- title: 'Український фольклор'
curriculum/l2-uk-en/folk/narodna-kultura-yak-systema/resources.yaml:9:3:  role: reading
curriculum/l2-uk-en/folk/narodna-kultura-yak-systema/resources.yaml:10:3:  url: https://uk.wikipedia.org/wiki/Український_фольклор
curriculum/l2-uk-en/folk/narodni-viruvannia-mifolohiia-demonolohiia/resources.yaml:18:3:- title: 'Українська демонологія'
curriculum/l2-uk-en/folk/narodni-viruvannia-mifolohiia-demonolohiia/resources.yaml:19:3:  role: reading
curriculum/l2-uk-en/folk/narodni-viruvannia-mifolohiia-demonolohiia/resources.yaml:20:3:  url: https://uk.wikipedia.org/wiki/Українська_демонологія
curriculum/l2-uk-en/folk/zamovliannia-zaklynannia-prymovky/resources.yaml:17:3:- title: 'Замовляння'
curriculum/l2-uk-en/folk/zamovliannia-zaklynannia-prymovky/resources.yaml:18:3:  role: reading
curriculum/l2-uk-en/folk/zamovliannia-zaklynannia-prymovky/resources.yaml:19:3:  url: https://uk.wikipedia.org/wiki/Замовляння
```

### Mislabeled Scholarship Evidence

Raw `references:` lines:

```text
    98	references:
   103	- title: Історія української літератури
   104	  author: Чижевський Д.
   105	  note: Психологізм невільницьких дум, анонімність, три брати з Азова
   106	  type: primary
   107	  work: Історія української літератури
   108	- title: Слов'янська міфологія
   109	  author: Костомаров М.
   110	  note: Козацькі морські походи, зозуля та явір як символи, дівчина-бранка
   111	  type: primary
   112	  work: Слов'янська міфологія
   113	- title: Нарис історії культури України
   114	  author: Попович М.
   115	  note: Козацька героїка, набіги та работоргівля
   116	  type: primary
   117	  work: Нарис історії культури України
```

Justification: `Історія української літератури`, `Слов'янська міфологія`, and `Нарис історії культури України` are authored monograph/survey/analysis works, not primary folk texts. Correct type: `scholarly`.

### Corpus Evidence - `koliadky-shchedrivky`

Search excerpts:

```text
Found 20 results for: "Як ще не було початку світа Ой над Дунаєм Рано рано куроньки Ой сивая зозулечка Прилетіла зозуленька Щедрик щедрівочка"
- **Author**: Народна творчість
- **Source**: ukrlib-narod-dumy
- **Chunk ID**: `d4848a7e_c0000`
- **Text**:
ЩЕДРИК, ЩЕДРИК, ЩЕДРІВОЧКА
```

```text
- **Author**: Народна творчість
- **Source**: ukrlib-narod-dumy
- **Chunk ID**: `70435c0b_c0000`
- **Text**:
ОЙ СИВАЯ ТА І ЗОЗУЛЕЧКА
```

```text
- **Author**: Народна творчість
- **Source**: ukrlib-narod-dumy
- **Chunk ID**: `4e9a8170_c0000`
- **Text**:
РАНО, РАНО КУРОНЬКИ ПІЛИ
```

```text
- **Author**: Народна творчість
- **Source**: ukrlib-narod-dumy
- **Chunk ID**: `6be1cfdc_c0000`
- **Text**:
ПРИЛЕТІЛА ЗОЗУЛЕНЬКА
```

```text
- **Author**: Народна творчість
- **Source**: ukrlib-narod-dumy
- **Chunk ID**: `61bfde21_c0000`
- **Text**:
ЯК ЩЕ НЕ БУЛО ПОЧАТКУ СВІТА
```

```text
Found 5 results for: "Ой над Дунаєм над береженьком"
- **Author**: Народна творчість
- **Source**: ukrlib-narod-dumy
- **Chunk ID**: `672a677a_c0000`
- **Text**:
ОЙ НАД ДУНАЄМ, НАД БЕРЕЖЕНЬКОМ
```

Verifier excerpts:

```json
{"matched": true, "best_confidence": 1.0, "line": "ЯК ЩЕ НЕ БУЛО ПОЧАТКУ СВІТА", "work": "ukrlib-narod-dumy", "context_chunk_id": "61bfde21_c0000"}
{"matched": true, "best_confidence": 1.0, "line": "ОЙ НАД ДУНАЄМ, НАД БЕРЕЖЕНЬКОМ", "work": "ukrlib-narod-dumy", "context_chunk_id": "672a677a_c0000"}
{"matched": true, "best_confidence": 1.0, "line": "РАНО, РАНО КУРОНЬКИ ПІЛИ", "work": "ukrlib-narod-dumy", "context_chunk_id": "4e9a8170_c0000"}
{"matched": true, "best_confidence": 0.8442, "line": "ОЙ СИВАЯ ТА І ЗОЗУЛЕЧКА", "work": "ukrlib-narod-dumy", "context_chunk_id": "70435c0b_c0000"}
{"matched": true, "best_confidence": 1.0, "line": "ПРИЛЕТІЛА ЗОЗУЛЕНЬКА", "work": "ukrlib-narod-dumy", "context_chunk_id": "6be1cfdc_c0000"}
{"matched": true, "best_confidence": 1.0, "line": "ЩЕДРИК, ЩЕДРИК, ЩЕДРІВОЧКА", "work": "ukrlib-narod-dumy", "context_chunk_id": "d4848a7e_c0000"}
```

Negative verifier:

```json
{"matched": false, "best_confidence": 0.0, "matched_lines": [], "text_query": "у цьому дворку як у вінку"}
```

### Corpus Evidence - `dumy-nevilnytski-lytsarski`

Search excerpts:

```text
Found 20 results for: "Втеча трьох братів з Азова Гей не дивуйте добрії люди Зажурилась Україна Максим козак Залізняк Ой на горі да женці жнуть"
- **Author**: Народна творчість
- **Source**: ukrlib-narod-dumy
- **Chunk ID**: `8028b13a_c0000`
- **Text**:
ГЕЙ, НЕ ДИВУЙТЕ, ДОБРІЇ ЛЮДИ
```

```text
- **Author**: Народна творчість
- **Source**: ukrlib-narod-dumy
- **Chunk ID**: `d0c6550e_c0000`
- **Text**:
ОЙ НА ГОРІ ДА ЖЕНЦІ ЖНУТЬ
```

```text
- **Author**: Народна творчість
- **Source**: ukrlib-narod-dumy
- **Chunk ID**: `8d7b076e_c0000`
- **Text**:
ВТЕЧА ТРЬОХ БРАТІВ 3 АЗОВА, З ТУРЕЦЬКОЇ НЕВОЛІ
```

```text
Found 10 results for: "Зажурилась Україна що нігде прожити Максим козак Залізняк"
- **Author**: Народна творчість
- **Source**: ukrlib-narod-dumy
- **Chunk ID**: `1f7ae6ee_c0000`
- **Text**:
ЗАЖУРИЛАСЬ УКРАЇНА, БО НІЧИМ ПРОЖИТИ
```

```text
- **Author**: Народна творчість
- **Source**: ukrlib-narod-dumy
- **Chunk ID**: `83f36b8b_c0000`
- **Text**:
МАКСИМ КОЗАК ЗАЛІЗНЯК
```

Verifier excerpts:

```json
{"matched": true, "best_confidence": 0.9834, "line": "Ой то не пили то пилили,", "work": "ukrlib-narod-dumy", "context_chunk_id": "8d7b076e_c0000"}
{"matched": true, "best_confidence": 1.0, "line": "ГЕЙ, НЕ ДИВУЙТЕ, ДОБРІЇ ЛЮДИ", "work": "ukrlib-narod-dumy", "context_chunk_id": "8028b13a_c0000"}
{"matched": true, "best_confidence": 0.9865, "line": "ЗАЖУРИЛАСЬ УКРАЇНА, БО НІЧИМ ПРОЖИТИ", "work": "ukrlib-narod-dumy", "context_chunk_id": "1f7ae6ee_c0000"}
{"matched": true, "best_confidence": 1.0, "line": "МАКСИМ КОЗАК ЗАЛІЗНЯК", "work": "ukrlib-narod-dumy", "context_chunk_id": "83f36b8b_c0000"}
{"matched": true, "best_confidence": 1.0, "line": "ОЙ НА ГОРІ ДА ЖЕНЦІ ЖНУТЬ", "work": "ukrlib-narod-dumy", "context_chunk_id": "d0c6550e_c0000"}
```

Marusia search/negative verifier:

```text
Found 10 results for: "Дума про Марусю Богуславку Маруся Богуславка невольники"
- **Author**: Драгоманов М.
- **Source**: wave7-drahomanov-vybrani
- **Chunk ID**: `c846b4d3_c0041`
```

```json
{"matched": false, "best_confidence": 0.0, "matched_lines": [], "text_query": "що на чорному морі, на камені біленькому, там стояла темниця кам яная"}
```

### Corpus Evidence - `kalendarna-obriadovist-zvychai`

Search excerpts:

```text
Found 10 results for: "Ой весна весна ти красна Ой виорю я нивку широкую"
- **Author**: Народна творчість
- **Source**: ukrlib-narod-dumy
- **Chunk ID**: `cdffaaff_c0000`
- **Text**:
ОЙ ВИОРЮ Я НИВКУ ШИРОКУЮ
```

```text
- **Author**: Народна творчість
- **Source**: ukrlib-narod-dumy
- **Chunk ID**: `2df42ee0_c0000`
- **Text**:
ОЙ ВЕСНА, ВЕСНА, ТИ КРАСНА
```

```text
Found 10 results for: "Котився віночок по полю Сидить ведмідь на копі Жали женчики жали Нуте нуте до межі"
- **Author**: Народна творчість
- **Source**: ukrlib-narod-dumy
- **Chunk ID**: `d72aa98d_c0000`
- **Text**:
КОТИВСЯ ВІНОЧОК ПО ПОЛЮ
```

```text
- **Author**: Народна творчість
- **Source**: ukrlib-narod-dumy
- **Chunk ID**: `e025bb90_c0000`
- **Text**:
СИДИТЬ ВЕДМІДЬ НА КОПІ1
```

Verifier excerpts:

```json
{"matched": true, "best_confidence": 1.0, "line": "ОЙ ВЕСНА, ВЕСНА, ТИ КРАСНА", "work": "ukrlib-narod-dumy", "context_chunk_id": "2df42ee0_c0000"}
{"matched": true, "best_confidence": 1.0, "line": "ОЙ ВИОРЮ Я НИВКУ ШИРОКУЮ", "work": "ukrlib-narod-dumy", "context_chunk_id": "cdffaaff_c0000"}
{"matched": true, "best_confidence": 1.0, "line": "КОТИВСЯ ВІНОЧОК ПО ПОЛЮ", "work": "ukrlib-narod-dumy", "context_chunk_id": "d72aa98d_c0000"}
{"matched": true, "best_confidence": 1.0, "line": "СИДИТЬ ВЕДМІДЬ НА КОПІ1 Сидить ведмідь на копі, Дивується бороді2:", "work": "ukrlib-narod-dumy", "context_chunk_id": "e025bb90_c0000"}
```

Negative verifier:

```json
{"matched": false, "best_confidence": 0.5556, "context_chunk_id": "d72aa98d_c0000", "text_query": "жали женчики, жали"}
{"matched": false, "best_confidence": 0.0, "matched_lines": [], "text_query": "нуте, нуте, до межі, вареники у діжі"}
```

### Corpus Evidence - `narodna-kultura-yak-systema`

Search excerpt showing system/genre topic:

```text
search_sources("український фольклор народна творчість колядки думи веснянки жниварські пісні система жанрів")
"title": "ПІСЕННІ СКАРБИ РІДНОГО КРАЮ (p. 6)"
"text": "Пісні розрізняють за циклами з  огляду на пори року, коли виконували обряди. Народні обрядові пісні зимовий цикл весняний цикл літній цикл колядки щедрівки веснянки (гаївки) русальні купальські жниварські"
```

Cross-genre verified candidates from the same audit run:

```json
{"matched": true, "line": "ЩЕДРИК, ЩЕДРИК, ЩЕДРІВОЧКА", "work": "ukrlib-narod-dumy", "context_chunk_id": "d4848a7e_c0000"}
{"matched": true, "line": "Ой то не пили то пилили,", "work": "ukrlib-narod-dumy", "context_chunk_id": "8d7b076e_c0000"}
{"matched": true, "line": "ОЙ ВЕСНА, ВЕСНА, ТИ КРАСНА", "work": "ukrlib-narod-dumy", "context_chunk_id": "2df42ee0_c0000"}
{"matched": true, "line": "СИДИТЬ ВЕДМІДЬ НА КОПІ1 Сидить ведмідь на копі, Дивується бороді2:", "work": "ukrlib-narod-dumy", "context_chunk_id": "e025bb90_c0000"}
```

### Corpus Evidence - `narodni-viruvannia-mifolohiia-demonolohiia`

Search excerpts:

```text
Found 10 results for: "домовик водяник лісовик польовик русалка народна творчість демонологія"
### Result 1
- **Author**: Українка Л.
- **Source**: ukrlib-lesya
- **Chunk ID**: `06137f6e_c0000`
```

```text
### Result 2
- **Author**: Хоткевич Г.
- **Source**: ukrlib-khotkevych
- **Chunk ID**: `8a6de40c_c0075`
```

```text
### Result 7
- **Author**: Колектив
- **Source**: wave8-ukr-lit-entsyklopediia
- **Chunk ID**: `fc2291b5_c0794`
```

`search_sources` likewise returned wiki/textbook/literary/scholarly chunks, not standalone primary rows:

```text
"unit_key": "ukrainian_wiki:vesna-ta-lito:p9-9"
"source_type": "ukrainian_wiki"
"title": "Академічна C1: Весна та літо"
```

```text
"unit_key": "modern_literary:48346587_c0601"
"author": "Крип'якевич І."
"work": "Крип'якевич — Історія української культури (1937)"
```

Negative verifier:

```json
{"matched": false, "best_confidence": 0.0, "matched_lines": [], "text_query": "ух, ух! солом’янии дух! мене мати породила, нехрещену положила"}
```

### Corpus Evidence - `zamovliannia-zaklynannia-prymovky`

Search excerpt:

```text
search_sources("замовляння заклинання примовка Волос волос вийди на колос Я тебе виганяю український фольклор")
"unit_key": "modern_literary:feaa5fa7_c0589"
"author": "Колектив"
"work": "Енциклопедія українознавства"
"chunk_id": "feaa5fa7_c0589"
"text": "Волос, волос, вийди на колос"
```

Negative verifiers:

```json
{"matched": false, "best_confidence": 0.5, "line": "Ниво золота", "work": "ukrlib-narod-dumy", "context_chunk_id": "39b89ebc_c0000", "text_query": "волос, волос, вииди на колос"}
{"matched": false, "best_confidence": 0.0, "matched_lines": [], "text_query": "я тебе виганяю, виклинаю, проклинаю! иди пріч! та иди на ліси, на очерети, та на луги, та на пущі"}
```

## Recommended Remediation Batch Order

1. Metadata cleanup batch: retag the three duma scholarly references as `type: scholarly`; add curated `readings:` blocks for `koliadky-shchedrivky`, `dumy-nevilnytski-lytsarski`, `kalendarna-obriadovist-zvychai`, and `narodna-kultura-yak-systema`.
2. Hosted reading generation batch: create or update hosted readings for the verified public-domain `ukrlib-narod-dumy` rows, then wire plan, source module, resources, and built MDX links.
3. Rebuild/verification batch: regenerate affected modules with `:::primary-reading` blocks and run the track shippability/reading dry-run checks.
4. Source acquisition batch: find standalone public-domain primary folklore texts for `narodni-viruvannia-mifolohiia-demonolohiia` and `zamovliannia-zaklynannia-prymovky`; do not backfill from literary adaptations, encyclopedia prose, or modern textbooks.

## Expected Final Response

```text
FOLK preflight report: docs/audits/folk-preflight-readiness-built6-2026-06-21.md
Modules/plans inspected: 6 - koliadky-shchedrivky, dumy-nevilnytski-lytsarski, kalendarna-obriadovist-zvychai, narodna-kultura-yak-systema, narodni-viruvannia-mifolohiia-demonolohiia, zamovliannia-zaklynannia-prymovky
Reading coverage: hosted 3 currently surfaced / 19 verified hostable candidate slots; link-only 6 current external resources; excerpt-only 2 secondary-quoted snippets; omit 4 failed/non-primary candidates; needed 8 source-acquisition slots
Blockers: 7
Next production/remediation batches: metadata cleanup; hosted reading generation; rebuild/verification; source acquisition
Files changed: docs/audits/folk-preflight-readiness-built6-2026-06-21.md only
Forbidden artifacts included: no
swarm_used: true
swarm_label: helper
swarm_note: one read-only explorer summarized local plan/site/resource/activity evidence; main agent performed corpus verification, report writing, validation, commit, push, PR
```

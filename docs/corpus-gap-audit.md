# Corpus Gap Audit #4594

Date: 2026-07-06

Scope: deterministic gap audit over the read-only live corpus database at
`/Users/krisztiankoos/projects/learn-ukrainian/data/sources.db` and the curriculum
vocabulary files present in this worktree. This report is an evidence artifact, not an
acquisition approval. The consumer-driven acquisition queue is marked DRAFT because the
orchestrator makes the final ranking judgment.

Anti-fabrication note: every headline number below is backed by a command in
[Methods and raw evidence](#methods-and-raw-evidence). Dimensions that could not be
computed from present artifacts are marked NOT COMPUTED.

## Headline findings

The five content corpora currently total 188,053 chunks:

| Corpus | Chunks |
| --- |
| `literary_texts` | 137,723 |
| `textbooks` | 25,714 |
| `ukrainian_wiki` | 22,385 |
| `external_articles` | 1,205 |
| `wikipedia` | 1,026 |
| **Total** | **188,053** |

The corpus is strong for humanities grounding and weak for contemporary applied domains:

| Gap signal | Evidence |
| --- |
| School-textbook domain coverage is Ukrainian language, Ukrainian literature, and history-heavy. | `textbooks` maps to 11,334 Ukrainian-language chunks, 6,323 Ukrainian-literature chunks, and 6,120 history-of-Ukraine chunks; explicit STEM/business/law/professional source-token check returned 0 chunks. |
| Press/current-news grounding is absent by deterministic tags and source names. | `external_articles` rows with `register_tag` or `source_file` matching press/news returned 0 chunks. |
| Spontaneous contemporary conversation is absent by deterministic tags and source names. | `external_articles` rows with conversational/spontaneous/source-token evidence returned 0 chunks; the only conversational-adjacent mapped material is 556 scripted pedagogical chunks. |
| Folk primary material remains near-zero relative to the FOLK curriculum. | Standalone literary folk genres (`duma`, `carol`, `harvest_song`, `spring_song`, `historical_song`) total 35 chunks; sampled FOLK curriculum attestation is 165/200 exact FTS phrase hits and 24/200 PULS hits. |
| Advanced and specialized curriculum vocabulary is weaker than A-level vocabulary. | Sampled exact FTS attestation: A1 198/200, A2 196/200, B1 183/200, B2 169/200, BIO 19/24, FOLK 165/200. PULS exact-word coverage drops to B2 49/200, BIO 1/24, FOLK 24/200. |

## Domain coverage

### Textbooks by subject

Subject was derived from `textbooks.source_file` naming tokens. The mapping covers every
row in `textbooks`; the unmapped-row check returned 0.

| Source-file token rule | Subject | Chunks | Distinct source files |
| --- | --- | ---: |
| `%ukrmova%`, `%ukrajinska-mova%`, `%ukrainska-mova%`, `%ukrayinska-mova%`, `%bukvar%` | Ukrainian language | 11,334 | 49 |
| `%ukrlit%`, `%ukrajinska-literatura%` | Ukrainian literature | 6,323 | 16 |
| `%istori%`, `%istorij%`, `%istoria%`, `%istoriia%` | History of Ukraine | 6,120 | 16 |
| `anna-ohoiko-%` | Learner lexicon | 1,500 | 2 |
| `ulp-%lesson-notes` | Learner podcast notes | 240 | 6 |
| `antonenko-davydovych-%` | Style/usage guide | 169 | 1 |
| `pohribnyi-%` | Orthoepy/pronunciation | 28 | 1 |

The explicit non-humanities school-textbook source-token check for STEM, geography,
informatics, economics/business, law/professional labels returned 0 chunks.

### Literary texts by genre

`literary_texts` has 137,723 chunks across 229 source files and 32 genres.

| Genre | Chunks | Genre | Chunks |
| --- | ---: | --- |
| scholarly | 40,480 | letters | 1,175 |
| prose | 33,186 | legal | 1,022 |
| chronicle | 18,777 | diary | 939 |
| poetry | 14,184 | fable | 832 |
| encyclopedia | 11,459 | documents | 635 |
| philosophy | 2,954 | hagiography | 425 |
| polemic | 2,844 | religious | 379 |
| biography | 2,446 | travelogue | 335 |
| anthology | 1,624 | rhetoric | 316 |
| memoir | 1,442 | reference | 297 |
| drama | 1,183 | grammar | 242 |
| interlude | 172 | lexicon | 141 |
| manual | 141 | ethnography | 57 |
| historical_song | 12 | duma | 9 |
| carol | 7 | harvest_song | 4 |
| spring_song | 3 | letter | 1 |

Standalone folk-primary genres total 35 chunks.

### External articles

`external_articles` has 1,205 chunks. The deterministic source classification is:

| External class | Chunks | Source files |
| --- | ---: |
| history/language YouTube transcript | 644 | 4 |
| conversational scripted or lesson audio | 316 | 1 |
| pedagogical blog | 208 | 2 |
| encyclopedia | 26 | 1 |
| scripted pronunciation video | 6 | 1 |
| academic or language resource | 2 | 1 |
| unmapped external | 2 | 1 |
| literary | 1 | 1 |

The raw domain/register distribution shows no deterministic press domain:

| Domain | Register tag | Chunks |
| --- | --- |
| blank | blank | 960 |
| `ukrainianlessons.com` | blank | 164 |
| `opentext.ku.edu` | blank | 32 |
| `uk.wikipedia.org` | blank | 26 |
| `talkukrainian.com` | blank | 9 |
| `youtube.com` | scripted | 6 |
| `verba.school` | blank | 3 |
| `lcorp.ulif.org.ua` | blank | 2 |
| `youtube.com` | blank | 2 |
| `ukrlib.com.ua` | blank | 1 |

### Ukrainian wiki and cached Wikipedia

`ukrainian_wiki` has 22,385 chunks. Track distribution:

| Track | Chunks |
| --- |
| works | 5,276 |
| figures | 3,835 |
| periods | 3,200 |
| historiography | 3,160 |
| c1 | 2,175 |
| b2 | 1,394 |
| b1 | 1,383 |
| a2 | 739 |
| a1 | 598 |
| genres | 252 |
| ritual | 121 |
| prose | 80 |
| lyric | 50 |
| tradition | 46 |
| short-forms | 42 |
| ruthenian | 22 |
| oes | 12 |

`wikipedia` has 1,026 cached chunks. It has no domain/category column in the schema, so
topic-domain coverage for cached Wikipedia is NOT COMPUTED.

## Register coverage

Register mapping is deterministic over table, genre, source-file, and domain fields. It
does not infer social register from the prose itself.

Required-register summary:

| Required register | Count used in audit | Note |
| --- | ---: |
| school-textbook | 23,777 | Grade-bearing `textbooks` rows. |
| literary | 57,555 | Literary register bucket after genre/domain mapping. |
| encyclopedia/reference | 35,334 | Literary encyclopedia/reference/lexicon plus Ukrainian wiki, cached Wikipedia, and external wiki rows. |
| academic/scholarly | 49,527 | Scholarly/philosophy/polemic/legal/documents/rhetoric/grammar/manual/ethnography/religious/hagiography plus `opentext.ku.edu`. |
| press/current news | 0 | Deterministic press/news query over `external_articles.register_tag` and `source_file`. |
| spontaneous contemporary conversational | 0 | Deterministic conversational/spontaneous/source-token query over `external_articles`. |
| scripted pedagogical conversational-adjacent | 556 | ULP lesson notes and ULP YouTube rows; not spontaneous conversation. |

| Register bucket | Chunks |
| --- |
| literary | 57,555 |
| academic/scholarly | 49,527 |
| encyclopedia/reference | 35,334 |
| school textbook | 23,777 |
| historical primary | 18,777 |
| pedagogical reference | 1,676 |
| scripted public video, humanities | 644 |
| conversational scripted/pedagogical | 556 |
| usage reference | 205 |
| unmapped external | 2 |

Zero or near-zero register grounding:

- Press/current news: 0 chunks by `register_tag` or `source_file` press/news evidence.
- Spontaneous contemporary conversation: 0 chunks by conversational/spontaneous/source-token evidence.
- Contemporary applied professional/STEM school materials: 0 chunks by textbook source-token evidence.
- Standalone folk primaries: 35 chunks.

## CEFR and track vocabulary alignment

No existing content-lexicon reconciler output artifact was present in this worktree. The
only matching files were `scripts/lexicon/content_lexicon_reconciler.py` and
`tests/test_content_lexicon_reconciler.py`; those are the script and tests, not output.

Atlas coverage is NOT COMPUTED: `site/src/data/lexicon-manifest.json` is absent in this
worktree. `site/src/data/lexicon-manifest.pointer.json` and
`data/lexicon-dataset.pointer.json` are present, but pointer metadata does not contain
the lemma set needed for coverage.

Fallback method: deterministic sampled exact FTS alnum-token phrase attestation. For each
level/track with vocabulary files, vocabulary terms were normalized from `lemma` or
`word`, de-duplicated, sorted by stable SHA-256 sample key, and capped at sample_n=200
except BIO where the population is 24. Corpus attestation means an exact FTS alnum-token phrase
hit in any of `textbooks_fts`, `literary_fts`, `external_fts`, `ukrainian_wiki_fts`, or
`wikipedia_fts`. PULS coverage is exact `lower(word)=lower(term)` lookup in `puls_cefr`.
This is not lemmatized morphology coverage.

| Level/track | Vocabulary files | Entries | Unique terms | Sample n | Corpus attested | Corpus rate | PULS attested | PULS rate | Deterministic unattested examples |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A1 | 55 | 2,146 | 1,298 | 200 | 198 | 0.990 | 88 | 0.440 | мені каву, будь ласка; один кілограм яблук |
| A2 | 69 | 1,691 | 1,168 | 200 | 196 | 0.980 | 109 | 0.545 | казати / кажу; цим вечором; іменникова група; уважний / уважним |
| B1 | 94 | 4,080 | 2,867 | 200 | 183 | 0.915 | 72 | 0.360 | розставляти коми; негативна причина; аргумент до особи; присудкова модель; межа групи; умови оренди; служба газу; несуча конструкція |
| B2 | 93 | 3,149 | 2,266 | 200 | 169 | 0.845 | 49 | 0.245 | вкладене запитання; кількісний родовий; предикативний зв'язок; міжмовна асиметрія; дієслово введення чужого мовлення; пітч; юридична точність; метод мосту |
| BIO | 1 | 24 | 24 | 24 | 19 | 0.792 | 1 | 0.042 | радянський контекст; співаність; інституційна кар'єра; пісенний канон; велика форма |
| FOLK | 36 | 944 | 753 | 200 | 165 | 0.825 | 24 | 0.120 | склодувна трубка; вірш без сталої строфи; екзотизація; топонімічний переказ; таємна мова; кінь-вісник; восковий резерв; галицький запис |

Manifest levels/tracks with zero `vocabulary.yaml` files found are NOT COMPUTED for
this CEFR/track vocabulary table: C1, HIST, LIT, ISTORIO, C2, OES, RUTH,
LIT-ESSAY, LIT-HIST-FIC, LIT-FANTASTIKA, LIT-WAR, LIT-HUMOR, LIT-YOUTH, and
LIT-DRAMA.

## Consumer-driven acquisition queue - DRAFT

| Draft rank | Gap | Concrete consumer | Evidence line |
| ---: | --- | --- |
| 1 | Contemporary applied-domain school/professional sources: STEM, geography, informatics, economics/business, law, professional/technical prose. | Writer sourcing, reviewer grounding, Atlas, benchmark, Hramatka. | Textbook source-token check returned 0 chunks; B2 sample had 169/200 corpus hits and 49/200 PULS hits, with misses including `пітч` and `юридична точність`. |
| 2 | Press/current-news Ukrainian. | Reviewer grounding, writer sourcing, benchmark. | Press/news query over `external_articles.register_tag` and `source_file` returned 0 chunks; external domain/register distribution is YouTube/pedagogical/reference, not press. |
| 3 | Spontaneous contemporary conversational speech. | Hramatka, Atlas examples, benchmark. | Conversational/spontaneous/source-token query returned 0 chunks; mapped conversational-adjacent material is 556 scripted pedagogical chunks. |
| 4 | Standalone folk primary texts beyond the current narrow genres. | Reviewer grounding and writer sourcing for FOLK modules. | Standalone folk-primary literary genres total 35 chunks; FOLK sampled corpus attestation is 165/200 and PULS coverage is 24/200. |
| 5 | Specialized advanced vocabulary support for BIO and upper-level curriculum terms. | Atlas, benchmark, reviewer grounding. | BIO sampled corpus attestation is 19/24 and PULS coverage is 1/24; B2 sampled corpus attestation is 169/200 and PULS coverage is 49/200. |

## Final acquisition ranking — orchestrator judgment (2026-07-06)

This section is the binding gate output; the table above is the evidence draft it
was judged from. Rule applied: an active-consumer gap outranks a future-consumer
gap, and a gap already being closed by a live track epic is NOT an acquisition
item — it gets re-audited after that epic lands, not double-acquired.

| Rank | Item | Disposition |
| ---: | --- | --- |
| 1 | STEM/applied school textbooks | **EXECUTING** — approved acquisition #4593 (34 core books, wave 1 grades 5–9). Re-run this audit's domain queries after ingest to confirm the 0-chunk cell closes. |
| 2 | Press/current-news Ukrainian | **NEXT CANDIDATE, gated** — first genuinely NEW channel type; needs a license-posture decision at THIS gate (state/public broadcasters e.g. Суспільне first) before any proposal. Consumer weight rises when C1/C2 build starts (0 published today). |
| 3 | Spontaneous contemporary conversational | **PARKED** — primary consumer (Hramatka) is itself gated; hardest legitimate sourcing. Revisit when Hramatka ungates. |
| — | Folk primaries (draft rank 4) | **NOT AN ACQUISITION ITEM** — actively closing via the folk epic's reading expansion (batches C–E in flight). Re-audit after the epic lands; acquire only what still remains. |
| — | BIO/advanced vocabulary (draft rank 5) | **NOT AN ACQUISITION ITEM** — partially closed by #4593 rank 1 (STEM terminology) + the BIO epic's reading packets; BIO sample was n=24, too small to rank on. Re-audit post-ingest with a larger sample. |

Standing rule going forward: any corpus-expansion proposal must cite this report's
deterministic queries (re-run, not quoted) and name its consumer, per #4594.

## Methods and raw evidence

All commands below were run from:

```text
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/4594-corpus-gap-audit
```

The database was opened read-only via:

```text
sqlite3 'file:/Users/krisztiankoos/projects/learn-ukrainian/data/sources.db?mode=ro'
```

### Issue and worktree orientation

```bash
git status --short --branch
```

```text
## codex/4594-corpus-gap-audit...origin/main
```

```bash
gh issue view 4594
```

```text
title: [corpus] Deterministic corpus gap audit: register × domain × CEFR coverage vs curriculum needs
state: OPEN
number: 4594
```

### Content-corpus row counts

```bash
sqlite3 -header -column 'file:/Users/krisztiankoos/projects/learn-ukrainian/data/sources.db?mode=ro' "SELECT 'textbooks' AS corpus, COUNT(*) AS chunks FROM textbooks UNION ALL SELECT 'literary_texts', COUNT(*) FROM literary_texts UNION ALL SELECT 'external_articles', COUNT(*) FROM external_articles UNION ALL SELECT 'ukrainian_wiki', COUNT(*) FROM ukrainian_wiki UNION ALL SELECT 'wikipedia', COUNT(*) FROM wikipedia UNION ALL SELECT 'TOTAL_content_corpora', (SELECT COUNT(*) FROM textbooks)+(SELECT COUNT(*) FROM literary_texts)+(SELECT COUNT(*) FROM external_articles)+(SELECT COUNT(*) FROM ukrainian_wiki)+(SELECT COUNT(*) FROM wikipedia);"
```

```text
corpus                 chunks
---------------------  ------
textbooks              25714
literary_texts         137723
external_articles      1205
ukrainian_wiki         22385
wikipedia              1026
TOTAL_content_corpora  188053
```

### Textbook subject mapping

```bash
sqlite3 -header -column 'file:/Users/krisztiankoos/projects/learn-ukrainian/data/sources.db?mode=ro' "WITH mapped AS (SELECT CASE WHEN source_file LIKE '%istori%' OR source_file LIKE '%istorij%' OR source_file LIKE '%istoria%' OR source_file LIKE '%istoriia%' THEN 'history_of_ukraine' WHEN source_file LIKE '%ukrlit%' OR source_file LIKE '%ukrajinska-literatura%' THEN 'ukrainian_literature' WHEN source_file LIKE '%ukrmova%' OR source_file LIKE '%ukrajinska-mova%' OR source_file LIKE '%ukrainska-mova%' OR source_file LIKE '%ukrayinska-mova%' OR source_file LIKE '%bukvar%' THEN 'ukrainian_language' WHEN source_file LIKE 'anna-ohoiko-%' THEN 'learner_lexicon' WHEN source_file LIKE 'ulp-%lesson-notes' THEN 'learner_podcast_notes' WHEN source_file LIKE 'antonenko-davydovych-%' THEN 'style_usage_guide' WHEN source_file LIKE 'pohribnyi-%' THEN 'orthoepy_pronunciation' ELSE 'UNMAPPED' END AS subject, source_file FROM textbooks) SELECT subject, COUNT(*) AS chunks, COUNT(DISTINCT source_file) AS source_files FROM mapped GROUP BY subject ORDER BY chunks DESC, subject;"
```

```text
subject                 chunks  source_files
----------------------  ------  ------------
ukrainian_language      11334   49
ukrainian_literature    6323    16
history_of_ukraine      6120    16
learner_lexicon         1500    2
learner_podcast_notes   240     6
style_usage_guide       169     1
orthoepy_pronunciation  28      1
```

```bash
sqlite3 -header -column 'file:/Users/krisztiankoos/projects/learn-ukrainian/data/sources.db?mode=ro' "SELECT COUNT(*) AS rows FROM textbooks WHERE source_file NOT LIKE '%istori%' AND source_file NOT LIKE '%istorij%' AND source_file NOT LIKE '%istoria%' AND source_file NOT LIKE '%istoriia%' AND source_file NOT LIKE '%ukrlit%' AND source_file NOT LIKE '%ukrajinska-literatura%' AND source_file NOT LIKE '%ukrmova%' AND source_file NOT LIKE '%ukrajinska-mova%' AND source_file NOT LIKE '%ukrainska-mova%' AND source_file NOT LIKE '%ukrayinska-mova%' AND source_file NOT LIKE '%bukvar%' AND source_file NOT LIKE 'anna-ohoiko-%' AND source_file NOT LIKE 'ulp-%lesson-notes' AND source_file NOT LIKE 'antonenko-davydovych-%' AND source_file NOT LIKE 'pohribnyi-%';"
```

```text
rows
----
0
```

```bash
sqlite3 -header -column 'file:/Users/krisztiankoos/projects/learn-ukrainian/data/sources.db?mode=ro' "SELECT COUNT(*) AS chunks FROM textbooks WHERE source_file LIKE '%matem%' OR source_file LIKE '%math%' OR source_file LIKE '%fizy%' OR source_file LIKE '%physics%' OR source_file LIKE '%khim%' OR source_file LIKE '%chem%' OR source_file LIKE '%biol%' OR source_file LIKE '%geogr%' OR source_file LIKE '%informat%' OR source_file LIKE '%ekonom%' OR source_file LIKE '%econom%' OR source_file LIKE '%business%' OR source_file LIKE '%law%' OR source_file LIKE '%pravo%';"
```

```text
chunks
------
0
```

```bash
sqlite3 -header -column 'file:/Users/krisztiankoos/projects/learn-ukrainian/data/sources.db?mode=ro' "SELECT COUNT(*) AS chunks FROM textbooks WHERE grade <> '' AND source_file NOT LIKE '%ukrmova%' AND source_file NOT LIKE '%ukrajinska-mova%' AND source_file NOT LIKE '%ukrainska-mova%' AND source_file NOT LIKE '%ukrayinska-mova%' AND source_file NOT LIKE '%bukvar%' AND source_file NOT LIKE '%ukrlit%' AND source_file NOT LIKE '%ukrajinska-literatura%' AND source_file NOT LIKE '%istori%' AND source_file NOT LIKE '%istorij%' AND source_file NOT LIKE '%istoria%' AND source_file NOT LIKE '%istoriia%';"
```

```text
chunks
------
0
```

### Literary domain and genre coverage

```bash
sqlite3 -header -column 'file:/Users/krisztiankoos/projects/learn-ukrainian/data/sources.db?mode=ro' "SELECT COUNT(*) AS chunks, COUNT(DISTINCT source_file) AS source_files FROM literary_texts; SELECT COUNT(*) AS chunks, COUNT(DISTINCT genre) AS genres FROM literary_texts;"
```

```text
chunks  source_files
------  ------------
137723  229
chunks  genres
------  ------
137723  32
```

```bash
sqlite3 -header -column 'file:/Users/krisztiankoos/projects/learn-ukrainian/data/sources.db?mode=ro' "SELECT genre, COUNT(*) AS chunks FROM literary_texts GROUP BY genre ORDER BY chunks DESC, genre;"
```

```text
genre            chunks
---------------  ------
scholarly        40480
prose            33186
chronicle        18777
poetry           14184
encyclopedia     11459
philosophy       2954
polemic          2844
biography        2446
anthology        1624
memoir           1442
drama            1183
letters          1175
legal            1022
diary            939
fable            832
documents        635
hagiography      425
religious        379
travelogue       335
rhetoric         316
reference        297
grammar          242
interlude        172
lexicon          141
manual           141
ethnography      57
historical_song  12
duma             9
carol            7
harvest_song     4
spring_song      3
letter           1
```

```bash
sqlite3 -header -column 'file:/Users/krisztiankoos/projects/learn-ukrainian/data/sources.db?mode=ro' "SELECT COUNT(*) AS chunks FROM literary_texts WHERE genre IN ('duma','carol','harvest_song','spring_song','historical_song');"
```

```text
chunks
------
35
```

### External domain coverage

```bash
sqlite3 -header -column 'file:/Users/krisztiankoos/projects/learn-ukrainian/data/sources.db?mode=ro' "SELECT domain, register_tag, COUNT(*) AS chunks, COUNT(DISTINCT source_file) AS source_files, MIN(source_file) AS sample_source FROM external_articles GROUP BY domain, register_tag ORDER BY chunks DESC, domain, register_tag;"
```

```text
domain                register_tag  chunks  source_files  sample_source
--------------------  ------------  ------  ------------  -----------------------
                                    960     5             imtgsh
ukrainianlessons.com                164     1             ulp_blogs
opentext.ku.edu                     32      1             other_blogs
uk.wikipedia.org                    26      1             other_blogs
talkukrainian.com                   9       1             other_blogs
youtube.com           scripted      6       1             pohribnyi_pronunciation
verba.school                        3       1             other_blogs
lcorp.ulif.org.ua                   2       1             other_blogs
youtube.com                         2       1             other_blogs
ukrlib.com.ua                       1       1             other_blogs
```

```bash
sqlite3 -header -column 'file:/Users/krisztiankoos/projects/learn-ukrainian/data/sources.db?mode=ro' "SELECT CASE WHEN source_file='ulp_youtube' THEN 'conversational_scripted_or_lesson_audio' WHEN source_file IN ('imtgsh','realna_istoria','istoria_movy','komik_istoryk') THEN 'history_language_youtube_transcript' WHEN source_file='ulp_blogs' OR domain IN ('ukrainianlessons.com','talkukrainian.com','verba.school','opentext.ku.edu') THEN 'pedagogical_blog' WHEN domain='uk.wikipedia.org' THEN 'encyclopedia' WHEN domain='lcorp.ulif.org.ua' THEN 'academic_or_language_resource' WHEN domain='ukrlib.com.ua' THEN 'literary' WHEN register_tag='scripted' THEN 'scripted_pronunciation_video' ELSE 'unmapped_external' END AS external_class, COUNT(*) AS chunks, COUNT(DISTINCT source_file) AS source_files FROM external_articles GROUP BY external_class ORDER BY chunks DESC, external_class;"
```

```text
external_class                           chunks  source_files
---------------------------------------  ------  ------------
history_language_youtube_transcript      644     4
conversational_scripted_or_lesson_audio  316     1
pedagogical_blog                         208     2
encyclopedia                             26      1
scripted_pronunciation_video             6       1
academic_or_language_resource            2       1
unmapped_external                        2       1
literary                                 1       1
```

### Ukrainian wiki and Wikipedia coverage

```bash
sqlite3 -header -column 'file:/Users/krisztiankoos/projects/learn-ukrainian/data/sources.db?mode=ro' "SELECT track, COUNT(*) AS chunks FROM ukrainian_wiki GROUP BY track ORDER BY chunks DESC, track;"
```

```text
track           chunks
--------------  ------
works           5276
figures         3835
periods         3200
historiography  3160
c1              2175
b2              1394
b1              1383
a2              739
a1              598
genres          252
ritual          121
prose           80
lyric           50
tradition       46
short-forms     42
ruthenian       22
oes             12
```

```bash
sqlite3 -header -column 'file:/Users/krisztiankoos/projects/learn-ukrainian/data/sources.db?mode=ro' "SELECT COUNT(*) AS chunks FROM wikipedia;"
```

```text
chunks
------
1026
```

### Register mapping

```bash
sqlite3 -header -column 'file:/Users/krisztiankoos/projects/learn-ukrainian/data/sources.db?mode=ro' "WITH register_rows AS (SELECT CASE WHEN grade <> '' THEN 'school_textbook' WHEN source_file LIKE 'ulp-%lesson-notes' THEN 'conversational_scripted_pedagogical' WHEN source_file LIKE 'anna-ohoiko-%' THEN 'pedagogical_reference' WHEN source_file LIKE 'antonenko-davydovych-%' OR source_file LIKE 'pohribnyi-%' THEN 'usage_reference' ELSE 'UNMAPPED_TEXTBOOKS' END AS register, COUNT(*) AS chunks FROM textbooks GROUP BY register UNION ALL SELECT CASE WHEN genre IN ('prose','poetry','drama','fable','anthology','memoir','diary','letters','letter','travelogue','biography','interlude','duma','carol','harvest_song','spring_song','historical_song') THEN 'literary' WHEN genre IN ('encyclopedia','reference','lexicon') THEN 'encyclopedia_reference' WHEN genre IN ('scholarly','philosophy','polemic','legal','documents','rhetoric','grammar','manual','ethnography','religious','hagiography') THEN 'academic_scholarly' WHEN genre='chronicle' THEN 'historical_primary' ELSE 'UNMAPPED_LITERARY' END AS register, COUNT(*) AS chunks FROM literary_texts GROUP BY register UNION ALL SELECT CASE WHEN source_file='ulp_youtube' THEN 'conversational_scripted_pedagogical' WHEN source_file IN ('imtgsh','realna_istoria','istoria_movy','komik_istoryk') THEN 'scripted_public_video_humanities' WHEN source_file='ulp_blogs' OR domain IN ('ukrainianlessons.com','talkukrainian.com','verba.school') THEN 'pedagogical_reference' WHEN domain='opentext.ku.edu' THEN 'academic_scholarly' WHEN domain='uk.wikipedia.org' THEN 'encyclopedia_reference' WHEN domain='lcorp.ulif.org.ua' THEN 'usage_reference' WHEN domain='ukrlib.com.ua' THEN 'literary' WHEN register_tag='scripted' THEN 'usage_reference' ELSE 'UNMAPPED_EXTERNAL' END AS register, COUNT(*) AS chunks FROM external_articles GROUP BY register UNION ALL SELECT 'encyclopedia_reference' AS register, COUNT(*) AS chunks FROM ukrainian_wiki UNION ALL SELECT 'encyclopedia_reference' AS register, COUNT(*) AS chunks FROM wikipedia) SELECT register, SUM(chunks) AS chunks FROM register_rows GROUP BY register ORDER BY chunks DESC, register;"
```

```text
register                             chunks
-----------------------------------  ------
literary                             57555
academic_scholarly                   49527
encyclopedia_reference               35334
school_textbook                      23777
historical_primary                   18777
pedagogical_reference                1676
scripted_public_video_humanities     644
conversational_scripted_pedagogical  556
usage_reference                      205
UNMAPPED_EXTERNAL                    2
```

```bash
sqlite3 -header -column 'file:/Users/krisztiankoos/projects/learn-ukrainian/data/sources.db?mode=ro' "SELECT COUNT(*) AS chunks FROM external_articles WHERE lower(register_tag)='press' OR lower(register_tag)='news' OR lower(source_file) LIKE '%press%' OR lower(source_file) LIKE '%news%';"
```

```text
chunks
------
0
```

```bash
sqlite3 -header -column 'file:/Users/krisztiankoos/projects/learn-ukrainian/data/sources.db?mode=ro' "SELECT COUNT(*) AS chunks FROM external_articles WHERE lower(register_tag)='conversational' OR lower(register_tag)='conversation' OR lower(register_tag)='spontaneous' OR lower(source_file) LIKE '%conversation%' OR lower(source_file) LIKE '%spoken%' OR lower(source_file) LIKE '%dialog%';"
```

```text
chunks
------
0
```

### Curriculum vocabulary files and reconciler-output absence

```bash
find curriculum/l2-uk-en -mindepth 2 -maxdepth 3 -name 'vocabulary.yaml' -print | awk -F/ '{print $3}' | sort | uniq -c
```

```text
     55 a1
     69 a2
     94 b1
     93 b2
      1 bio
     36 folk
```

```bash
find curriculum/l2-uk-en -maxdepth 3 -name 'vocabulary.yaml' | sort | wc -l
```

```text
348
```

```bash
find . -iname '*lexicon*reconc*' -o -iname '*reconc*lexicon*' -o -iname '*content*reconc*' | sort
```

```text
./scripts/lexicon/content_lexicon_reconciler.py
./tests/test_content_lexicon_reconciler.py
```

```bash
find . -iname '*lexicon*reconc*' -o -iname '*reconc*lexicon*' -o -iname '*content*reconc*' | sort | wc -l
```

```text
2
```

```bash
.venv/bin/python - <<'PY'
import json
from pathlib import Path
for p in [Path('site/src/data/lexicon-manifest.json'), Path('site/src/data/lexicon-manifest.pointer.json'), Path('data/lexicon-dataset.pointer.json')]:
    print(p, p.exists(), p.stat().st_size if p.exists() else 'NA')
    if p.exists() and p.suffix == '.json':
        try:
            data=json.loads(p.read_text())
            print('keys', sorted(data)[:10])
        except Exception as e:
            print(type(e).__name__, e)
PY
```

```text
site/src/data/lexicon-manifest.json False NA
site/src/data/lexicon-manifest.pointer.json True 720
keys ['asset_url', 'fingerprint_schema_version', 'generated_at', 'gz_bytes', 'gz_sha256', 'json_bytes', 'json_sha256', 'manifest_fingerprint', 'manifest_version', 'note']
data/lexicon-dataset.pointer.json True 6516
keys ['asset_url', 'file_count', 'files', 'generated_at', 'gz_bytes', 'gz_sha256', 'manifest_stats', 'manifest_version', 'note', 'package_bytes']
```

```bash
sqlite3 -header -column 'file:/Users/krisztiankoos/projects/learn-ukrainian/data/sources.db?mode=ro' "SELECT level, COUNT(*) AS rows, COUNT(DISTINCT word) AS words FROM puls_cefr GROUP BY level ORDER BY level;"
```

```text
level  rows  words
-----  ----  -----
A1     962   947
A2     1386  1371
B1     2164  2153
B2     1194  1193
C1     233   233
```

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
import yaml
root=Path('curriculum/l2-uk-en')
manifest=yaml.safe_load((root/'curriculum.yaml').read_text(encoding='utf-8'))
for level in manifest['levels']:
    count=len(list((root/level).glob('*/vocabulary.yaml')))
    print(f'{level}\t{count}')
PY
```

```text
a1 55
a2 69
b1 94
b2 93
c1 0
hist 0
bio 1
lit 0
istorio 0
c2 0
oes 0
ruth 0
lit-essay 0
lit-hist-fic 0
lit-fantastika 0
lit-war 0
lit-humor 0
lit-youth 0
lit-drama 0
folk 36
```

### Sampled curriculum vocabulary attestation

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
from collections import defaultdict
import hashlib
import re
import sqlite3
import unicodedata
import yaml

DB='file:/Users/krisztiankoos/projects/learn-ukrainian/data/sources.db?mode=ro'
ROOT=Path('curriculum/l2-uk-en')
SAMPLE_LIMIT=200
STRESS_RE=re.compile('[\u0300\u0301]')
TRANS=str.maketrans({'ʼ':"'", '’':"'", '`':"'", '′':"'", '‐':'-', '‑':'-'})

def norm(s):
    s=unicodedata.normalize('NFC', str(s)).translate(TRANS).casefold().strip()
    s=STRESS_RE.sub('', s)
    return re.sub(r'\s+', ' ', s)

def token_pieces(term):
    pieces=[]
    current=[]
    for ch in norm(term):
        if ch.isalnum():
            current.append(ch)
        elif current:
            pieces.append(''.join(current))
            current=[]
    if current:
        pieces.append(''.join(current))
    return pieces

def fts_query(term):
    tokens=token_pieces(term)
    if not tokens:
        return None
    return '"' + ' '.join(t.replace('"', '""') for t in tokens) + '"'

terms=defaultdict(set)
entry_counts=defaultdict(int)
file_counts={}
for level_dir in sorted(p for p in ROOT.iterdir() if p.is_dir()):
    vocab_files=sorted(level_dir.glob('*/vocabulary.yaml'))
    if vocab_files:
        file_counts[level_dir.name]=len(vocab_files)
    for path in vocab_files:
        data=yaml.safe_load(path.read_text(encoding='utf-8'))
        if not isinstance(data, list):
            continue
        for item in data:
            if not isinstance(item, dict):
                continue
            value=item.get('lemma') or item.get('word')
            if isinstance(value, str) and value.strip():
                entry_counts[level_dir.name]+=1
                terms[level_dir.name].add(norm(value))

conn=sqlite3.connect(DB, uri=True)
content_checks=[
    ('textbooks_fts', 'textbooks_fts'),
    ('literary_fts', 'literary_fts'),
    ('external_fts', 'external_fts'),
    ('ukrainian_wiki_fts', 'ukrainian_wiki_fts'),
    ('wikipedia_fts', 'wikipedia_fts'),
]

def in_corpus(term):
    q=fts_query(term)
    if not q:
        return False
    for table, match_name in content_checks:
        if conn.execute(f'SELECT 1 FROM {table} WHERE {match_name} MATCH ? LIMIT 1', (q,)).fetchone():
            return True
    return False

def in_puls(term):
    return conn.execute('SELECT 1 FROM puls_cefr WHERE lower(word)=lower(?) LIMIT 1', (term,)).fetchone() is not None

print('method: stable_sha256_sample_lowest; sample_limit=200; corpus_match=FTS alnum token phrase across textbooks,literary,external,ukrainian_wiki,wikipedia; puls_match=lower(word)=lower(term)')
print('level vocab_files entries unique_terms sample_n corpus_attested corpus_rate puls_attested puls_rate unattested_examples')
for level in sorted(terms):
    population=sorted(terms[level])
    sample=sorted(population, key=lambda term: hashlib.sha256(f'{level}\0{term}'.encode('utf-8')).hexdigest())[:min(SAMPLE_LIMIT, len(population))]
    corpus_hits=[]
    puls_hits=[]
    misses=[]
    for term in sample:
        c=in_corpus(term)
        p=in_puls(term)
        if c:
            corpus_hits.append(term)
        else:
            misses.append(term)
        if p:
            puls_hits.append(term)
    n=len(sample)
    examples=', '.join(misses[:8]) if misses else 'NONE'
    print(f'{level} {file_counts.get(level,0)} {entry_counts[level]} {len(population)} {n} {len(corpus_hits)} {len(corpus_hits)/n:.3f} {len(puls_hits)} {len(puls_hits)/n:.3f} {examples}')
PY
```

```text
method: stable_sha256_sample_lowest; sample_limit=200; corpus_match=FTS alnum token phrase across textbooks,literary,external,ukrainian_wiki,wikipedia; puls_match=lower(word)=lower(term)
level vocab_files entries unique_terms sample_n corpus_attested corpus_rate puls_attested puls_rate unattested_examples
a1 55 2146 1298 200 198 0.990 88 0.440 мені каву, будь ласка, один кілограм яблук
a2 69 1691 1168 200 196 0.980 109 0.545 казати / кажу, цим вечором, іменникова група, уважний / уважним
b1 94 4080 2867 200 183 0.915 72 0.360 розставляти коми, негативна причина, аргумент до особи, присудкова модель, межа групи, умови оренди, служба газу, несуча конструкція
b2 93 3149 2266 200 169 0.845 49 0.245 вкладене запитання, кількісний родовий, предикативний зв'язок, міжмовна асиметрія, дієслово введення чужого мовлення, пітч, юридична точність, метод мосту
bio 1 24 24 24 19 0.792 1 0.042 радянський контекст, співаність, інституційна кар'єра, пісенний канон, велика форма
folk 36 944 753 200 165 0.825 24 0.120 склодувна трубка, вірш без сталої строфи, екзотизація, топонімічний переказ, таємна мова, кінь-вісник, восковий резерв, галицький запис
```

## Post-batch-3 re-run — gap closure verified (2026-07-07, #4593)

Re-ran the headline queries after the batch-3 ingest (47 books / 15,544 chunks, PRs
#4667/#4671/#4675). Deterministic, `mode=ro`, live `data/sources.db`:

### Content-corpus row counts

| corpus | chunks (2026-07-06 audit) | chunks (2026-07-07) |
|---|---:|---:|
| textbooks | 35,389 | **50,933** |
| literary_texts | 137,723 | 137,723 |
| external_articles | 1,205 | 1,205 |
| ukrainian_wiki | 22,385 | 22,385 |
| wikipedia | 1,026 | 1,026 |

### STEM / applied-register cell (the audit's headline "0-chunk" finding)

STEM-pattern chunks (query §"STEM presence", extended with algebra/heometr/fizik/himi
translit stems): 0 (pre-wave-1) → 5,334 (post-wave-1) → **14,400** (post-batch-3).

### Authoritative subject census (subject column, 25 subjects, 0 UNMAPPED)

zarlit 2,348 · heohrafiya 2,340 · informatyka 2,009 · fizyka 1,964 · vsesvitnia 1,678 ·
algebra 1,564 · mystetstvo 1,532 · matematyka 1,430 · biolohiya 1,408 · khimiya 1,387 ·
heometriya 1,223 · zakhyst 1,126 · pravoznavstvo 1,104 · ekonomika 961 · zdorovia 910 ·
pryroda 764 · hromadianska 656 · etyka 384 · finansova 226 · astronomiya 205
(core: ukrmova 10,940 · ukrlit 6,323 · istoriya 6,120 · lexicon 1,937 · bukvar 394).

**Register balance shift:** subject-register Ukrainian now exceeds core-language chunks
(31,339 vs 19,594) — the diversification this audit's ranking called for is delivered.
Consumers unblocked at the new scale: Atlas grounding (fresh reconciler baseline 15,880
missing lemmas / 416 files, attestable against the widened corpus), reviewer grounding,
practice decks, benchmark domain coverage.

**Cells still open:** grade-9 2026 pryroda/zdorovia/finansova/pravoznavstvo (view-only
Drive, wave-3b watch) · wave-1b scans (4 books) · wave-2 10-11 scanned leftovers ·
geography stretch (#4594-gated) · press/conversational registers (parked per ranking §
"Final acquisition ranking").

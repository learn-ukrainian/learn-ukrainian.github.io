# FOLK Reading Coverage Map

Report version: 0.1
Date: 2026-06-21
Auditor: Codex
Worktree: `/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/folk-coverage-map`
Scope: all 42 FOLK plans in `curriculum/l2-uk-en/plans/folk/*.yaml`
Read-only: true for curriculum, site, plan, research, corpus, and source files
Durable report path: `docs/audits/folk-reading-coverage-map-2026-06-21.md`
Only content write: this report
swarm_used: true
swarm_label: helper
swarm_note: three read-only explorer helpers summarized plan clusters, existing built/hosted reading surfaces, and public-domain acquisition source families; Codex verified corpus rows and wrote this report.

## Scope And Method

Inspected source files:

- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`
- `docs/prompts/orchestrators/folk/preflight-readiness-audit-orchestrator.md`
- `docs/prompts/orchestrators/shared/repo-rules.md`
- `docs/prompts/orchestrators/shared/validation-checklist.md`
- `docs/prompts/orchestrators/shared/review-output-schema.md`
- `docs/prompts/orchestrators/shared/seminar-source-rules.md`
- `docs/prompts/orchestrators/shared/reading-section-rules.md`
- `docs/folk-epic/EXEMPLAR-STANDARD.md`
- `docs/folk-epic/folk-review-rubric.md`
- `docs/folk-epic/folk-text-layer-spec.md`
- `scripts/build/phases/linear-write-seminar-folk-rules.md`
- `site/src/content.config.ts`
- `scripts/readings/generate_readings.py`
- `curriculum/l2-uk-en/curriculum.yaml`
- `curriculum/l2-uk-en/plans/folk/*.yaml`
- `docs/research/folk/*.md`
- built module directories under `curriculum/l2-uk-en/folk/`
- hosted readings under `site/src/content/readings/*.mdx`
- local read-only corpus database `data/sources.db`

Classification rules:

- `HOSTED`: already present under `site/src/content/readings/`.
- `IN-CORPUS`: `mcp__sources__verify_quote` returned `matched=true` under the required collector-author. The source cell carries the raw verifier line: `matched`, `best_confidence`, `work`, and `context_chunk_id`.
- `NEEDS-FETCH`: not hosted and not proven by a successful required-author verifier call during this run. This is a batch acquisition work item, not a claim that the text does not circulate elsewhere.

Verifier boundary notes:

- Correct-author checks used `author="Народна творчість"` for `ukrlib-narod-dumy` and `author="Драгоманов М."` for `wave7-drahomanov-vybrani`.
- Representative false or unusable checks: `verify_quote(author="Народна творчість", text="Волос, волос, вийди на колос") -> matched=false; best_confidence=0.5; context_chunk_id=39b89ebc_c0000`; `verify_quote(author="Народна творчість", text="Поле не міряне, вівці не лічені, пастух рогатий") -> matched=false; best_confidence=0.0`; `verify_quote(author="Народна творчість", text="Ой ходить сон коло вікон, а дрімота коло плота") -> matched=false; best_confidence=0.5`; `verify_quote(author="Народна творчість", text="Ой не ходи, Грицю, та й на вечорниці") -> matched=false; best_confidence=0.0`.
- Local SQLite showed some `ukrlib-narod-dumy` rows that the verifier did not confirm at threshold, so they are not classified `IN-CORPUS`: `У цьому дворку як у вінку` (`matched=false`), `Жали женчики, жали` (`matched=false; best_confidence=0.5556` on retry), `Нуте, нуте, до межі` (`matched=false`), and `Ой на горі да женці жнуть` (`matched=false; best_confidence=0.7671`).
- `Ой у лузі червона калина` produced a single-line match to an unrelated `ukrlib-narod-dumy` row (`context_chunk_id=1b55083a_c0000`), so it is not treated as in-corpus.

## §A Per-Module Matrix

| # | Module | Genre cluster | Needed primary texts | Breakdown |
| --- | --- | --- | --- | --- |
| 1 | `narodna-kultura-yak-systema` | system / genre overview | T002, T027, T035, T025 | 1 hosted / 1 in-corpus / 2 needs-fetch |
| 2 | `narodni-viruvannia-mifolohiia-demonolohiia` | beliefs / demonology | T031, T032, T033, T034 | 0 hosted / 0 in-corpus / 4 needs-fetch |
| 3 | `zamovliannia-zaklynannia-prymovky` | charms / verbal magic | T027, T028, T029, T030 | 0 hosted / 0 in-corpus / 4 needs-fetch |
| 4 | `kalendarna-obriadovist-zvychai` | calendar rite overview | T002, T008, T010, T011 | 1 hosted / 3 in-corpus / 0 needs-fetch |
| 5 | `koliadky-shchedrivky` | winter calendar songs | T002, T003, T004, T005, T006, T007 | 3 hosted / 3 in-corpus / 0 needs-fetch |
| 6 | `vesnianky-hayivky` | spring songs / games | T008, T009, T039, T040 | 0 hosted / 2 in-corpus / 2 needs-fetch |
| 7 | `kupalski-rusalni-pisni` | Kupalo / Rusalka songs | T041, T042, T043, T044 | 0 hosted / 0 in-corpus / 4 needs-fetch |
| 8 | `zhnyvarski-obzhynkovi-pisni` | harvest / obzhynky songs | T010, T011, T045, T046 | 0 hosted / 2 in-corpus / 2 needs-fetch |
| 9 | `rodynna-obriadovist-zvychai` | family rite overview | T047, T048, T051, T112 | 0 hosted / 0 in-corpus / 4 needs-fetch |
| 10 | `vesilni-pisni` | wedding songs | T047, T048, T049, T050 | 0 hosted / 0 in-corpus / 4 needs-fetch |
| 11 | `holosinnya` | laments | T051, T052, T053, T054 | 0 hosted / 0 in-corpus / 4 needs-fetch |
| 12 | `dumy-nevilnytski-lytsarski` | captivity / heroic dumas | T001, T025, T026, T021 | 1 hosted / 3 in-corpus / 0 needs-fetch |
| 13 | `dumy-sotsialno-pobutovi` | social-domestic dumas | T055, T056, T057, T058 | 0 hosted / 0 in-corpus / 4 needs-fetch |
| 14 | `kobzarstvo-lirnytstvo` | kobzar / lirnyk performance | T001, T025, T026, T059 | 1 hosted / 2 in-corpus / 1 needs-fetch |
| 15 | `bylyny-kyivskoho-tsyklu` | Kyivan byliny / contested epic | T060, T061, T062, T063 | 0 hosted / 0 in-corpus / 4 needs-fetch |
| 16 | `istorychni-pisni` | historical songs | T012, T013, T014, T015, T016, T017, T018, T019, T020 | 0 hosted / 9 in-corpus / 0 needs-fetch |
| 17 | `striletski-povstanski-pisni` | rifle / insurgent songs | T024, T064, T065, T066, T067 | 0 hosted / 1 in-corpus / 4 needs-fetch |
| 18 | `rodynno-pobutovi-pisni` | family / intimate lyric | T068, T069, T070, T071 | 0 hosted / 0 in-corpus / 4 needs-fetch |
| 19 | `kolomyiky` | kolomyiky / short songs | T022, T072, T073, T074 | 0 hosted / 1 in-corpus / 3 needs-fetch |
| 20 | `suspilno-pobutovi-pisni` | social songs / chumak-burlak | T023, T075, T076, T017 | 0 hosted / 2 in-corpus / 2 needs-fetch |
| 21 | `narodni-balady` | ballads / narrative songs | T069, T077, T078, T079 | 0 hosted / 0 in-corpus / 4 needs-fetch |
| 22 | `pisni-literaturnoho-pokhodzhennia` | songs of literary origin | T080, T081, T082, T083 | 0 hosted / 0 in-corpus / 4 needs-fetch |
| 23 | `charivni-kazky` | magic tales | T084, T085, T060, T086, T087 | 0 hosted / 0 in-corpus / 5 needs-fetch |
| 24 | `kazky-pro-tvaryn` | animal tales | T088, T089, T090, T091 | 0 hosted / 0 in-corpus / 4 needs-fetch |
| 25 | `sotsialno-pobutovi-kazky` | realistic / social tales | T092, T093, T094, T095 | 0 hosted / 0 in-corpus / 4 needs-fetch |
| 26 | `narodni-lehendy` | legends / popular Christianity | T096, T097, T098, T099 | 0 hosted / 0 in-corpus / 4 needs-fetch |
| 27 | `istorychni-perekazy` | historical oral memory | T060, T100, T101, T102 | 0 hosted / 0 in-corpus / 4 needs-fetch |
| 28 | `narodni-opovidannia-buvalshchyny-memoraty` | memorates / buvalshchyny | T031, T032, T033, T103 | 0 hosted / 0 in-corpus / 4 needs-fetch |
| 29 | `prykazky-ta-pryslivia` | proverbs / sayings | T104, T105, T106, T107 | 0 hosted / 0 in-corpus / 4 needs-fetch |
| 30 | `zahadky` | riddles | T035, T036, T037, T038 | 0 hosted / 0 in-corpus / 4 needs-fetch |
| 31 | `narodni-anekdoty` | anecdotes / tall tales | T108, T109, T110, T111 | 0 hosted / 0 in-corpus / 4 needs-fetch |
| 32 | `dytiachyi-folklor-kolyskovi` | child folklore / lullabies | T112, T113, T114, T115 | 0 hosted / 0 in-corpus / 4 needs-fetch |
| 33 | `vertep-narodna-drama` | vertep / folk drama | T116, T117, T118, T119 | 0 hosted / 0 in-corpus / 4 needs-fetch |
| 34 | `narodni-muzychni-instrumenty` | instruments / performance texts | T001, T025, T026, T016 | 1 hosted / 3 in-corpus / 0 needs-fetch |
| 35 | `narodni-tantsi` | dance texts / dance songs | T120, T121, T122, T123 | 0 hosted / 0 in-corpus / 4 needs-fetch |
| 36 | `pysankarstvo` | egg-symbol text layer | T003, T037, T009, T124 | 1 hosted / 1 in-corpus / 2 needs-fetch |
| 37 | `narodna-vyshyvka-rushnyk-strii` | textile / rushnyk texts | T047, T005, T050, T127 | 0 hosted / 1 in-corpus / 3 needs-fetch |
| 38 | `narodni-remesla-ta-khudozhni-promysly` | craft lore | T005, T125, T126, T127 | 0 hosted / 1 in-corpus / 3 needs-fetch |
| 39 | `narodne-zhytlo-sadyba-hospodarstvo` | house / homestead lore | T003, T006, T031, T128 | 1 hosted / 1 in-corpus / 2 needs-fetch |
| 40 | `narodna-kukhnia-obriadova-yizha` | ritual food | T047, T114, T046, T129 | 0 hosted / 0 in-corpus / 4 needs-fetch |
| 41 | `rehionalni-etnokulturni-tradytsii` | regional traditions | T002, T022, T130, T131 | 1 hosted / 1 in-corpus / 2 needs-fetch |
| 42 | `narodna-kultura-ta-vysoka-kultura-mistky` | folk / high-culture bridges | T004, T069, T016, T132 | 1 hosted / 1 in-corpus / 2 needs-fetch |

## §B Deduplicated Text Catalog

| ID | Primary text | Status | Source / raw verifier line | Modules served |
| --- | --- | --- | --- | --- |
| T001 | `Дума про Марусю Богуславку` | HOSTED | `site/src/content/readings/duma-marusia-bohuslavka.mdx` | `dumy-nevilnytski-lytsarski`, `kobzarstvo-lirnytstvo`, `narodni-muzychni-instrumenty` |
| T002 | `Як ще не було початку світа` | HOSTED | `site/src/content/readings/koliadka-yak-shche-ne-bulo.mdx` | `narodna-kultura-yak-systema`, `kalendarna-obriadovist-zvychai`, `koliadky-shchedrivky`, `rehionalni-etnokulturni-tradytsii` |
| T003 | `Ой сивая та і зозулечка` | HOSTED | `site/src/content/readings/shchedrivka-oi-syvaia-ta-i-zozulechka.mdx` | `koliadky-shchedrivky`, `pysankarstvo`, `narodne-zhytlo-sadyba-hospodarstvo` |
| T004 | `Щедрик, щедрик, щедрівочка` | HOSTED | `site/src/content/readings/shchedrivka-shchedryk-lastivochka.mdx` | `koliadky-shchedrivky`, `narodna-kultura-ta-vysoka-kultura-mistky` |
| T005 | `Ой над Дунаєм, над береженьком` | IN-CORPUS | raw `verify_quote(author="Народна творчість")`: `matched=true; best_confidence=1.0; work=ukrlib-narod-dumy; context_chunk_id=672a677a_c0000` | `koliadky-shchedrivky`, `narodna-vyshyvka-rushnyk-strii`, `narodni-remesla-ta-khudozhni-promysly` |
| T006 | `Рано, рано куроньки піли` | IN-CORPUS | raw `verify_quote(author="Народна творчість")`: `matched=true; best_confidence=0.98; work=ukrlib-narod-dumy; context_chunk_id=4e9a8170_c0000` | `koliadky-shchedrivky`, `narodne-zhytlo-sadyba-hospodarstvo` |
| T007 | `Прилетіла зозуленька` | IN-CORPUS | raw `verify_quote(author="Народна творчість")`: `matched=true; best_confidence=0.987; work=ukrlib-narod-dumy; context_chunk_id=6be1cfdc_c0000` | `koliadky-shchedrivky` |
| T008 | `Ой весна, весна, ти красна` | IN-CORPUS | raw `verify_quote(author="Народна творчість")`: `matched=true; best_confidence=0.9818; work=ukrlib-narod-dumy; context_chunk_id=2df42ee0_c0000` | `kalendarna-obriadovist-zvychai`, `vesnianky-hayivky` |
| T009 | `Ой виорю я нивку широкую` | IN-CORPUS | raw `verify_quote(author="Народна творчість")`: `matched=true; best_confidence=1.0; work=ukrlib-narod-dumy; context_chunk_id=cdffaaff_c0000` | `vesnianky-hayivky`, `pysankarstvo` |
| T010 | `Котився віночок по полю` | IN-CORPUS | raw `verify_quote(author="Народна творчість")`: `matched=true; best_confidence=0.9804; work=ukrlib-narod-dumy; context_chunk_id=d72aa98d_c0000` | `kalendarna-obriadovist-zvychai`, `zhnyvarski-obzhynkovi-pisni` |
| T011 | `Сидить ведмідь на копі` | IN-CORPUS | raw `verify_quote(author="Народна творчість")`: `matched=true; best_confidence=0.9242; work=ukrlib-narod-dumy; context_chunk_id=e025bb90_c0000` | `kalendarna-obriadovist-zvychai`, `zhnyvarski-obzhynkovi-pisni` |
| T012 | `Зажурилась Україна` | IN-CORPUS | raw `verify_quote(author="Народна творчість")`: `matched=true; best_confidence=0.9722; work=ukrlib-narod-dumy; context_chunk_id=1f7ae6ee_c0000` | `istorychni-pisni` |
| T013 | `Ой Морозе, Морозенку` | IN-CORPUS | raw `verify_quote(author="Народна творчість")`: `matched=true; best_confidence=0.9634; work=ukrlib-narod-dumy; context_chunk_id=208e8198_c0000` | `istorychni-pisni` |
| T014 | `Ой ти, Морозенку` | IN-CORPUS | raw `verify_quote(author="Народна творчість")`: `matched=true; best_confidence=0.9615; work=ukrlib-narod-dumy; context_chunk_id=92231b56_c0000` | `istorychni-pisni` |
| T015 | `Ой на горі вогонь горить` | IN-CORPUS | raw `verify_quote(author="Народна творчість")`: `matched=true; best_confidence=0.9714; work=ukrlib-narod-dumy; context_chunk_id=1d9e690e_c0000` | `istorychni-pisni` |
| T016 | `Пісня про Байду` | IN-CORPUS | raw `verify_quote(author="Народна творчість")`: `matched=true; best_confidence=1.0; work=ukrlib-narod-dumy; context_chunk_id=40beaaff_c0000` | `istorychni-pisni`, `narodni-muzychni-instrumenty`, `narodna-kultura-ta-vysoka-kultura-mistky` |
| T017 | `За Сибіром сонце сходить` | IN-CORPUS | raw `verify_quote(author="Народна творчість")`: `matched=true; best_confidence=0.9756; work=ukrlib-narod-dumy; context_chunk_id=ff912500_c0000` | `istorychni-pisni`, `suspilno-pobutovi-pisni` |
| T018 | `Розлилися круті бережечки` | IN-CORPUS | raw `verify_quote(author="Народна творчість")`: `matched=true; best_confidence=0.9737; work=ukrlib-narod-dumy; context_chunk_id=1b55083a_c0000` | `istorychni-pisni` |
| T019 | `Максим козак Залізняк` | IN-CORPUS | raw `verify_quote(author="Народна творчість")`: `matched=true; best_confidence=0.9467; work=ukrlib-narod-dumy; context_chunk_id=83f36b8b_c0000` | `istorychni-pisni` |
| T020 | `Гей, не дивуйте, добрії люди` | IN-CORPUS | raw `verify_quote(author="Народна творчість")`: `matched=true; best_confidence=0.9747; work=ukrlib-narod-dumy; context_chunk_id=8028b13a_c0000` | `istorychni-pisni` |
| T021 | `Втеча трьох братів з Азова` | IN-CORPUS | raw `verify_quote(author="Народна творчість")`: `matched=true; best_confidence=0.9419; work=ukrlib-narod-dumy; context_chunk_id=8d7b076e_c0000` | `dumy-nevilnytski-lytsarski` |
| T022 | `Коломийки` | IN-CORPUS | raw `verify_quote(author="Народна творчість")`: `matched=true; best_confidence=0.9427; work=ukrlib-narod-dumy; context_chunk_id=ae13494d_c0000` | `kolomyiky`, `rehionalni-etnokulturni-tradytsii` |
| T023 | `Ой ти, ниво моя, ниво` | IN-CORPUS | raw `verify_quote(author="Народна творчість")`: `matched=true; best_confidence=0.9706; work=ukrlib-narod-dumy; context_chunk_id=39b89ebc_c0000` | `suspilno-pobutovi-pisni` |
| T024 | `Єднаймось, брати-українці` | IN-CORPUS | raw `verify_quote(author="Народна творчість")`: `matched=true; best_confidence=0.9747; work=ukrlib-narod-dumy; context_chunk_id=6a91808f_c0000` | `striletski-povstanski-pisni` |
| T025 | `Плач невольників` | IN-CORPUS | raw `verify_quote(author="Драгоманов М.")`: `matched=true; best_confidence=0.9829; work=wave7-drahomanov-vybrani; context_chunk_id=c846b4d3_c0210` | `narodna-kultura-yak-systema`, `dumy-nevilnytski-lytsarski`, `kobzarstvo-lirnytstvo`, `narodni-muzychni-instrumenty` |
| T026 | `Дума про Самійла Кішку` | IN-CORPUS | raw `verify_quote(author="Драгоманов М.")`: `matched=true; best_confidence=0.9794; work=wave7-drahomanov-vybrani; context_chunk_id=c846b4d3_c0224`; second checked line `matched=true; best_confidence=0.9697; context_chunk_id=c846b4d3_c0226` | `dumy-nevilnytski-lytsarski`, `kobzarstvo-lirnytstvo`, `narodni-muzychni-instrumenty` |
| T027 | `Волос, волос, вийди на колос` | NEEDS-FETCH | Єфименко, `Збірник малоросійських заклинань`, 1874; Chubynskyi vol. 1 fallback | `narodna-kultura-yak-systema`, `zamovliannia-zaklynannia-prymovky` |
| T028 | `Я тебе виганяю, виклинаю, проклинаю` | NEEDS-FETCH | Єфименко 1874 or Chubynskyi vol. 1 charms | `zamovliannia-zaklynannia-prymovky` |
| T029 | `Як тобі жаль своїх очей...` | NEEDS-FETCH | Єфименко 1874 charms | `zamovliannia-zaklynannia-prymovky` |
| T030 | `Добрий вечір, сливочки...` | NEEDS-FETCH | Єфименко 1874 charms / plant-address formula | `zamovliannia-zaklynannia-prymovky` |
| T031 | `Про домовика / хованця` | NEEDS-FETCH | Гнатюк, `Знадоби до української демонології`, 1912 | `narodni-viruvannia-mifolohiia-demonolohiia`, `narodni-opovidannia-buvalshchyny-memoraty`, `narodne-zhytlo-sadyba-hospodarstvo` |
| T032 | `Бувальщина про відьму` | NEEDS-FETCH | Гнатюк 1912; Chubynskyi vol. 1 beliefs fallback | `narodni-viruvannia-mifolohiia-demonolohiia`, `narodni-opovidannia-buvalshchyny-memoraty` |
| T033 | `Меморат про русалку` | NEEDS-FETCH | Гнатюк 1912; Chubynskyi vol. 1 beliefs fallback | `narodni-viruvannia-mifolohiia-demonolohiia`, `narodni-opovidannia-buvalshchyny-memoraty` |
| T034 | `Переказ про чугайстра` | NEEDS-FETCH | Гнатюк 1912 demonology / Carpathian memorates | `narodni-viruvannia-mifolohiia-demonolohiia` |
| T035 | `Поле не міряне, вівці не лічені, пастух рогатий` | NEEDS-FETCH | Chubynskyi vol. 1 riddles; Sementovskyi 1851 fallback | `narodna-kultura-yak-systema`, `zahadky` |
| T036 | `Біле поле, чорне насіння, хто його сіє, той розуміє` | NEEDS-FETCH | Chubynskyi vol. 1 riddles | `zahadky` |
| T037 | `За лісом, за перелісом золота діжа горить` | NEEDS-FETCH | Chubynskyi vol. 1 riddles | `zahadky`, `pysankarstvo` |
| T038 | `На вогні мокне, а на воді сохне` | NEEDS-FETCH | Chubynskyi vol. 1 riddles | `zahadky` |
| T039 | `Вже весна воскресла` | NEEDS-FETCH | Chubynskyi calendar songs; Hnatiuk spring-song fallback | `vesnianky-hayivky` |
| T040 | `Кривого танця йдемо` | NEEDS-FETCH | Chubynskyi spring games / Hnatiuk regional spring songs | `vesnianky-hayivky` |
| T041 | `Ой на Івана, ой на Купала` | NEEDS-FETCH | Chubynskyi calendar songs; `ukrlib.com.ua/narod` if clean page resolves | `kupalski-rusalni-pisni` |
| T042 | `Заплету віночок...` | NEEDS-FETCH | Chubynskyi Kupalo songs | `kupalski-rusalni-pisni` |
| T043 | `Русалка по полю ходила` | NEEDS-FETCH | Chubynskyi Rusalka songs / Hnatiuk demonology fallback | `kupalski-rusalni-pisni` |
| T044 | `Проведу я русалочки...` | NEEDS-FETCH | Chubynskyi Rusalka sendoff songs | `kupalski-rusalni-pisni` |
| T045 | `Жали женчики, жали` | NEEDS-FETCH | `ukrlib.com.ua/narod` harvest page or Chubynskyi harvest songs; local verifier did not confirm | `zhnyvarski-obzhynkovi-pisni` |
| T046 | `Нуте, нуте, до межі` | NEEDS-FETCH | `ukrlib.com.ua/narod` harvest page or Chubynskyi harvest songs; local verifier did not confirm | `zhnyvarski-obzhynkovi-pisni`, `narodna-kukhnia-obriadova-yizha` |
| T047 | `Сходися, родоньку, сходися в купоньку` | NEEDS-FETCH | Chubynskyi wedding songs | `rodynna-obriadovist-zvychai`, `vesilni-pisni`, `narodna-vyshyvka-rushnyk-strii`, `narodna-kukhnia-obriadova-yizha` |
| T048 | `Ой сій, мати, овес...` | NEEDS-FETCH | Chubynskyi wedding songs | `rodynna-obriadovist-zvychai`, `vesilni-pisni` |
| T049 | `У неділю рано синє море грало` | NEEDS-FETCH | Chubynskyi wedding songs | `vesilni-pisni` |
| T050 | `Встаньте, бояри... будем замки ламати` | NEEDS-FETCH | Chubynskyi wedding songs | `vesilni-pisni`, `narodna-vyshyvka-rushnyk-strii` |
| T051 | `Синочку, синочку, Іваночку` | NEEDS-FETCH | Hnatiuk funeral customs / laments; Hrushevsky 1920 excerpt fallback | `rodynna-obriadovist-zvychai`, `holosinnya` |
| T052 | `Тут то твоє місце порожне` | NEEDS-FETCH | Hnatiuk funeral customs / laments | `holosinnya` |
| T053 | `Мій синочку -- мій голубчику` | NEEDS-FETCH | Hnatiuk funeral customs / laments | `holosinnya` |
| T054 | `Чоловіче мій, дружино моя` | NEEDS-FETCH | Hnatiuk funeral customs / laments | `holosinnya` |
| T055 | `Дума про вдову і трьох синів` | NEEDS-FETCH | `uk.wikisource.org` duma pages; `Українські народні думи` collection | `dumy-sotsialno-pobutovi` |
| T056 | `Дума про сестру та брата` | NEEDS-FETCH | `uk.wikisource.org` duma pages; `Українські народні думи` collection | `dumy-sotsialno-pobutovi` |
| T057 | `Дума про Ганжу Андибера` | NEEDS-FETCH | `uk.wikisource.org` duma pages; `Українські народні думи` collection | `dumy-sotsialno-pobutovi` |
| T058 | `Дума про Олексія Поповича / буря на Чорному морі` | NEEDS-FETCH | `uk.wikisource.org` duma pages; `Українські народні думи` collection | `dumy-sotsialno-pobutovi` |
| T059 | `Козак Голота` | NEEDS-FETCH | `uk.wikisource.org` duma pages or `ukrlib.com.ua/narod`; current corpus evidence is scholarly-quoted, not clean standalone | `kobzarstvo-lirnytstvo` |
| T060 | `Кирило Кожум'яка` | NEEDS-FETCH | Drahomanov, `Малорусские народные предания и рассказы`, 1876; Kulish `Записки о Южной Руси` fallback | `bylyny-kyivskoho-tsyklu`, `charivni-kazky`, `istorychni-perekazy` |
| T061 | `Ілля Муромець і князь Володимир` | NEEDS-FETCH | `uk.wikisource.org` / byliny collection; linked-only with decolonization framing | `bylyny-kyivskoho-tsyklu` |
| T062 | `Добриня і змій` | NEEDS-FETCH | `uk.wikisource.org` / byliny collection; linked-only with decolonization framing | `bylyny-kyivskoho-tsyklu` |
| T063 | `Михайло Потик` | NEEDS-FETCH | `uk.wikisource.org` / byliny collection; linked-only with decolonization framing | `bylyny-kyivskoho-tsyklu` |
| T064 | `Ой у лузі червона калина` | NEEDS-FETCH | `uk.wikisource.org`; rights/attribution review before hosting | `striletski-povstanski-pisni` |
| T065 | `Ой видно село` | NEEDS-FETCH | `uk.wikisource.org`; Bagrіanyi witness is literary context, not standalone folk row | `striletski-povstanski-pisni` |
| T066 | `Чуєш, брате мій` | NEEDS-FETCH | `uk.wikisource.org`; author/rights review before hosting | `striletski-povstanski-pisni` |
| T067 | `Лента за лентою` | NEEDS-FETCH | `uk.wikisource.org` or linked-only rights review; post-1925 risk likely | `striletski-povstanski-pisni` |
| T068 | `Цвіте терен` | NEEDS-FETCH | Chubynskyi / `ukrlib.com.ua/narod` family lyric page | `rodynno-pobutovi-pisni` |
| T069 | `Ой не ходи, Грицю` | NEEDS-FETCH | Chubynskyi / `ukrlib.com.ua/narod` ballad page | `rodynno-pobutovi-pisni`, `narodni-balady`, `narodna-kultura-ta-vysoka-kultura-mistky` |
| T070 | `Летіла зозуля` | NEEDS-FETCH | Chubynskyi family lyric / lament-adjacent songs | `rodynno-pobutovi-pisni` |
| T071 | `Ой у полі криниченька` | NEEDS-FETCH | Chubynskyi family/social lyric | `rodynno-pobutovi-pisni` |
| T072 | `Коломийка про рекрутчину` | NEEDS-FETCH | Hnatiuk, `Коломийки`, 1905-1907 | `kolomyiky` |
| T073 | `Коломийка про кохання` | NEEDS-FETCH | Hnatiuk, `Коломийки`, 1905-1907 | `kolomyiky` |
| T074 | `Коломийка про заробітки` | NEEDS-FETCH | Hnatiuk, `Коломийки`, 1905-1907 | `kolomyiky` |
| T075 | `Ой ішов чумак з Дону` | NEEDS-FETCH | Chubynskyi social songs / `ukrlib.com.ua/narod` if clean page resolves | `suspilno-pobutovi-pisni` |
| T076 | `Та нема в світі гірш нікому...` | NEEDS-FETCH | Chubynskyi burlak / hired-labor songs | `suspilno-pobutovi-pisni` |
| T077 | `Бондарівна` | NEEDS-FETCH | Chubynskyi / `ukrlib.com.ua/narod` ballads | `narodni-balady` |
| T078 | `Ой чиє ж то жито...` | NEEDS-FETCH | Chubynskyi / `ukrlib.com.ua/narod` ballads | `narodni-balady` |
| T079 | `Лимерівна` | NEEDS-FETCH | Chubynskyi / `ukrlib.com.ua/narod` ballads | `narodni-balady` |
| T080 | `Реве та стогне Дніпр широкий` | NEEDS-FETCH | `uk.wikisource.org` Shevchenko text; literary-origin song, not folk-authored | `pisni-literaturnoho-pokhodzhennia` |
| T081 | `Дивлюсь я на небо` | NEEDS-FETCH | `uk.wikisource.org` / PD authored text | `pisni-literaturnoho-pokhodzhennia` |
| T082 | `Повій, вітре, на Вкраїну` | NEEDS-FETCH | `uk.wikisource.org` / PD authored text | `pisni-literaturnoho-pokhodzhennia` |
| T083 | `Стоїть гора високая` | NEEDS-FETCH | `uk.wikisource.org` / PD authored text | `pisni-literaturnoho-pokhodzhennia` |
| T084 | `Івасик-Телесик` | NEEDS-FETCH | Rudchenko 1869-1870 or Drahomanov 1876 tale collections | `charivni-kazky` |
| T085 | `Котигорошко` | NEEDS-FETCH | Rudchenko 1869-1870 or Drahomanov 1876 tale collections | `charivni-kazky` |
| T086 | `Царівна-жаба` | NEEDS-FETCH | Rudchenko 1869-1870 or Drahomanov 1876 tale collections | `charivni-kazky` |
| T087 | `Летючий корабель` | NEEDS-FETCH | Rudchenko 1869-1870 or Drahomanov 1876 tale collections | `charivni-kazky` |
| T088 | `Рукавичка` | NEEDS-FETCH | Rudchenko / Drahomanov animal-tale collections | `kazky-pro-tvaryn` |
| T089 | `Коза-дереза` | NEEDS-FETCH | Rudchenko / Drahomanov animal-tale collections | `kazky-pro-tvaryn` |
| T090 | `Лисичка-сестричка і вовк-панібрат` | NEEDS-FETCH | Rudchenko / Drahomanov animal-tale collections | `kazky-pro-tvaryn` |
| T091 | `Пан Коцький` | NEEDS-FETCH | Rudchenko / Drahomanov animal-tale collections | `kazky-pro-tvaryn` |
| T092 | `Мудра дівчина` | NEEDS-FETCH | Drahomanov 1876 / Rudchenko social tale collections | `sotsialno-pobutovi-kazky` |
| T093 | `Про правду і кривду` | NEEDS-FETCH | Drahomanov 1876 / Rudchenko social tale collections | `sotsialno-pobutovi-kazky` |
| T094 | `Наймит і пан` | NEEDS-FETCH | Drahomanov 1876 / Chubynskyi social prose fallback | `sotsialno-pobutovi-kazky` |
| T095 | `Бідний чоловік і цар` | NEEDS-FETCH | Drahomanov 1876 / Rudchenko social tale collections | `sotsialno-pobutovi-kazky` |
| T096 | `Про створення світу` | NEEDS-FETCH | Drahomanov 1876 legends / Hnatiuk legend collections | `narodni-lehendy` |
| T097 | `Про святого Миколая` | NEEDS-FETCH | Drahomanov 1876 / Hnatiuk popular-Christian legends | `narodni-lehendy` |
| T098 | `Про Божу Матір і жнива` | NEEDS-FETCH | Drahomanov 1876 / Hnatiuk popular-Christian legends | `narodni-lehendy` |
| T099 | `Про грішну душу` | NEEDS-FETCH | Drahomanov 1876 / Hnatiuk popular-Christian legends | `narodni-lehendy` |
| T100 | `Переказ про Савур-могилу` | NEEDS-FETCH | Antonovych-Drahomanov historical songs/predaniya; `uk.wikisource.org` fallback | `istorychni-perekazy` |
| T101 | `Переказ про Хмельницького` | NEEDS-FETCH | Antonovych-Drahomanov historical materials | `istorychni-perekazy` |
| T102 | `Переказ про Кармалюка` | NEEDS-FETCH | Drahomanov / Hnatiuk historical-memory collections | `istorychni-perekazy` |
| T103 | `Про чорта на дорозі` | NEEDS-FETCH | Hnatiuk 1912 demonological memorates | `narodni-opovidannia-buvalshchyny-memoraty` |
| T104 | `Без верби і калини нема України` | NEEDS-FETCH | Chubynskyi / Franko proverb collections; verify before use | `prykazky-ta-pryslivia` |
| T105 | `Який батько, такий син` | NEEDS-FETCH | Chubynskyi / Franko proverb collections | `prykazky-ta-pryslivia` |
| T106 | `Не копай другому ями...` | NEEDS-FETCH | Chubynskyi / Franko proverb collections | `prykazky-ta-pryslivia` |
| T107 | `Хліб усьому голова` | NEEDS-FETCH | Chubynskyi / Franko proverb collections; check Soviet-filter risk | `prykazky-ta-pryslivia` |
| T108 | `Небилиця про дурня і пана` | NEEDS-FETCH | Hnatiuk / Chubynskyi anecdote and tall-tale collections | `narodni-anekdoty` |
| T109 | `Пан і селянин` | NEEDS-FETCH | Hnatiuk / Chubynskyi anecdote collections | `narodni-anekdoty` |
| T110 | `Небилиця про те, як баба воли пасла` | NEEDS-FETCH | Hnatiuk / Chubynskyi tall-tale collections | `narodni-anekdoty` |
| T111 | `Жарт про кмітливого селянина` | NEEDS-FETCH | Hnatiuk / Chubynskyi anecdote collections; avoid xenonym jokes unless explicitly taught with harm framing | `narodni-anekdoty` |
| T112 | `Ой ходить сон коло вікон` | NEEDS-FETCH | Chubynskyi / Miloradovych child folklore and lullaby collections | `rodynna-obriadovist-zvychai`, `dytiachyi-folklor-kolyskovi` |
| T113 | `Котику сіренький` | NEEDS-FETCH | Chubynskyi / Miloradovych lullabies | `dytiachyi-folklor-kolyskovi` |
| T114 | `Еники-беники їли вареники` | NEEDS-FETCH | Chubynskyi / Hnatiuk child folklore; standalone row needed | `dytiachyi-folklor-kolyskovi`, `narodna-kukhnia-obriadova-yizha` |
| T115 | `Раз, два, три - коника бери` | NEEDS-FETCH | Chubynskyi / Hnatiuk child folklore | `dytiachyi-folklor-kolyskovi` |
| T116 | `Вертеп: Цар Ірод` | NEEDS-FETCH | `uk.wikisource.org` vertep drama pages | `vertep-narodna-drama` |
| T117 | `Вертеп: Козак / Запорожець` | NEEDS-FETCH | `uk.wikisource.org` vertep drama pages | `vertep-narodna-drama` |
| T118 | `Вертеп: Пастухи й ангели` | NEEDS-FETCH | `uk.wikisource.org` vertep drama pages | `vertep-narodna-drama` |
| T119 | `Вертеп: Чорт і Смерть` | NEEDS-FETCH | `uk.wikisource.org` vertep drama pages | `vertep-narodna-drama` |
| T120 | `Кривий танець` | NEEDS-FETCH | Chubynskyi / Hnatiuk spring dance-song records | `narodni-tantsi` |
| T121 | `Шум` | NEEDS-FETCH | Chubynskyi / Hnatiuk dance-song records | `narodni-tantsi` |
| T122 | `Метелиця` | NEEDS-FETCH | Chubynskyi / Hnatiuk dance-song records | `narodni-tantsi` |
| T123 | `Аркан` | NEEDS-FETCH | Hnatiuk / regional dance-song records | `narodni-tantsi` |
| T124 | `Писанкова коломийка` | NEEDS-FETCH | Hnatiuk / Chubynskyi regional short-song records | `pysankarstvo` |
| T125 | `Гончарська коломийка` | NEEDS-FETCH | Hnatiuk / Chubynskyi craft short-song records | `narodni-remesla-ta-khudozhni-promysly` |
| T126 | `Ковальський переказ` | NEEDS-FETCH | Hnatiuk / Chubynskyi craft memorates | `narodni-remesla-ta-khudozhni-promysly` |
| T127 | `Ткацька загадка` | NEEDS-FETCH | Chubynskyi riddles / Hnatiuk craft lore | `narodna-vyshyvka-rushnyk-strii`, `narodni-remesla-ta-khudozhni-promysly` |
| T128 | `Хата скраю` | NEEDS-FETCH | Chubynskyi / Franko proverb collections | `narodne-zhytlo-sadyba-hospodarstvo` |
| T129 | `На щастя, на здоров'я... жито, пшеницю і всяку пашницю` | NEEDS-FETCH | Chubynskyi winter formulas or Єфименко blessing formulas | `narodna-kukhnia-obriadova-yizha` |
| T130 | `Гуцульська коляда з березою` | NEEDS-FETCH | Chubynskyi / Hnatiuk regional winter-rite records | `rehionalni-etnokulturni-tradytsii` |
| T131 | `Лемківська або бойківська колискова` | NEEDS-FETCH | Hnatiuk / regional child folklore collections | `rehionalni-etnokulturni-tradytsii` |
| T132 | `Наталка Полтавка: Віють вітри / пісенний пласт` | NEEDS-FETCH | `uk.wikisource.org` or `litopys.org.ua` Kotliarevsky text; use as high-culture bridge, not folk-authored row | `narodna-kultura-ta-vysoka-kultura-mistky` |

## §C Acquisition List

Only `NEEDS-FETCH` rows appear here. The list is deduplicated: if a text serves several modules, fetch it once and wire every served module after verification.

### Chubynskyi 1872, `Труды этнографическо-статистической экспедиции`, vol. 1 and ritual-song volumes

Acquire: T035, T036, T037, T038, T039, T040, T041, T042, T043, T044, T047, T048, T049, T050, T068, T069, T070, T071, T075, T076, T077, T078, T079, T104, T105, T106, T107, T112, T113, T114, T115, T127, T128.

Batch note: this is the largest single source family. Pull riddles/proverbs/charms from vol. 1 first, then calendar, wedding, family lyric, social-song, ballad, and child-folklore volumes.

### Hnatiuk And NTSh Folk Collections, 1902-1912

Acquire: T031, T032, T033, T034, T051, T052, T053, T054, T072, T073, T074, T103, T108, T109, T110, T111, T120, T121, T122, T123, T124, T125, T126, T130, T131.

Batch note: use Hnatiuk `Знадоби до української демонології` (1912) for demonology and memorates; `Галицько-руські народні легенди` (1902-1903) for legends; `Коломийки` (1905-1907) for regional short songs; and Hnatiuk/NTSh regional collections for dance/craft/child texts.

### Drahomanov 1876, Rudchenko 1869-1870, And Historical Predaniya

Acquire: T060, T084, T085, T086, T087, T088, T089, T090, T091, T092, T093, T094, T095, T096, T097, T098, T099, T100, T101, T102.

Batch note: use Drahomanov `Малорусские народные предания и рассказы` (Kyiv, 1876) for legends/predaniya/tales; Rudchenko `Народні південноросійські казки` (1869-1870) for full tale texts where cleaner than Drahomanov. Preserve imperial-era bibliographic titles only as titles, not as identity framing.

### Wikisource / Hostable Public-Domain Named Pages

Acquire: T055, T056, T057, T058, T059, T061, T062, T063, T064, T065, T066, T067, T080, T081, T082, T083, T116, T117, T118, T119, T132.

**CORRECTED ENTRY POINTS (verified 2026-06-22, Claude folk driver).** The original draft cited
`https://uk.wikisource.org/wiki/Українські_народні_думи`, which is a **disambiguation page, NOT a
text index** — do not crawl it. Wikisource exposes folk texts through **category pages**, each listing
individual hostable work pages. Verified counts via the MediaWiki `categorymembers` API:

| Category | API title | Hostable pages | Feeds |
| --- | --- | --- | --- |
| Думи | `Категорія:Думи` | **45** | dumy-sotsialno-pobutovi (T055-T058), kobzarstvo (T059) |
| Колядки | `Категорія:Колядки` | **136** | koliadky-shchedrivky |
| Українські народні казки | `Категорія:Українські народні казки` | **307** | charivni/tvaryn/sotsialno-pobutovi kazky |
| Веснянки / Гаївки | `Категорія:Веснянки`, `Категорія:Гаївки` | ~11+ | vesnianky-hayivky (T039-T040) |
| Купальські / Русальні пісні | `Категорія:Купальські пісні`, `Категорія:Русальні пісні` | (cats exist) | kupalski-rusalni-pisni (T041-T044) |
| Весільні пісні | `Категорія:Весільні пісні` | (exists) | vesilni-pisni (T047-T050) |
| Жниварські пісні | `Категорія:Жниварські пісні` | (exists) | zhnyvarski (T045-T046) |
| Колискові пісні | `Категорія:Колискові пісні` | (exists) | dytiachyi-folklor-kolyskovi (T112-T115) |
| Коломийки | `Категорія:Коломийки` | (exists) | kolomyiky (T072-T074) |
| Родинно-побутові пісні | `Категорія:Родинно-побутові пісні` | (exists) | rodynno-pobutovi-pisni (T068-T071) |
| Стрілецькі пісні ⚠️ | `Категорія:Стрілецькі пісні` | (exists) | striletski (T064-T067) — RIGHTS REVIEW |
| Українські народні легенди / Перекази | `Категорія:Українські народні легенди`, `Категорія:Перекази` | (exist) | narodni-lehendy, istorychni-perekazy |

Parent index categories: `Категорія:Українська усна народна творчість` (казки, легенди, колядки,
щедрівки, перекази, засівалки) and `Категорія:Українські народні пісні` (17 song subcategories above).

**Fetch API (verified):** `prop=extracts&explaintext` returns ONLY the title for Wikisource works
(ProofreadPage transclusion) — it is the WRONG endpoint. Use `action=parse&prop=wikitext` (verse is
inline inside `<poem>...</poem>`, with a `{{заголовок}}` header template and `[[Категорія:…]]` footer
to strip) or `action=parse&prop=text` (rendered HTML). Confirmed on `Дума про козака Голоту` (T059):
opening verse "Ой полем киліїмським, / То шляхом битим гординським, / Ой там гуляв козак Голота".

**Implication for §D batch order:** most texts the draft routed to scanned scholarly PDFs
(Chubynskyi/Hnatiuk/Drahomanov) are also available as clean individual Wikisource pages — prefer the
Wikisource page where one exists; fall back to scholarly volumes only for texts with no Wikisource page.

Rights note: T064-T067 (стрілецькі пісні) require explicit per-text authorship/PD review before
hosting (e.g. «Чуєш, брате мій» = Богдан Лепкий, d. 1941; «Червона калина» has a named 1914 arranger);
if not safely PD, classify as linked-only or excerpt-only. **`Категорія:Замовляння` is EMPTY** on
Wikisource — zamovliannia (T027-T030) still needs the Yefymenko-1874 route below, not Wikisource.
Every individual page must be browser-verified (full text + PD status) before hosting.

### Ukrlib Public-Domain Folk Pages Requiring Fetch Or Verifier Repair

Acquire: T045, T046.

Known source family: `https://www.ukrlib.com.ua/narod/` harvest-song pages. Local SQLite has rows, but `verify_quote(author="Народна творчість")` did not return `matched=true`; fetch the public page and decide whether to add/repair a standalone reading row or keep as linked-only.

### Yefymenko 1874, `Збірник малоросійських заклинань`

Acquire: T027, T028, T029, T030, T129.

Batch note: pull charms and blessing formulas together. These are especially prone to encyclopedia-embedded citation; do not host until a standalone PD edition row is captured and quote-verified.

## §D Summary

- Modules inspected: 42.
- Distinct primary texts in this deduplicated map: 132.
- Hosted: 4.
- In-corpus with raw successful `verify_quote`: 22.
- Needs-fetch acquisition items: 106.
- Acquisition list size: 106 deduplicated items.
- Top source collections by expected supply: Chubynskyi 1872 and adjacent ritual-song volumes (33), Hnatiuk/NTSh collections 1902-1912 (25), Wikisource named PD pages (21), Drahomanov/Rudchenko tale-legend-predaniya collections (20), Yefymenko 1874 charms (5), ukrlib fetch/verifier-repair rows (2).

Immediate batch order:

1. Fetch Chubynskyi vol. 1 plus ritual-song volumes to cover riddles, proverbs, wedding, calendar, family/social songs, ballads, child folklore, and textile/craft riddles.
2. Fetch Hnatiuk/NTSh demonology, legends, kolomyiky, dance, regional, and lament material.
3. Fetch Drahomanov/Rudchenko prose collections for tales, legends, and historical predaniya.
4. Fetch Wikisource named pages for dumas, literary-origin songs, vertep, and bridge texts, with rights review for rifle/insurgent songs.
5. Repair or re-fetch the small ukrlib verifier-failure harvest set and the Yefymenko charm set.

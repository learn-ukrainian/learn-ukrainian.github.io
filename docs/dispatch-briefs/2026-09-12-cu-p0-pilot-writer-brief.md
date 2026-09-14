# Dispatch brief — curriculum-upgrade Phase 0 pilot: split A1 m08 `things-have-gender` into three real 60-minute lessons (LOCAL ONLY) — revision 2

You are the writer seat for ONE module. Produce real, complete lesson content — not a mockup, not placeholders. **DO NOT deploy. DO NOT change any file under `scripts/`, `site/`, `starlight/`, `.github/`, or `curriculum/l2-uk-en/plans/`. DO NOT edit the four original module files. DO NOT touch any other module. DO NOT merge.** Work only inside your dispatch worktree (`pwd` must be under `.worktrees/dispatch/`). Python is always `.venv/bin/python` (primary checkout interpreter; set `LEARN_UKRAINIAN_PRIMARY_REPO_ROOT` when an extra search root is required).

## 1. User-visible outcome

A reader opens `docs/poc/poc-lesson-split-things-have-gender.html` and can read and work through **three complete real lessons** of module A1-008 «Речі мають рід» — each one sitting of about 60 minutes, each with the four tabs Урок · Словник · Вправи · Ресурси — with **every original paragraph preserved verbatim** (plus your additions) and **at least 10 activities per lesson** (4–6 inline, 6–9 workbook). The same content exists as source artifacts under the parallel `a1-v2` level folder for Phase 1.

## 2. Denominator (frozen on `main`; the checker reads it from git, not from your tree)

- `curriculum/l2-uk-en/a1/things-have-gender/module.md` — **1,772 prose tokens in 68 paragraphs** after stripping the 8 HTML comment blocks (2,344 raw tokens). Structure: a pre-section introduction (title, orientation paragraph, "By the end, you can:" list) then five `##` sections: Діалоги · Він, вона, воно · Предмети навколо · Підсумок · Імена, пастки й самоперевірка.
- `activities.yaml` — a mapping `{inline: [6 activities with ids act-1, act-2, act-3, act-5, act-4, act-9], workbook: [5 activities WITHOUT ids]}` = 11 activities. `act-9` (4 items) is the **profession-form quiz** and the last workbook quiz (5 items, becomes `act-w5`) is the **plan's 5-point gender diagnostic**: both are kept as they are and are the only two entries allowed in `lessons.yaml: items_min_exempt`, each with an accurate reason.
- `vocabulary.yaml` — a bare list of **48 entries** (`lemma`, `translation`, `pos`, `usage`), 4 of them multi-word.
- `resources.yaml` — a list of 6 entries.
- Plan (read-only, locked): `curriculum/l2-uk-en/plans/a1/things-have-gender.yaml` — `objectives`, `content_outline` (four sections: Діалоги · Він, вона, воно · Предмети навколо · Підсумок), `vocabulary_hints`, `activity_hints`, `references`. The plan has no `targets` block. The module's fifth section realises objectives 5–6 (diagnostic traps + feminitives).
- Prerequisite identity: module 5 is «Хто я?» (self-introduction); module 6 «Моя сім'я»; **module 7 is `checkpoint-first-contact`**. Lesson 1's warm-up recalls the checkpoint (greeting, name, family) — not "module 7 «Хто я?»".

**Lesson map (fixed):**

| Lesson | Title | Takes these original parts | Minutes |
|---|---|---|---|
| 1 | Він, вона́ чи воно́? | introduction + Діалоги + Він, вона, воно | 60 |
| 2 | Предме́ти навко́ло | Предмети навколо | 60 |
| 3 | Профе́сії, па́стки й самопереві́рка | Підсумок + Імена, пастки й самоперевірка — **closes the module** with the module summary and a self-check across all three lessons | 60 |

**Preservation rule (operator: "divide the prose", not rewrite it):** every original paragraph of 8+ words (47 of them) must appear **verbatim, exactly once, in the lesson its section maps to** (introduction + Діалоги + Він, вона, воно → lesson 1; Предмети навколо → lesson 2; Підсумок + Імена, пастки й самоперевірка → lesson 3), outside HTML comments; the only permitted change inside an original sentence is adding stress marks (capitalisation and punctuation stay). Headings, bullets and short lines may move or be re-titled. You **add** (warm-up, transitions, breakdown tables, summaries, new activities); you never cut or paraphrase. Minimums: each lesson `module.md` ≥ 550 prose tokens (comments excluded); all three together ≥ 2,000.

## 3. Non-goals

No pipeline, site, plan, or CI changes; no MDX; no other module; no deploy; no increase of the English share relative to the original module (Ukrainian first in every construction; A1 English scaffolding is by design).

## 4. Read before writing

1. `docs/best-practices/v7-design-and-corpus.md` §1–§2.
2. `docs/best-practices/activity-pedagogy.md` and `docs/ACTIVITY-YAML-REFERENCE.md` for per-type fields. **Shape rule for this pilot:** each lesson's `activities.yaml` is a mapping `{inline: [...], workbook: [...]}` exactly like the original module file (this overrides the reference's bare-list note for this pilot); every activity has a unique `id`.
3. `docs/best-practices/vocabulary-activity-standards.md` for vocabulary entry quality (keep the original entry shape).
4. Template (copy unchanged to `docs/poc/poc-lesson-split-design.html`): `/tmp/claude-1000/-home-ops-learn-ukrainian/005deabf-f5ad-4ef5-b466-8ed4b7bc1ae3/scratchpad/poc-lesson-split-design.html`, SHA-256 `935c9b632b89b0b4bc3dd124bced27743a93b3dba7a924b8ece5ff28d01a91b6`. Its CSS, screen switcher and component markup are the authority for the rendered page. You are **authorised and required** to complete what the template only sketches: full screens for Урок 1, Урок 2 and Урок 3 — `<section class="screen" id="s-l1">` … `s-l3`, switcher buttons `data-screen="l1"|"l2"|"l3"`, and inside each screen exactly four tabs whose `data-tab` and panel `id` are `l{n}-urok`, `l{n}-slovnyk`, `l{n}-vpravy`, `l{n}-resursy` (the template's lesson-1 naming, repeated for 2 and 3); the module screen is `<section class="screen" id="s-module">` with `data-screen="module"`, and a Модуль screen with the real objectives and lesson cards. The A1-level screen and the design-notes screen may be dropped from the rendered page.
5. Checker and browser proof: `/tmp/claude-1000/-home-ops-learn-ukrainian/005deabf-f5ad-4ef5-b466-8ed4b7bc1ae3/scratchpad/verify_pilot.py` and `.../browser_check.mjs`. Read them first — they define "done". They are orchestrator-owned and may be updated while you work: **copy them fresh from that path immediately before your final verification run**, commit those two files unchanged under `audit/curriculum-upgrade/pilot-things-have-gender/`, and never edit them. The checker pins the baseline to commit `7829e74b6031cdcc4ef69895b5f42e0643569e44` and the four original file hashes; it fails, not warns, on drift.

## 5. Activity rules (A1 allowlist — enforced by the checker)

- Both placements: `divide-words`, `count-syllables`, `pick-syllables`, `unjumble`, `order`, `odd-one-out`, `observe`, `phrase-table`, `match-up`, `group-sort`, `quiz`, `true-false`, `fill-in`. Inline only: `image-to-letter`, `letter-grid`, `watch-and-repeat`. Workbook only: `anagram`, `error-correction`, `translate`.
- Per lesson: inline 4–6, workbook 6–9, total ≥ 10. Every activity has a list payload (`items`/`questions`/`pairs`/`sentences`/`words`/`statements`/`groups`) with ≥ 6 items (for `groups`, the sum of inner items) unless its id is `act-9` or `act-w5` (the two exemptions above).
- `<!-- INJECT_ACTIVITY: id -->` placeholders in a lesson's `module.md` must equal that lesson's inline ids, at least one per `##` section.
- The 11 originals survive with the same `type` and their full payload preserved structurally (every original item, answer flag and group stays; you may add items and stress marks), each re-homed exactly once. Inline originals keep their ids (`act-1, act-2, act-3, act-5, act-4, act-9`); the five id-less workbook originals get `act-w1`…`act-w5` in their original order. Record all 11 in `lessons.yaml`:
  ```yaml
  provenance:
    - {placement: inline, index: 0, new_id: act-1, lesson: 1}
    - {placement: workbook, index: 0, new_id: act-w1, lesson: 1}
    # … all 11
  ```
- New activities follow the presentation standard: Ukrainian-only stems and options for comprehension/recall; `translate` (EN→UK) only in workbook as a bonus.

## 6. Presentation standard (our own method)

1. Ukrainian first, English gloss after an em-dash (`Це моя́ кімна́та — this is my room.`); never "the Ukrainian word for X is Y".
2. Side-by-side bilingual table (Ukrainian left, English right) for any passage of 3+ sentences that you add; original paragraphs stay as written.
3. Stress marks (U+0301) on every multi-syllable Ukrainian word in prose, vocabulary, and activity text (original paragraphs get marks added; see §7 for verification).
4. Dialogues Ukrainian-only with named speakers; breakdown after, never interleaved.
5. Recall Q&A Ukrainian-only.
6. EN→UK translation only as a workbook bonus.
7. Voice (operator 2026-09-12): **no named guide or narrator, no "Приві́т! Я …" opener.** The lesson addresses the learner directly in second person (ви), peer tone, no praise stickers. Named people (**Марко́**, **Окса́на**, others you need) exist only as characters inside dialogues and examples; real Ukrainian places. **Attribution rule (operator 2026-09-12): citing is allowed, uncredited reuse is not.** A quotation from any reference (textbook, dictionary, podcast lesson notes, book) is a marked quotation with author/title + lesson/page at the point of use **and** an entry in that lesson's `resources.yaml`; no other author's persona, opener or lesson structure becomes ours. The checker flags any line containing `Анна|Anna|ULP|Ohoiko|Огойко` that lacks an attribution marker (`цит.`, `цитата`, `джерело`, `quoted from`, `source:`).

## 7. Language procedure (concrete; the stop rule is below)

For every Ukrainian word you introduce (not in the original module) and for every stressed form you write:
1. `mcp__sources__verify_words` on the lemma **and on each inflected form you actually use** (VESUM lists forms). Multi-word entries: verify each token.
2. `mcp__sources__verify_stress` on each multi-syllable form; on `ambiguous`, pass `pos`/`tags`; on `not_found`, do not mark it — add it to that lesson's `unverified_stress` list inside `lessons.yaml: lessons[n]` (per lesson, ≤ 10), with a one-line reason in `NOTES.md`. Unverifiable lemmas go to `lessons[n].unverified_lemmas` (per lesson, ≤ 5).
3. `mcp__sources__check_russian_shadow` takes one **word**: run it on every new lemma. Any flag → replace or justify in `NOTES.md` with a `search_style_guide` (Антоненко-Давидович) or `query_pravopys` result.
4. Calques/Surzhyk: `mcp__sources__search_ua_gec_errors` on every new verb and preposition phrase you write; paronyms: `mcp__sources__search_definitions` when two near-forms exist (e.g. -ний/-ній adjectives).
5. Feminitives are the primary profession form (вчи́телька, лі́карка); spelling per Правопис 2019.
6. Resources: cite only what you actually pulled (`chunk_id` for textbooks via `search_text`/`search_sources`); every lesson ≥ 1 entry with `title` + (`url` | `chunk_id` | `source`).

**Stop rule (enforced by the checker):** more than 5 unverified lemmas or more than 10 unverified stresses in any lesson ⇒ the lesson is **not done**; say so in the PR title (`[NOT DONE]`) and list them. Entries in `NOTES.md` explain; they never confer acceptance.

## 8. Deliverables

**Layout decision (operator 2026-09-12): the current A1 stays live and untouched; the new version is a parallel level `a1-v2`** (URLs `/a1-v2/…`, content `curriculum/l2-uk-en/a1-v2/`), so old and new can be compared side by side until cut-over.

```
curriculum/l2-uk-en/a1-v2/things-have-gender/
  lessons.yaml        # lessons: [{n: 1|2|3, title, sections: [exact original section titles this lesson carries], minutes: 60, word_target: 550 (int, >=550), activities: {total: 10, inline: [4, 6], workbook: [6, 9]},
                      #            unverified_stress: [...], unverified_lemmas: [...]}], closes_module: 3,
                      # provenance: [...11 entries {placement, index, new_id, lesson}], items_min_exempt: [{id: act-9, reason}, {id: act-w5, reason}]
  lesson-1/{module.md, activities.yaml, vocabulary.yaml, resources.yaml}
  lesson-2/…  lesson-3/…
  NOTES.md            # reasons for every exemption/unverified entry, judgement calls, residual gaps, overflow proposals
docs/poc/poc-lesson-split-design.html                 # template, unchanged (hash-checked)
docs/poc/poc-lesson-split-things-have-gender.html     # rendered real module (Модуль · Урок 1 · Урок 2 · Урок 3)
audit/curriculum-upgrade/pilot-things-have-gender/{verify_pilot.py, browser_check.mjs}   # commit these two only; verify_report.json and screens/*.png stay UNTRACKED (paste outputs in the PR body)
```
Vocabulary: the 48 originals are distributed by first use, each in exactly one lesson, every lesson ≥ 12 entries; the module union stays exactly 48 (add new words to prose only if you also add them — then the union grows and you must say so in `NOTES.md`; the checker will flag it, and the orchestrator decides).

## 9. Verification — paste raw command + cwd + output in the PR body (#M-4)

1. `.venv/bin/python audit/curriculum-upgrade/pilot-things-have-gender/verify_pilot.py` → must end `VERIFY_PILOT: PASS`. It checks: protected paths untouched, template hash, lessons.yaml shape, per-lesson prose minimums, inline/workbook counts and allowlist placement, INJECT ids, item minimums and exemptions, unique ids, vocabulary union = 48 with no duplicates, verbatim preservation of all 8+-word original paragraphs, provenance of all 11 original activities (type + item strings), stress coverage against `unverified_stress`, attribution hits, resources present, and that the rendered HTML contains every original paragraph and every activity title and the three lesson screen buttons. A pacing heuristic prints estimated minutes per lesson (45–75 expected; outside is a warning to explain, not a block).
2. `node audit/curriculum-upgrade/pilot-things-have-gender/browser_check.mjs` → must end `BROWSER_CHECK: PASS` (opens every screen and tab in headless Chromium, no page/console errors, no tab under 40 words, no horizontal overflow at 400px, screenshots saved). If Chromium is missing run `npx --prefix site playwright install chromium` first and say so.
3. `git diff --stat 7829e74b6031cdcc4ef69895b5f42e0643569e44 -- scripts site starlight .github curriculum/l2-uk-en/plans curriculum/l2-uk-en/a1/things-have-gender` → empty (same pinned commit the checker uses).
4. A table of `verify_words` / `verify_stress` / `check_russian_shadow` outcomes per lesson (counts: verified / whitelisted proper names / unverified) and the list of every unverified item.

## 10. Git

Conventional commit with the `X-Agent` trailer: `feat(curriculum-upgrade): pilot lesson split for a1/things-have-gender [Phase 0, local-only]`. `git push -u origin <branch>`; open a **DRAFT** PR whose body contains §9 outputs verbatim, the `NOTES.md` residual list, and "how to view: open docs/poc/poc-lesson-split-things-have-gender.html". Do not merge.

## 11. Completion vocabulary

**Done (for this dispatch)** = both checks PASS, §9.3 empty, stop rule not triggered, draft PR open. **Not done** = anything else; title the PR `[NOT DONE]` and name what is missing. A check you did not run is "not verified", never "passed". The two scripts prove structure, preservation, counts, coverage and rendering; they do **not** certify language quality, first-use vocabulary allocation, source verification, or the presentation rules — those are judged by an independent cross-family content review and the orchestrator's own read after your PR opens, and your §9.4 table is the evidence they start from.

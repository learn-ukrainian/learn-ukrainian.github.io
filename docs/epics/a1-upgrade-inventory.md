# A1 upgrade inventory and engine plan

Status: inventory complete; encoder in upgrade writer/assembler/gates. Do not
hand-edit lesson pages. Run `--upgrade` with `--writer agy-tools` (Gemini 3.8
Flash High). Pedagogical review stays **cross-family**; Gemini also does a
**sources audit** because this corpus feeds a Ukrainian LLM dataset.

## Pushback (binding)

1. **Gemini writes. Gemini must not be the only reviewer.** Same-family review
   is not the project gate. Writer = AGY 3.8 High. Pedagogical review = another
   family (Claude/Codex). Extra Gemini pass = **VESUM/`sources` audit** for the
   LLM dataset, not a substitute for CF.
2. **Module 9 is the close/summary *shape*, not the content clone.** Each
   module keeps the **old module's A1 immersion mix** (English carrier, UK
   targets). Do not flatten 55 modules into 9's adjectives lesson.
3. **Stress still comes from `stress_annotator.py` after review**, not from
   Gemini guessing marks. Phase 0: 29 wrong stresses when the writer "verified."
4. **Original activities stay.** New activities fill the ≥10/lesson floor.
   23 of 55 old modules have fewer than 10 activities *total*; after a 2–3
   lesson split the engine must add a lot. That is expected, not padding.
5. **Manifest order after the machine matches the approved shape.** Epic #7994:
   fixture-quality on `things-have-gender`, then A1 from `sounds-letters-and-hello`.

## Inventory (55 `a1-v1` modules, manifest order)

Opening = text before the first `##`. Kinds: `by_end` (23, like module 9),
`by_end_tip` (15, like module 8), `table` (10), `tip_no_by_end` (4),
`prose_no_by_end` (3). None missing on disk. Vocab all ≥12. **23 modules have
&lt;10 activities** and will need new ones after the split.

| n | slug | opening | words | acts | vocab |
|--:|---|---|---:|---:|---:|
| 1 | sounds-letters-and-hello | by_end | 2249 | 0 | 32 |
| 2 | reading-ukrainian | by_end | 1547 | 10 | 27 |
| 3 | special-signs | by_end | 1469 | 12 | 29 |
| 4 | stress-and-melody | by_end_tip | 1591 | 11 | 43 |
| 5 | who-am-i | table | 1853 | 10 | 55 |
| 6 | my-family | by_end | 1735 | 10 | 51 |
| 7 | checkpoint-first-contact | by_end | 1869 | 9 | 35 |
| 8 | things-have-gender | by_end_tip | 2344 | 11 | 48 |
| 9 | what-is-it-like | by_end | 1580 | 10 | 39 |
| 10 | colors | by_end | 1920 | 10 | 37 |
| 11 | how-many | by_end | 1898 | 10 | 60 |
| 12 | this-and-that | by_end | 1581 | 8 | 28 |
| 13 | many-things | by_end_tip | 1592 | 7 | 38 |
| 14 | checkpoint-my-world | by_end_tip | 1857 | 8 | 73 |
| 15–21 | verbs / questions / morning / checkpoint-actions | mixed | — | 3–4 | — |
| 22–32 | time / city (many 3–8 acts) | mostly by_end | — | 3–8 | — |
| 33–47 | city / food / communication | by_end or tip | — | 8–12 | — |
| 48–55 | past/future/health/finale | **table** openings | — | 10 | 16–26 |

Full JSON: generate with the same script in the epic comment; do not treat this
table as a substitute for `curriculum.yaml` order.

## Engine (already / to run)

| Piece | Rule |
|---|---|
| Writer | `agy-tools` / Gemini 3.8 Flash High. `--upgrade`. Sources/VESUM **required** (LLM dataset). |
| Shape | Module 9: bilingual bullets, dialogues as `>`, last lesson `Підсумок модуля — Module summary`. No ` ```text `, no `Завершення модуля` table. |
| Immersion | Copy the **old module's** A1 English/UK mix, not 9's topic. Landing: clean 9-shape or Gemini `landing-overview.md` if no "By the end". |
| Activities | Keep originals; add until ≥10/lesson. |
| Review | Cross-family pedagogy + Gemini sources audit. Stress annotator after. |
| Order | `sounds-letters-and-hello` … `a1-finale` after 8 is fixture-true. |

A2+ is a later switch (full Ukrainian). Not this inventory.

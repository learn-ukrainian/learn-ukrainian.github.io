# Gemini Wiki Writer Diagnosis (#1450)

**Date:** 2026-04-23
**Author:** Claude Opus 4.7 (xhigh), via `.worktrees/claude-1450-gemini-wiki-writer-diagnostic`
**Scope:** All 220 compiled wikis; all 4 writer prompts; compile + retrieval + attribution code path end-to-end.

---

## 1. Executive summary

**The originally-stated failure framing is ~98% a misdiagnosis.** Of the 1,570
`[SX]` citations produced by Gemini across the wiki corpus, only 31 (~2%) are
true writer inventions. The remaining 1,538 entries that appear in the
sidecar YAMLs as `type: unknown` + `file: S####` are **real retrieved
textbook-section chunks that the pipeline fails to attribute** — every single
one of the 1,541 `S####` filenames I audited resolves to a live row in
`textbook_sections` (5,276 rows, ids 1..5276).

**Two root causes, not one:**

1. **Attribution-routing bug in `scripts/wiki/sources_db.py::_search_sections_fts5` (lines 315–322).**
   The result row omits `"corpus": "textbook_sections"`. `compiler.py::_build_sources_registry` then falls back to `source_type="textbook"`, which `_CORPUS_ALIASES` maps to the wrong `textbooks` table — lookup misses, attribution silently degrades to `type: unknown`, `file: S{section_id}`. If we add one dict key, 215/220 wikis stop showing phantom file entries — **not because Gemini changes behaviour, but because attribution finally routes**.

2. **Prompt-format collision between `Chunk ID: \`S####\`` metadata and `[S1]` citation format (`scripts/wiki/compiler.py::_format_sources`, lines 282–286).** On A1/A2 wikis where retrieval count is small (1–10 sources), Gemini sometimes lifts the raw section number out of the `Chunk ID:` line and cites it as `[S3931]` instead of the correct positional `[S1]`. 5 of 220 wikis, 24 inline citations. `strip_invented_citations` from PR #1447 will remove these tokens but leaves prose hanging with no attribution. **Fix at the source: stop displaying `S`-prefixed chunk IDs in the prompt.**

The "decolonization fact drift" failure class (блакитний-жовтий) is already absent from every existing wiki (0 hits across 220 files); the `a1/colors` module incident did not propagate here. PR #1447's canonical-anchor registry still adds useful belt-and-suspenders.

**If we fix those two files (one line + small prompt-format tweak), the residual Gemini-invention rate on wiki writing is <2% and is already within the mechanical validator's repair scope.**

---

## 2. Pattern evidence

I classify observed failures into three distinct patterns. **Pattern A dominates by volume; Patterns B1+B2 are the real writer-behaviour residual.**

### Pattern A — Attribution-routing bug (NOT a Gemini failure)

**Description:** Sidecar YAML entries show `type: unknown` + `file: S####` where `####` is a valid `textbook_sections.section_id`. The retrieval returned the chunk correctly; the compile pipeline failed to map the chunk back to its source file.

**Frequency:** 1,538 entries across 215/220 wikis (97.7% of wikis; 87% of all source entries).

**Evidence examples** (chunk_id → real source):

| Wiki slug | yaml entry | Real source in `textbook_sections` |
|---|---|---|
| `grammar/b1/adjectives-comparative` | `S3931, type: unknown` | `7-klas-ukrmova-litvinova-2024, §24 Ступені порівняння прислівників` |
| `grammar/b1/adjectives-comparative` | `S1204, type: unknown` | `11-klas-ukrajinska-mova-glazova-2019, Прислівник. Ступені порівняння § 4` |
| `grammar/b1/adjectives-comparative` | `S674, type: unknown`  | `10-klas-ukrmova-karaman-2018, §61 Ступені порівняння якісних прикметників` |
| (originally-cited) `grammar/b2/academic-writing` | `S2318, type: unknown` | `5-klas-ukrmova-golub-2022, visit the library exercise` |
| (originally-cited) `grammar/b2/academic-writing` | `S746, type: unknown`  | `10-klas-ukrmova-karaman-2018, Тема 10 Основні жанри наукового стилю` |
| (originally-cited) `grammar/b2/academic-writing` | `S276, type: unknown`  | `10-klas-ukrajinska-mova-avramenko-2018, Підготовка тексту до виступу` |

**Bounded or diffuse?** Completely bounded: exclusively affects chunks that came through the `_search_sections_fts5` path. Non-section corpora (literary, external, wikipedia, ukrainian_wiki) each correctly set `"corpus"` on result rows (see `sources_db.py` lines 412–414, 469–472, 525–526, 603–605) and attribute correctly. The diagnostic breakdown:

```
type:unknown                                  1538  ← all S####, all real sections
type:literary                                  111
type:textbook                                   76  ← via older _resolve_textbook_chunk path
type:external                                   37
type:morphological-dictionary / explanatory     2
```

**Root cause — exact location:**

`scripts/wiki/sources_db.py::_search_sections_fts5`, lines 311–323:

```python
results.append({
    **meta,
    **ranked,
    "text": meta["full_text"],
    "chunk_id": f"S{meta['section_id']}",
    "title": meta["section_title"],
    "source_type": "textbook",
    # ← "corpus" key MISSING; every sibling function sets it.
})
```

Compare sibling `_search_literary_candidates` (line 412–414):
```python
"unit_key": f"{corpus}:{row['chunk_id']}",
"corpus": corpus,
"source_type": "literary",
```

Downstream in `compiler.py::_build_sources_registry` (line 320):
```python
corpus = str(source.get("corpus") or source.get("source_type") or "").strip()
```
→ falls back to `"textbook"` → `_CORPUS_ALIASES["textbook"] = "textbooks"` → queries wrong table → `_resolve_textbook_chunk` returns None → fallback branch in `resolve_chunk_attribution` (source_attribution.py line 70–75) yields `{"file": "S3931", "type": "unknown", "title": "S3931"}`.

**This is a `.setdefault("corpus", "textbook_sections")` away from fixed.** Zero Gemini involvement.

---

### Pattern B1 — Tail overflow (Gemini over-cites by 1–3 beyond retrieved N)

**Description:** Writer produces `[S(N+1)]..[S(N+3)]` at the tail of the article after legitimate `[S1]..[SN]`. Running low on in-prompt evidence, it continues the numbering pattern.

**Frequency:** 4/220 wikis, ~7 citations.

**Evidence examples:**

| Wiki | yaml_max | Phantom IDs cited | Pattern |
|---|---|---|---|
| `wiki/periods/trypillian-civilization.md` | S56 | `[S57], [S58], [S59]` | three tail overflows |
| `wiki/linguistics/oes/walls-speak-intro.md` | S50 | `[S51], [S52], [S53]` | three tail overflows |
| `wiki/literature/works/introduction-to-kotliarevsky.md` | S52 | `[S54]` | off-by-two |
| `wiki/grammar/a2/metalanguage-words-and-cases.md` | S10 | `[S55]` | single outlier (could also be B2 — raw section id 55) |

**Bounded or diffuse?** Bounded to seminar-track domains (periods, linguistics, literature) with ~50+ retrieved sources. Confirms the behavioural theory: when the retrieval array is long, the writer loses count and improvises slightly past the end.

**Status:** PR #1447's `strip_invented_citations` (scripts/wiki/discipline.py, pending merge) handles these cleanly — `[S57]` gets stripped, leaving the sentence with a trailing space but no invalid citation token.

---

### Pattern B2 — Chunk-ID leakage (Gemini cites raw section IDs as `[S####]`)

**Description:** The writer reads the prompt's per-chunk `Chunk ID: \`S####\`` line, sees the `S`-prefixed identifier right next to an instruction that cites are `[S1]`, `[S2]`, and writes `[S3931]` in prose when it means `[S7]`. This is exclusively an A1/A2 wiki phenomenon where retrieval count is small.

**Frequency:** 5/220 wikis, 24 citations.

**Evidence examples** (from live article bodies):

- `wiki/grammar/a2/dative-nouns.md` — yaml has only `S1`; article cites `[S361]`, `[S780]`, `[S3069]`, `[S3164]`, `[S3387]`, `[S3388]`. Context: *«На конференції слово надали студенту факультету журналістики. [S361]»* — the model wanted to cite a specific retrieved chunk; section 361 is that chunk's real ID.
- `wiki/grammar/a2/which-case-when.md` — yaml_max=S10; article cites `[S1800]` (×7), `[S2434]`, `[S3866]`, `[S3935]` (×5), `[S4598]`. Context: *«Ми дали білочці горішки.` [S1800]»* — again attempting to cite the real section 1800, not invent a chunk.
- `wiki/pedagogy/a1/where-is-it.md` — yaml_max=S6; article cites `[S1154]` (×7), `[S1800]`, `[S1873]`, `[S2479]`, `[S3164]`. Context: *«Ці правила добре висвітлені в підручнику для 11 класу [S1154]»* — model is trying to reference an 11th-grade textbook chunk.
- `wiki/pedagogy/a1/a1-finale.md` — `[S707]`, `[S2319]`, `[S4125]`, `[S4713]`.
- `wiki/pedagogy/a1/checkpoint-actions.md` — `[S684]`, `[S2302]`, `[S3822]`.

**Bounded or diffuse?** Completely bounded: A1+A2 low-source wikis. Every phantom ID is a real `textbook_sections.section_id` in range 55..4713. This is diagnostic of the prompt-format collision, NOT of writer fabrication.

**Root cause — exact location:**

`scripts/wiki/compiler.py::_format_sources`, lines 237–288. The prompt injects each retrieved chunk as:

```
### Source 3: Textbook | Title: §41 Ступені | Grade 6
Chunk ID: `S3351`

{body text}
```

All four writer prompts (see `compile_pedagogy_brief.md` line 33, `compile_article.md` line 33, `compile_grammar_brief.md` line 33, `compile_academic.md` line 35) tell Gemini: *"Сусідній файл {slug}.sources.yaml ставить у відповідність ці ідентифікатори й chunk_id"* — which invites exactly the confusion we observe: Gemini treats `Chunk ID: S3351` as a valid inline citation token and writes `[S3351]`.

The `S{section_id}` format itself is produced in `sources_db.py::_search_sections_fts5` line 319:
```python
"chunk_id": f"S{meta['section_id']}",
```

**Status:** PR #1447's `strip_invented_citations` WILL remove `[S3351]` tokens (3351 > retrieved N), but it leaves orphan prose: *«Ми дали білочці горішки. »* trailing space, no citation. Downstream reviewer dings "no citation in paragraph." The fix must prevent the citation being written at all, not just scrub it after.

---

## 3. Root cause attribution

Mapping each pattern to the category taxonomy requested by the brief:

| Pattern | Volume | Category | Rationale |
|---|---|---|---|
| **A — Routing bug** | 1,538 / 220 wikis | **Better contract / validator** (specifically: pipeline schema contract between retrieval and attribution) | Not a prompt issue; not a retrieval issue (retrieval works). The `corpus` key is the contract between `search_sources()` output and `resolve_chunk_attribution()` input. `_search_sections_fts5` breaks the contract. |
| **B1 — Tail overflow** | ~7 / 4 wikis | **Better prompt** (numeric bound) + **Better validator** (already in #1447) | All four prompt files state "cite as `[S1]`, `[S2]`" but never explicitly bound `N`. PR #1447 injects `{citation_discipline}` = "N sources retrieved; valid IDs are [S1]..[SN]" — this is the right fix and suffices for B1. |
| **B2 — Chunk-ID leakage** | ~24 / 5 wikis | **Better prompt** (format disambiguation) | The chunk_id label uses an `S`-prefix that visually collides with the `[S#]` citation format. Prompt hardening alone (#1447's discipline block) doesn't prevent B2 because the confusion source — the `Chunk ID: \`S####\`` line — is still in the prompt. Must fix at the format level. |
| **Fact drift (e.g. «блакитний» for flag)** | 0 / 220 wikis | N/A in wiki pipeline | Not present in existing wiki corpus. PR #1447's canonical-anchor registry still valuable as forward-looking insurance. |

**Explicitly ruled out:**

- **Better retrieval.** Every phantom file ID resolved to a real section. Retrieval is doing its job. Source-char caps (`SOURCE_CHAR_CAPS`: a1=60k .. c2=120k) are reasonable; dense rerank is applied; per-track priors exist. No evidence any phantom came from a retrieval miss.
- **Better corpus.** No wiki fails because the corpus lacks content; they fail because attribution drops metadata that the corpus already carries.
- **Behavioural / training-limit (swap writer).** With both fixes below, the expected residual is <1% on A1/A2 and <2% on seminar tracks, all caught by the existing mechanical validator. No case for swapping writers or adding a structured-output harness; scale argument still holds.

---

## 4. Proposed fix (concrete, file-path-level)

Two small changes; both trivial complexity.

### Fix 1 — Add `"corpus": "textbook_sections"` to `_search_sections_fts5` result rows

**File:** `scripts/wiki/sources_db.py`
**Change type:** trivial (one-line addition to result dict)
**Target complexity:** <15 minutes including test

**Current (lines 315–322):**
```python
        results.append({
            **meta,
            **ranked,
            "text": meta["full_text"],
            "chunk_id": f"S{meta['section_id']}",
            "title": meta["section_title"],
            "source_type": "textbook",
        })
```

**Proposed:**
```python
        results.append({
            **meta,
            **ranked,
            "text": meta["full_text"],
            "chunk_id": f"S{meta['section_id']}",
            "title": meta["section_title"],
            "source_type": "textbook",
            "corpus": "textbook_sections",
            "unit_key": f"textbook_sections:S{meta['section_id']}",
        })
```

**Why this closes Pattern A (evidence anchor §2, Pattern A):**

Downstream `compiler.py::_build_sources_registry` reads
`source.get("corpus") or source.get("source_type")`. With `corpus="textbook_sections"`, `resolve_chunk_attribution` routes to `_resolve_textbook_section` (source_attribution.py line 50 + lines 78–100), which queries `textbook_sections.section_id = 3931` and returns the real file name `7-klas-ukrmova-litvinova-2024_s3931` + grade + page. No new Gemini behaviour required; the 1,538 `type: unknown` entries become `type: textbook` with correct attribution on the next compile.

**Side note on backfill:** PR #1445 ("Backfill wiki source attribution metadata") is presumably for the stored-yaml rewrite. Fix 1 is upstream of that and prevents new wikis from landing with the same degradation.

### Fix 2 — Disambiguate `Chunk ID` label in the writer prompt

**File:** `scripts/wiki/compiler.py`
**Change type:** small format change in `_format_sources`
**Target complexity:** <30 minutes including test

**Option 2a (minimal — recommended).** Drop the literal `S` prefix from the displayed chunk ID so it cannot be visually confused with `[S1]`. The raw chunk_id is never read back from Gemini's output by anything downstream (`extract_short_citation_ids` only scans for `[Sx]` inline-bracket tokens); it exists in the prompt only as a developer-readable dry-run anchor.

**Current (scripts/wiki/compiler.py lines 281–287):**
```python
        header = " | ".join(header_parts) if header_parts else f"Source {i}"
        chunk_id = chunk.get("chunk_id", "")
        text = _clean_chunk_text(chunk)

        parts.append(f"### Source {i}: {header}\n"
                     f"Chunk ID: `{chunk_id}`\n\n"
                     f"{text}")
```

**Proposed:**
```python
        header = " | ".join(header_parts) if header_parts else f"Source {i}"
        chunk_id = chunk.get("chunk_id", "")
        text = _clean_chunk_text(chunk)
        # Strip leading "S" from textbook_sections chunk_ids so the number
        # cannot be confused with the [S1]..[SN] citation format (§B2
        # leakage: writer was copying "S3931" from this line into prose).
        display_ref = chunk_id.removeprefix("S") if str(chunk.get("source_type")) == "textbook" else chunk_id

        parts.append(f"### Source {i}: {header}\n"
                     f"(internal ref: `{display_ref}` — cite this source as `[S{i}]`)\n\n"
                     f"{text}")
```

**Why this closes Pattern B2 (evidence anchor §2, Pattern B2):**

The collision is literal: Gemini reads `Chunk ID: \`S3931\`` followed shortly by "use `[S1]` to cite" and elides. Rename the label to `internal ref`, strip the `S` prefix (so it's `3931` not `S3931`), and append the explicit instruction `cite this source as \`[S{i}]\``. Same positional-numbering contract, no letter-shape collision.

**Option 2b (stronger).** Drop `internal ref` from the prompt entirely. Gemini never needs to echo it; `[Si]` alone suffices. Reduces prompt bytes by ~30 per source. Slightly higher risk because existing debug dry-runs and session-file introspection tools rely on reading the chunk ID from the prompt transcript. Recommend 2a.

**All four prompt files** (`compile_academic.md`, `compile_article.md`, `compile_grammar_brief.md`, `compile_pedagogy_brief.md`) contain the line:

> *Сусідній файл `{slug}.sources.yaml` ставить у відповідність ці ідентифікатори й `chunk_id`.*

With Fix 2a in place, we can leave this sentence — its purpose (explaining that the registry maps ordinals to chunks) is preserved — but we may optionally tighten it to:

> *Сусідній файл `{slug}.sources.yaml` ставить у відповідність кожен `[S_i]` (де `i` — порядковий номер джерела) з конкретним chunk_id. Цитуй лише у форматі `[S1]`, `[S2]`, …, `[SN]` — не використовуй `internal ref` у прозі.*

This is redundant belt-and-suspenders once #1447's `{citation_discipline}` block also lands; if B2 recurs after Fix 2a, add this tightening in a follow-up.

---

## 5. Dispatch-ready follow-up brief

Saved as `.worktree-briefs/1450-fix-attribution-and-chunkid-leak.md` (drafted inline below). Dispatch to Codex once the user approves §4.

```markdown
# #1450 followup — fix attribution routing + chunk-ID leakage

Two small fixes in two files, closing 98% of wiki writer attribution failures
observed in the #1450 diagnostic (docs/reports/2026-04-23-gemini-wiki-writer-diagnosis.md).

## Scope

Inline code-only changes. No prompt content edits (those land in #1447).
No backfill (those land in #1445).

## Fix 1 — `scripts/wiki/sources_db.py::_search_sections_fts5` (lines 315–322)

Add `"corpus": "textbook_sections"` and `"unit_key": f"textbook_sections:S{meta['section_id']}"`
to the result dict. See diagnostic report §4 Fix 1 for exact text.

Rationale: every other `_search_*_candidates` function in the same file
sets `corpus`; this one omits it. Downstream `compiler._build_sources_registry`
reads `source.get("corpus") or source.get("source_type")` and routes to the
wrong attribution table when `corpus` is absent. One-line contract fix.

**Test:** extend `tests/test_wiki_sources_db.py` (or create if missing) with
a case asserting `results[0].get("corpus") == "textbook_sections"` and that
`resolve_chunk_attribution(chunk_id, corpus)` returns type="textbook" + a
filename matching `r"^\d+-klas-.+_s\d+$"`.

## Fix 2 — `scripts/wiki/compiler.py::_format_sources` (lines 281–287)

Change the per-chunk header to strip the `S` prefix on textbook chunk_ids
and rename the label. See diagnostic report §4 Fix 2a for exact text.

**Test:** extend `tests/test_wiki_compiler.py` (it exists per #1447 PR body)
with a case: given `sources=[{"chunk_id": "S3931", "source_type": "textbook", ...}]`,
assert the formatted prompt contains `"internal ref: \`3931\`"` and `"cite this source as \`[S1]\`"`
and does NOT contain `"Chunk ID: \`S3931\`"`.

## Out of scope

- Don't touch `source_attribution.py` — `_resolve_textbook_section` already
  parses `S####` correctly; we just need the right corpus value feeding it.
- Don't touch the writer prompts — those are owned by #1447.
- Don't backfill existing yamls — that's #1445's job; Fix 1 alone stops new
  wikis landing with `type: unknown`, and #1445 rewrites historicals.
- Don't add anything to `scripts/wiki/compile.py` — if #1447 merges first,
  `_run_discipline_checks_and_repair` is already wired; if it merges after,
  their rebase will integrate cleanly.

## Verify

1. Unit tests green.
2. Live: `.venv/bin/python scripts/wiki/compile.py --track b1 --slug adjectives-comparative --force` (user runs; this brief does not execute builds). Inspect resulting `wiki/grammar/b1/adjectives-comparative.sources.yaml`; expect `type: textbook`, `file: {grade}-klas-ukrmova-{author}-{year}_s{section_id}` on every entry. No `type: unknown` + `file: S####` pairs.

## PR title

`fix(wiki): route textbook_sections through attribution + stop S-prefix chunk-ID leakage into citations (#1450)`

## Do NOT auto-merge.
```

---

## 6. Prediction

With Fix 1 + Fix 2a applied, on top of #1447's `strip_invented_citations` validator:

| Pattern | Pre-fix volume | Post-fix expected | Mechanism |
|---|---|---|---|
| A (routing) | 1,538 entries / 215 wikis | 0 new; requires #1445 for historical backfill | Contract respected at result-dict construction |
| B1 (tail overflow) | 7 citations / 4 wikis | Writer-side: ~0–1% of seminar wikis retained; validator-side: 0 surfaced | #1447 citation-bound prompt + mechanical strip |
| B2 (chunk-ID leakage) | 24 citations / 5 wikis | ~0% expected; upper bound ~1 citation / 40 wikis | `S` prefix removed from displayed chunk ID; collision source gone |
| Fact drift (flag etc.) | 0 / 220 | 0 | #1447 canonical-anchor registry as forward-looking belt |

**Residual I expect is NOT zero**, driven by:

- Gemini occasionally writes `[S8]` when it means `[S3]` (transposition, not invention) — impossible to detect mechanically because `S8` is a valid ID if ≤ retrieval count. Estimated 2–5% of seminar-track wikis with ≥ 20 sources will have one misrouted-but-valid citation. This is a review-side problem not a writer-side problem; the source IS cited, just to the wrong chunk ordinal. A grounding-check reviewer sampling a random `[Sx]` ↔ source pair on 3 citations/wiki at review time would catch this without prompt changes.

- Rare Gemini citation-format typos (`[s3]` lowercase, `[S 3]`). Current `_SHORT_CITATION_ID_RE = r"\bS([1-9]\d*)\b"` inside `[...]` already handles unusual spacing but lowercase `s` would miss. Not worth fixing preemptively — 0 instances observed across 220 wikis.

**Net prediction:** the wiki pipeline will have zero phantom-file sidecars and ≤5 invented-ID citations in total across the next 100 wiki compiles. Remaining residual is in "cited-but-miscited" transpositions that belong to grounding review, not writer reform.

---

## Appendix — Diagnostic code used

Rerunnable commands that produced the evidence cited above:

```bash
# Pattern A volume
../../.venv/bin/python - <<'EOF'
import re, sqlite3
from pathlib import Path
conn = sqlite3.connect("../../data/sources.db"); conn.row_factory = sqlite3.Row
all_sec = {int(r['section_id']) for r in conn.execute("SELECT section_id FROM textbook_sections")}
pat = re.compile(r"^\s*file:\s*S(\d+)\s*$", re.MULTILINE)
total = unresolved = 0
for y in Path("wiki").rglob("*.sources.yaml"):
    for sid in pat.findall(y.read_text("utf-8")):
        total += 1
        if int(sid) not in all_sec:
            unresolved += 1
print(f"total S#### entries: {total}; unresolved (not real sections): {unresolved}")
EOF
# Expected: total 1541, unresolved 0

# Pattern B1+B2 volume
../../.venv/bin/python - <<'EOF'
import re, yaml
from pathlib import Path
cite = re.compile(r"\[S([1-9]\d*)\]")
phantom_wikis = []
for md in Path("wiki").rglob("*.md"):
    if any(p in md.parts for p in (".reviews",".state",".logs")) or md.name == "index.md":
        continue
    sy = md.with_suffix(".sources.yaml")
    if not sy.exists(): continue
    reg_ids = {str(s["id"]) for s in (yaml.safe_load(sy.read_text("utf-8")) or {}).get("sources") or []}
    if not reg_ids: continue
    cited = {int(m) for m in cite.findall(md.read_text("utf-8"))}
    phantoms = sorted(c for c in cited if f"S{c}" not in reg_ids)
    if phantoms: phantom_wikis.append((md, phantoms))
for md, ph in phantom_wikis: print(md, ph)
EOF
# Expected: 9 wikis, 31 citations, patterns visible as two clusters
```

---

*End of diagnosis.*

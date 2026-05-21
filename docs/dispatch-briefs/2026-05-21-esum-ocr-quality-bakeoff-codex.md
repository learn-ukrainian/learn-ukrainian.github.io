# Brief: ЕСУМ OCR quality bake-off — Tesseract vs Gemini-2.5 vs Gemini-3.5/agy vs PDF-text-layer

> **Agent**: Codex (research with judgment + cross-file analysis + structured comparison report)
> **Mode**: workspace-write (no commits — pure research output; brief writes only to `audit/etymology-ocr-bakeoff/` and the final report)
> **Scope**: sample 30 pages × 4 OCR pipelines, score them, recommend a path forward
> **Why now**: Issue #2001 re-OCR is running, but we just discovered (a) all 6 vols are ALREADY in `data/processed/esum_vol{1..6}.jsonl` from a Tesseract pipeline, (b) the new Gemini-2.5 re-OCR produces semantic hallucinations that look clean but cite fabricated cognates (e.g. linking "сму́шок" sheepskin to Czech "smutek" sadness — confirmed wrong via `mcp__sources__search_esum`). User wants data, not gut feel, before deciding whether to (i) keep Gemini OCR, (ii) revert to Tesseract, (iii) switch to a third source.

---

## 1. Background (read first, do NOT re-debug)

**Two ESUM pipelines exist on disk RIGHT NOW**:

| Pipeline | Source files | When | What we know |
|---|---|---|---|
| **Tesseract (in MCP)** | `data/raw/esum/vol{N}.txt` (May 4 / May 14) → `data/processed/esum_vol{N}.jsonl` (29,171 entries) → `sources.db` → `mcp__sources__search_esum` | May 4–14 | Visible OCR noise: `\|снажний\|`, `Їснагі\|`, broken brackets. Errors are syntactic — easy to see, hard to silently misinterpret. |
| **Gemini-2.5-flash (current re-OCR)** | `data/raw/esum/jp2-staging/vol{N}/*.jp2` → `data/raw/esum/gemini-ocr/vol{N}/p*.md` (~3,179 files) → `data/raw/esum/vol{N}-gemini.txt` (vol1+2+3 concatenated) | May 17 onward, ongoing | Clean-looking output but **17 confirmed structural hallucinations** (repetition-loops) and **1 confirmed semantic hallucination** (vol5/p0469 cited Czech *smutek*=sadness and Sanskrit *smárati*=remembers as cognates for *сму́шок*=sheepskin — fabricated). |
| **Gemini-3.5-flash via agy** | not yet tried | — | User just discovered `agy` (Antigravity CLI 1.0.0, Gemini 3.5 Flash High) and says it has OCR capability. Available as dispatch agent: `--agent agy`. May be a meaningfully better model. |
| **PDF text layer (if present)** | `data/textbooks/` or wherever the original ESUM PDFs live | — | Sometimes scanned-PDFs have an underlying text layer from the publisher; `pdftotext` extracts it lossless. Worth a quick check before assuming all 4 paths are OCR. |

**Decision the user is trying to make**: which of these 4 pipelines (or a hybrid) becomes the canonical ESUM corpus loaded into the MCP for downstream consumers? Critical that the choice be evidence-based, not gut-feel.

---

## 2. Deliverable — single report at `audit/etymology-ocr-bakeoff/REPORT.md`

Structure (HTML allowed per #M-2 since this is ai→human):

```
# ESUM OCR quality bake-off — 2026-05-21

## TL;DR (one paragraph + verdict line)
RECOMMENDED PIPELINE: <one of: tesseract / gemini-2.5 / gemini-3.5-agy / pdf-text-layer / hybrid:X+Y>
WHY: <2 sentences>

## Method
- Sample: 30 pages selected by stratified random across vol1-vol6 (5 per vol). List the page numbers.
- Ground truth: original JP2 scan (visually inspected via image viewing) OR the PDF source.
- Pipelines tested: 4 above (skip pdf-text-layer if no text layer exists; note it).
- Scoring rubric: see §3.

## Per-pipeline scorecard (4 tables, identical columns)
Columns: page | char_acc | semantic_acc | hallucination_flags | quirks
Rows: 30 sampled pages.

## Aggregate scores (one bar chart or markdown table)
| Pipeline | mean char_acc | mean semantic_acc | hallucination_rate | speed | cost |
| ... | ... | ... | ... | ... | ... |

## Failure-mode taxonomy
For each pipeline, 3-5 representative failure examples with page citation and explanation.

## Recommendation
Numbered argument for the chosen pipeline. Address all 4 alternatives explicitly (don't omit any).

## Follow-up work
- What needs to land in main before the recommended pipeline can replace the deployed one.
```

---

## 3. Scoring rubric (apply uniformly)

| Dimension | Scale | How to score |
|---|---|---|
| **char_acc** | 0.0–1.0 | Fraction of words in OCR output that exactly match the JP2 ground truth (or are within 1 edit distance for Cyrillic-only). Sample a 50-word window per page. |
| **semantic_acc** | 0.0–1.0 | Fraction of cited cognates / cross-references that match the JP2 ground truth. Pipelines may invent plausible-looking cognates that aren't on the page — those score 0. |
| **hallucination_flags** | 0+ count | Number of structural (repetition-loop, off-topic content) + semantic (invented cognates) failures observed on the page. |
| **quirks** | free text | One-liner: visible OCR noise, layout breakage, language-mixing, etc. |

**Critical**: a pipeline that scores 0.95 char_acc but 0.40 semantic_acc is WORSE than one that scores 0.70 / 0.95 — because semantic noise fools downstream consumers while syntactic noise stays visible. State this trade-off explicitly in your TL;DR.

---

## 4. Tasks (numbered, execute in order)

### Step 1 — worktree setup

```bash
git worktree add .worktrees/codex/esum-bakeoff -b codex/esum-bakeoff origin/main
cd .worktrees/codex/esum-bakeoff
mkdir -p audit/etymology-ocr-bakeoff
```

### Step 2 — sample selection

Pick 5 pages per volume, stratified across page ranges (early / mid / late) for representativeness. Avoid the 17 known quarantined pages (those are pre-confirmed bad). Write the list to `audit/etymology-ocr-bakeoff/sample-pages.txt`.

Helper: `ls data/raw/esum/gemini-ocr/_quarantine/2026-05-19-repetition-hallucination/` lists the quarantined pages to avoid.

### Step 3 — gather 4 outputs per page

For each sampled page:

1. **Tesseract**: look up by lemma in `data/processed/esum_vol{N}.jsonl` (load JSONL, find rows whose `page == sampled_page`). Multiple entries per page is normal.
2. **Gemini-2.5-flash (current run)**: read `data/raw/esum/gemini-ocr/vol{N}/p{NNNN}.md`. If quarantined, skip and note.
3. **Gemini-3.5-flash via agy**: dispatch a single-page OCR via the agy CLI. Find the CLI invocation pattern — `agy --help` should show it, or fall back to `agy -p '<image-attached-via-something>'`. If agy doesn't have a headless prompt mode, note and skip this pipeline (don't fabricate output).
4. **PDF text layer**: check if any ESUM source PDF exists in `data/textbooks/` or similar. If yes, `pdftotext` it. If not, skip and note.

Store all four outputs under `audit/etymology-ocr-bakeoff/samples/vol{N}/p{NNNN}/` so they can be hand-inspected later.

### Step 4 — score each page against ground truth

Ground truth = the JP2 scan at `data/raw/esum/jp2-staging/vol{N}/p{NNNN}.jp2`. Two ways to inspect:

- **Visual**: open the JP2 and eyeball-compare to OCR output. Slowest but most reliable.
- **Cross-pipeline triangulation**: if 3 of 4 pipelines agree on a word and 1 disagrees, the dissenter is probably wrong. Faster proxy when visual is impractical.

Use the rubric in §3. Be honest — if Gemini-2.5 looks beautiful but invents a cognate, give it 0 on semantic_acc.

Spot-check semantic accuracy by querying `mcp__sources__search_esum` for the headword and comparing — if MCP's existing Tesseract-backed result says different cognates than the Gemini output claims, the Gemini one is the likely hallucination (because we have multiple independent witnesses: page + Tesseract + MCP).

### Step 5 — write the report (`audit/etymology-ocr-bakeoff/REPORT.md`)

Per §2 structure. Be brutal — recommendation must address WHY the other 3 are worse, not just why the chosen one is good.

### Step 6 — commit + push, NO PR

```bash
git add audit/etymology-ocr-bakeoff/
git commit -m "audit(esum-ocr-bakeoff): 4-pipeline quality comparison + recommendation"
git push -u origin codex/esum-bakeoff
```

NO PR needed — this is research output that the orchestrator (me) will read and act on. Land it on the branch for review.

### Step 7 — final stdout message

End your run with a one-line summary the orchestrator can grep:
```
ESUM_BAKEOFF_DONE recommendation=<tesseract|gemini-2.5|gemini-3.5-agy|pdf-text-layer|hybrid:X+Y> report=audit/etymology-ocr-bakeoff/REPORT.md
```

---

## 5. Anti-fabrication guard rails (per #M-4)

| Claim | Required evidence |
|---|---|
| "char_acc = 0.X" | Quote the 50-word ground-truth window + OCR window side-by-side in the per-page sample dir |
| "semantic_acc = 0.X" | List the cognates claimed by OCR + corresponding cognates from MCP/ground-truth + which match |
| "Pipeline N is best" | Per-dimension comparison with quoted examples, not vibes |
| "PDF text layer / agy / X not available" | Show the command you tried + raw stderr proving it failed |

Bare "I tested and Gemini won" without scoring data = report rejected.

---

## 6. Out of scope

- Do NOT touch `scripts/etymology/bulk_ocr_gemini.py` — the current run keeps going regardless of this brief's outcome.
- Do NOT migrate any data to MCP yet — recommendation only; orchestrator handles migration in follow-up.
- Do NOT re-OCR quarantined pages — that's closeout brief work, separate.

---

## 7. Failure modes — surface, don't fake

- If sample size of 30 is too expensive (e.g., agy CLI doesn't support headless), reduce to 15 (3 per vol) and note.
- If you can't visually inspect JP2 (no image tool available in dispatch env), use cross-pipeline triangulation only and CALL THAT OUT in the method section.
- If agy CLI isn't actually OCR-capable in headless mode (only interactive), don't fake a comparison — score it "not testable in dispatch" and note the user must run it manually for a fair comparison.

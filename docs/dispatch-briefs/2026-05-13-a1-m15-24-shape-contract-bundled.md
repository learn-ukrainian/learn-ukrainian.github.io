# Codex dispatch brief — a1-m15-24 shape contract (#1962 gates 2-4 bundled implementation)

> **Issues:** #1962 gates 2-4 — `citations_resolve` (writer drift), `l2_exposure_floor` (gate-counter format mismatch), `long_uk_ceiling` (source-blockquote exemption)
> **Decision Card:** `docs/decisions/pending/2026-05-13-a1-m15-24-shape-contract.md` (PROPOSED, multi-agent converged)
> **Mode:** danger
> **Worktree:** `.worktrees/dispatch/codex/a1-shape-contract-2026-05-13/`
> **Base:** `origin/main` (currently `44e6e9a964`)
> **Hard timeout:** 7200s
> **Silence timeout:** 1800s
> **Effort:** high

---

## ⚠️ CRITICAL — fresh-shell behavior

Each bash block runs in a FRESH SHELL. Prefix every command with `cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/a1-shape-contract-2026-05-13 && ...` or absolute path. Inside the worktree, `.venv/` is gitignored — use main checkout's `.venv` via absolute path: `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python`.

---

## Goal

Ship the converged a1-m15-24 module shape contract from the multi-agent discussion at `ab channel tail a1-m15-24-shape-contract --thread 767f107789e241919a36f573be37d4ca`. After this PR merges + m20 V7 build #5 runs, all 4 gates from #1962 should pass (gate 1 already shipped in PR #1963).

This is a **bundled PR** covering 3 axes. They cohere as a single contract; shipping piecemeal risks one axis landing without the others' enabling logic.

---

## #M-4 preamble — verifiable claims this work will produce

| Claim | Deterministic tool | Output format |
|---|---|---|
| "Writer prompt mandates `<DialogueBox>` or `> ` blockquote for dialogues" | `grep -n 'DialogueBox\|blockquote' scripts/build/phases/linear-write.md` | quote grep output |
| "Writer prompt requires inline gloss within 8 words for dialogue lines" | `grep -n 'inline gloss\|8 words\|within 8' scripts/build/phases/linear-write.md` | quote grep output |
| "Writer prompt restricts non-plan citations to Knowledge-Packet-grounded sources" | `grep -n 'plan_references\|Knowledge Packet\|knowledge.packet\|packet.grounded' scripts/build/phases/linear-write.md` | quote grep output |
| "long_uk_ceiling gate exempts citation-grounded source blockquotes" | `grep -n 'textbook_grounding\|source blockquote\|cited blockquote' scripts/build/linear_pipeline.py` | quote grep output |
| "All targeted tests pass" | `.venv/bin/pytest tests/build/test_linear_pipeline.py -v` | quote summary line |
| "Lint clean" | `.venv/bin/ruff check scripts/build/ tests/build/` | quote final line |
| "PR opened" | `gh pr view <N> --json url` | quote URL |

Inline "I checked X" without quoted raw output = hallucination per #M-4. Quote.

---

## Pre-read (do this before coding)

Read these files FIRST so the implementation respects existing architecture:

```bash
cat /Users/krisztiankoos/projects/learn-ukrainian/docs/decisions/pending/2026-05-13-a1-m15-24-shape-contract.md
sed -n '83,115p;195,230p' scripts/build/phases/linear-write.md   # citation + dialogue sections
sed -n '5290,5340p;5392,5450p' scripts/build/linear_pipeline.py  # immersion + long_uk gate code
grep -n "def _citation_gate\|def _count_uk_dialogue_lines\|def _unsupported_run_segments" scripts/build/linear_pipeline.py
cat scripts/build/citation_matcher.py | head -100
```

If the actual file content at `main@44e6e9a964` differs significantly from what this brief expects (e.g. the dialogue counter was already refactored), **STOP and report** — the design may need to shift.

---

## The 3 axes (implement in order — each independently verifiable)

### Axis 1: Writer prompt — citation discipline + dialogue format + gloss strategy

File: `scripts/build/phases/linear-write.md`

Three additive directives. Find appropriate insert sites (likely near existing dialogue + citation sections).

**Directive A — dialogue format (insert near existing dialogue guidance):**

```markdown
**Dialogue format (REQUIRED for gate counting).** All Ukrainian dialogue lines MUST be emitted as one of:

- `<DialogueBox uk="..." en="...">` JSX component (preferred for V7 rendering), or
- `> `-prefixed Markdown blockquote (Markdown fallback)

The `l2_exposure_floor` gate counts only these two forms. **Em-dash dialogue lines (e.g. `— Привіт, Насте!`) under a `## Діалоги` heading WITHOUT `<DialogueBox>` or `> ` wrapping are an anti-pattern** — the gate cannot count them and the module will fail the dialogue-line floor even when the dialogue is pedagogically present.

Default to `<DialogueBox>` for new modules; `> ` blockquote acceptable when a multi-line dialogue is more naturally rendered as quoted prose.
```

**Directive B — inline gloss strategy (insert near existing gloss / English-support guidance):**

```markdown
**Inline gloss for dialogue lines (REQUIRED to clear `long_uk_ceiling`).** Each Ukrainian dialogue line MUST have an inline English gloss within 8 tokens of proximity. Two valid shapes:

- Italic gloss directly after the UK line: `— Привіт, Насте! *(Hi, Nastia!)*`
- Inside the same DialogueBox prop: `<DialogueBox uk="..." en="...">`

**Anti-pattern: block-bottom gloss.** Do NOT emit all UK dialogue lines first and then a separate "translation:" / "English:" block at the bottom. This causes `long_uk_ceiling` to flag the entire UK run as one unsupported segment, even when every line has a corresponding English translation farther down.
```

**Directive C — citation discipline (insert near existing citation/sources guidance):**

```markdown
**Citation discipline.** Sources cited in `module.md` blockquotes and listed in `resources.yaml` MUST be either:

1. Listed in the module's `plan_references` (the matcher allows fuzzy match on author + grade + small page drift), OR
2. Grounded in a Knowledge Packet retrieval the writer's `mcp__sources__search_text` call actually returned. Cite the chunk's textbook + grade + page verbatim from the search result.

**Do NOT add textbook references outside `plan_references` unless option 2 holds and the citation appears in your `writer_tool_calls.json` evidence.** Adding ungrounded out-of-plan citations causes `citations_resolve` to fail and the build to halt.
```

Place each directive in the section that most closely matches its topic. The existing sections (search for `Citation`, `Dialogue`, `gloss`, `External Resources`) are likely candidates; pick the best fit and don't duplicate guidance the prompt already has — replace OR augment as appropriate.

### Axis 2: Gate — long_uk_ceiling source-blockquote exemption

File: `scripts/build/linear_pipeline.py`

Currently `_unsupported_run_segments` (line ~5451) treats all `> ` blockquotes as candidate UK runs, with no source-vs-practice distinction.

**Change:** Pass textbook_grounding evidence as input to `_long_uk_ceiling_gate` and onward to `_unsupported_run_segments`. Exempt blockquote spans that match a textbook_grounding `matched` citation.

Suggested shape:

```python
def _long_uk_ceiling_gate(
    text: str,
    plan: Mapping[str, Any],
    *,
    grounding_evidence: Mapping[str, Any] | None = None,  # NEW kwarg
) -> dict[str, Any]:
    ...
    runs = _unsupported_run_segments(
        text,
        grounding_evidence=grounding_evidence,  # propagate
    )
    ...

def _unsupported_run_segments(
    text: str,
    *,
    grounding_evidence: Mapping[str, Any] | None = None,
) -> list[str]:
    """Return UK runs that lack inline English support.

    Blockquote spans (`> ...`) whose content overlaps a textbook citation
    in `grounding_evidence['matched']` are exempted as source material,
    not learner-target prose.
    """
    # Build a set of "exempt blockquote signatures" from grounding_evidence
    # ... (signature = normalized substring or block-index — pick what's
    # cheapest to compute from the existing grounding evidence shape)
    # Skip blocks whose first 50 chars match an exempt signature.
```

**Call-site update** (line ~3696 in `run_python_qg`):

```python
record(
    "long_uk_ceiling",
    _long_uk_ceiling_gate(
        module_text,
        plan,
        grounding_evidence=gates.get("textbook_grounding"),  # pass earlier-recorded report
    ),
)
```

Order matters: `_textbook_grounding_gate` must run BEFORE `_long_uk_ceiling_gate` so the evidence is available. The current order at lines 3688-3696 already has `textbook_grounding` before `long_uk_ceiling` — good.

### Axis 3: Citation matcher — page-drift tolerance (small)

File: `scripts/build/citation_matcher.py`

Decision Card default: same author + same grade + page distance ≤5 pages.

If `citation_matcher.py` already parses author/grade/page (per Codex r1: line 80), the change is small — soften page-equality to tolerance check:

```python
# Before (likely):
if cite.author == plan.author and cite.grade == plan.grade and cite.page == plan.page:
    ...

# After:
if (
    cite.author == plan.author
    and cite.grade == plan.grade
    and abs(cite.page - plan.page) <= 5  # NEW: ±5 page tolerance
):
    ...
```

If the matcher is more complex than this skeleton, adapt — but preserve the existing exact-match-then-fuzzy hierarchy. **Page tolerance must NOT cross author or grade boundaries.**

---

## Tests (add ~8-10 fixtures across the 3 axes)

In `tests/build/test_linear_pipeline.py` near existing dialogue/long_uk tests:

**Axis 1 tests** (writer prompt content assertions, mirror `test_linear_write_prompt_documents_non_textbook_role_url_requirement` shape):

```python
def test_linear_write_prompt_mandates_dialoguebox_or_blockquote_for_dialogues() -> None:
    """#1962 axis 2: writer must emit dialogues in gate-countable form."""
    template = Path("scripts/build/phases/linear-write.md").read_text(encoding="utf-8")
    assert "DialogueBox" in template
    assert "blockquote" in template.lower() or "`> `" in template
    assert "em-dash" in template.lower() or "anti-pattern" in template.lower()


def test_linear_write_prompt_requires_inline_gloss_within_8_tokens() -> None:
    """#1962 axis 2b: each dialogue line needs inline English gloss."""
    template = Path("scripts/build/phases/linear-write.md").read_text(encoding="utf-8")
    assert "inline gloss" in template.lower() or "inline English" in template.lower()
    assert "8 tokens" in template or "8 words" in template or "within 8" in template
    assert "block-bottom" in template.lower() or "block bottom" in template.lower()


def test_linear_write_prompt_restricts_non_plan_citations() -> None:
    """#1962 axis 1: writer must not invent out-of-plan citations."""
    template = Path("scripts/build/phases/linear-write.md").read_text(encoding="utf-8")
    assert "plan_references" in template
    assert "Knowledge Packet" in template or "writer_tool_calls" in template
```

**Axis 2 test** (gate behavior):

```python
def test_long_uk_ceiling_exempts_citation_grounded_source_blockquote() -> None:
    """#1962 axis 3: source blockquotes (textbook citations) exempt from
    long_uk_ceiling; learner practice blockquotes still under ceiling."""
    text = (
        "## Дієслова на -ся\n\n"
        "> **Караман, 10 клас, с. 176:** *Дієслова із суфіксом -ся(-сь), які виражають "
        "зворотну дію, називаються зворотними: навчатися, закохатися. Сучасний дієслівний "
        "суфікс -ся(-сь) — це давня коротка форма зворотного займенника себе в Зн. в. однини: "
        "Я не боюся. — Я ся не бою (діал.). Уживається -ся(-сь) після інфінітивного суфікса.*\n\n"
        "## Мій ранок\n\n"
        "> Спочатку прокидаюся, потім вмиваюся і одягаюся, після цього снідаю і п'ю каву, "
        "нарешті йду на роботу — це мій типовий ранковий розпорядок без жодних відхилень.\n"
    )
    grounding_evidence = {
        "matched": ["Караман Grade 10, p.176"],
        "blockquotes_checked": [
            "> **Караман, 10 клас, с. 176:** *Дієслова із суфіксом -ся(-сь), які виражають зворотну дію..."
        ],
    }
    plan = {"level": "a1", "sequence": 20, "word_target": 1200}
    report = linear_pipeline._long_uk_ceiling_gate(
        text, plan, grounding_evidence=grounding_evidence
    )
    # Source blockquote (Караман) is exempt; learner practice block IS under ceiling
    # but its content is short enough OR has gloss → may or may not flag depending on length.
    # Assertion: the Караман blockquote does NOT appear in offending_runs.
    offending = report.get("offending_runs", [])
    assert not any("Караман" in run for run in offending), (
        f"Karaman source blockquote should be exempt; got offending: {offending}"
    )


def test_long_uk_ceiling_still_flags_uncited_learner_blockquote() -> None:
    """Without grounding evidence, learner practice blockquotes still flagged."""
    text = (
        "## Мій ранок\n\n"
        "> Спочатку прокидаюся о сьомій ранку коли ще темно за вікном потім швидко "
        "вмиваюся холодною водою бо нагрівач зламався і одягаюся в найтепліший одяг "
        "щоб не змерзнути коли поспішаю до автобуса о восьмій тридцять.\n"
    )
    grounding_evidence = {"matched": [], "blockquotes_checked": []}
    plan = {"level": "a1", "sequence": 20, "word_target": 1200}
    report = linear_pipeline._long_uk_ceiling_gate(
        text, plan, grounding_evidence=grounding_evidence
    )
    # No grounding → block is under ceiling → would flag if >28 UK words without gloss
    # Block above has ~40 UK words; should be in offending_runs OR passed=False
    assert report.get("offending_runs") or report.get("passed") is False
```

**Axis 3 test** (citation matcher fuzzy):

```python
def test_citation_matcher_allows_small_page_drift_same_author_grade() -> None:
    """Кравцова Grade 4 p.112 should match plan_ref Кравцова Grade 4 p.113."""
    # ... import citation_matcher and exercise it with the two strings
    # ... assert match returned with author + grade equal, page within tolerance


def test_citation_matcher_rejects_different_grade_even_small_page() -> None:
    """Different grade = different lesson, never match."""
    # ... assert no match between Аврамченко 6 клас vs plan_ref Кравцова 4 клас
```

Adapt test signatures and fixtures to whatever the actual citation_matcher API takes; the assertion intent is what matters.

---

## Execution steps (numbered)

1. **Pre-read** (see Pre-read section above). If file structure has drifted, STOP and report.

2. **Axis 1**: edit `scripts/build/phases/linear-write.md` to add 3 directives. Run any prompt-content tests after each.

3. **Axis 2**: modify `_long_uk_ceiling_gate` + `_unsupported_run_segments` signatures to accept `grounding_evidence`. Update the call-site in `run_python_qg`. Implement the exemption logic.

4. **Axis 3**: tighten or soften `citation_matcher.py` to support ±5 page drift for same author + grade.

5. **Add tests** (~8-10 fixtures across all axes).

6. **Run full test suite:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/a1-shape-contract-2026-05-13 && /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/pytest tests/build/test_linear_pipeline.py -v 2>&1 | tail -30
   ```
   Quote final summary. Per #M-7, pytest locally before push.

7. **Lint:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/a1-shape-contract-2026-05-13 && /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/ruff check scripts/build/ tests/build/ 2>&1 | tail -5
   ```
   Quote final line.

8. **Commit:** conventional message + `Closes #1962 gates 2-4` + X-Agent trailer + Co-Authored-By Codex.

9. **Push branch.**

10. **Open PR (NO auto-merge).** Title: `fix(a1-m15-24-contract): bundled implementation — writer prompt + gate counter + matcher (#1962 gates 2-4)`. Body references the Decision Card.

11. **Print PR URL.**

---

## Acceptance criteria

- [ ] Branch pushed; PR opened; URL printed.
- [ ] All new tests pass + existing tests still green.
- [ ] `ruff check` clean.
- [ ] Commit body has `Closes #1962 gates 2-4` + X-Agent trailer.
- [ ] PR body references Decision Card `docs/decisions/pending/2026-05-13-a1-m15-24-shape-contract.md`.

## On halt

- File structure significantly different from brief expectations → STOP, report what's different. The design depends on `_unsupported_run_segments`, `_count_uk_dialogue_lines`, `citation_matcher.py`, and `scripts/build/phases/linear-write.md` existing roughly as the brief describes.
- Pre-existing main-red tests (#1958 `test_a1_20_plan_context_matches_phase_4_contract` + `test_no_writer_rewrite_in_correction`) appear → quote them in your final report but DON'T try to fix them.
- Citation matcher is more complex than the simple author/grade/page skeleton → adapt the page-tolerance change to whatever shape exists; preserve exact-match-first hierarchy.
- Axis 3 (page tolerance) regression on existing citation-matcher tests → tighten tolerance from ±5 to ±3 or smaller. The Decision Card's default is provisional.

Do NOT widen scope beyond these 3 axes. Card 2 (V7 rollout failure taxonomy) and #1960 (wiki ingestion gap) are deferred.

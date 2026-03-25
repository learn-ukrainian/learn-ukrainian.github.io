# Session Handoff — 2026-03-25

## What was accomplished

### A2 Plans (53 new, 60/60 total)
- All A2 plans written (M08-M60), Gemini adversarial reviewed
- 3 fixes applied from Gemini review (із Львова→зі Львова, свято classification, майбутнє spelling, казати alternation rule)
- All pass `check_plan.py a2` (60/60)

### A1 Batch Build (48 modules, avg 9.0/10)
- M08-M55 built with `gemini-tools` writer, Claude cross-agent reviewer
- 47/48 pass (98%), 1 stub (M37 i-eat-i-drink: 338 words)
- 123,564 total words across 55 modules
- Score range: 8.6 (M44 linking-ideas) to 9.6 (M51 my-plans)
- Batch script: `scripts/batch_build_a1.sh`

### A2 Test Builds (4 modules, all pass)
- M48 comparison: 9.2/10 (gemini→claude fallback)
- M44 relative-clauses: 9.4/10 (gemini, first pass)
- M39 imperative-complete: 9.5/10 (claude-tools + improved prompt)
- M38 motion-verbs: 9.1/10 (gemini-tools, first pass)

### B1 + HIST Test Builds (need prompt work)
- B1 M08 alternation-vowels: 7.2/10 — word count issues (context anxiety)
- HIST M23 danylo-halytskyi: 5.3/10 — seminar prompt needs tuning
- Root cause found: skeleton step was silently failing for -tools writers (fixed)

### V6 Pipeline Enhancements
- **4 writer modes**: `gemini`, `gemini-tools`, `claude`, `claude-tools`
  - `-tools` variants have MCP access (VESUM, RAG, pravopys, Wikipedia) during writing
  - Gemini MCP configured: `gemini mcp add rag http://127.0.0.1:8766/sse -t sse --trust`
  - Improved tool prompt from Gemini consultation: explicit triggers, batching, concrete examples
- **Stub detection**: <100 word outputs retried without wasting correction attempt
- **Post-error friction auto-query**: searches ALL friction files on failure, injects matching hints
- **Review versioning**: saves all rounds (review-r1.md, r2.md...), extracts structured findings to YAML
- **Skeleton/vocab fix**: `-tools` writers now correctly dispatched in all pipeline steps
- **fill_template multi-pass**: nested placeholders (QUALITY_DIMENSIONS containing {IMMERSION_RULE}) now resolved
- **Exercise instructions**: DSL `title:` field now passed as `instruction` prop to all 5 React components

### Quality Infrastructure
- 4 new global frictions from aggregated MINOR findings (gf-008 through gf-011)
- Aggregation script tested: extracts findings from all review files, groups by dimension
- CLAUDE.md updated for V6 pipeline references

### Issues Created
- #1027: Review versioning (partially implemented)
- #1028: MINOR findings → prompt improvements (aggregation done, frictions added)
- #1029: Orchestration folder discoverability
- #1030: A1 quality pass — targeted rewrites to reach 9.5+
- #1031: Investigate Figma MCP + textbook image integration
- #1032: Restructure CLAUDE.md — path-scoped rules, under 200 lines
- #1033: Anthropic harness patterns — context anxiety, reviewer calibration

## What needs doing next session

### PRIORITY 1: Restructure CLAUDE.md (#1032)
- Split into path-scoped `.claude/rules/` files
- Target: CLAUDE.md under 100 lines, all detail in rules/
- Verify `paths:` frontmatter and `@path` imports work (fact-checked against official Anthropic docs)
- CLAUDE.local.md is NOT a real feature — use `~/.claude/CLAUDE.md` for personal prefs
- Fast (~1 hour), high impact on everything downstream

### PRIORITY 2: A1 Quality Pass (#1030)
- Fix M37 (rebuild — stub) and M38 (rebuild — no exercises)
- Targeted section rewrites on 8.x modules using review findings
- Strategy (from Gemini): fix PROMPT first (done — 4 frictions added), then fix CONTENT
- Hybrid approach: simple fixes via find/replace, structural fixes via section re-generation
- Target: avg 9.0 → 9.3+ (stretch 9.5)

### PRIORITY 3: A2 Batch Build
- 53 plans ready, 4 test builds proven (9.1-9.5)
- Use same batch pattern as A1: `gemini-tools` writer, Claude reviewer
- Wait until after A1 quality pass to benefit from prompt improvements

### PRIORITY 4: Figma MCP Investigation (#1031)
- 15,406 textbook images in RAG, searchable via `mcp__rag__search_images`
- Figma MCP enables design→code for lesson layouts
- Could transform text-heavy modules into textbook-style visual experiences

### PRIORITY 5: B1/HIST Prompt Engineering (#1033)
- Context anxiety causes short outputs on 4000+ word modules
- Section-by-section generation with context resets needed
- Reviewer calibration drift — need golden reference modules
- Not blocking A1/A2 work

## Key Technical Notes

### Writer mode defaults
```bash
# A1-A2 (2000 words, English explanation)
.venv/bin/python scripts/build/v6_build.py a1 8 --writer gemini-tools

# B1+ (4000 words, Ukrainian immersion) — needs prompt work first
.venv/bin/python scripts/build/v6_build.py b1 8 --writer gemini-tools --skeleton

# Seminars (5000 words, 100% Ukrainian) — needs prompt work first
.venv/bin/python scripts/build/v6_build.py hist 23 --writer gemini-tools
```

### Cross-agent review enforcement
- gemini / gemini-tools → Claude reviews
- claude / claude-tools → Gemini reviews

### Gemini MCP setup (already configured)
```bash
gemini mcp list  # should show: ✓ rag: http://127.0.0.1:8766/sse (sse) - Connected
```

### Global frictions (new this session)
- gf-008: No LLM filler phrases
- gf-009: Exercise items must be explicitly taught in prose
- gf-010: Quiz answer position randomization
- gf-011: No spatial metaphors for abstract grammar rules

### Anthropic doc fact-checks (for #1032)
- ✅ "Under 200 lines" is official Anthropic recommendation
- ✅ Path-scoped rules with `paths:` frontmatter works
- ✅ `@path` imports in CLAUDE.md work
- ❌ CLAUDE.local.md is fabricated — use `~/.claude/CLAUDE.md`
- ✅ CLAUDE.md loaded as user message, not system prompt
- ✅ Auto-memory: first 200 lines of MEMORY.md only

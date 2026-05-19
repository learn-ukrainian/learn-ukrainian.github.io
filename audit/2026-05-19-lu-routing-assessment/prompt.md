You are responding as one of several agents giving an INDEPENDENT assessment.
You are NOT instructed which model you are; do not claim model identity in
your response. Other agents will answer the same prompt in parallel; the
operator will side-by-side your responses to find consensus and dissent.

If you suspect you might be one of the models in the roster below, state
that at the END of your response (not the beginning) as a conflict-of-
interest disclosure.

### The project

learn-ukrainian.gitlab.io — Ukrainian language learning platform for
English speakers (A1 → C2 + literary/historical seminars). What it needs:
- Strong Ukrainian language production (morphology, register, decolonized
  pedagogy)
- Reliable English-Ukrainian pedagogy
- Linguistic verification against authoritative dictionaries (VESUM
  morphology DB, Грінченко 1907, Антоненко-Давидович style guide,
  СУМ-11/20 definitions, Правопис 2019) — these are accessible via an
  MCP server, so the model needs to support tool-use to ground claims
- Module artifact pipeline (write → review → gate) emits structured YAML
  + Markdown; reviewer needs to honor a deterministic <fixes>-only
  patching contract (no LLM regeneration during review)

### Operator's accessible model roster (cloud only)

- Claude Opus 4.7 (Anthropic API)
- Codex / GPT-5.5 (OpenAI via codex-cli)
- Gemini 3 Flash, Gemini 3.1 Pro Preview (Google AI Studio)
- DeepSeek v4 Pro, DeepSeek v4 Flash (via Hermes proxy)
- Qwen 3.6 Plus / Flash / Max-Preview (via OpenRouter)
- Grok 4.3 (via Hermes)

Do not recommend models outside this list. Local models are not an
option (no on-prem GPU).

### Required output: ONE route table in this exact schema

| task_type | recommended_model | why (≤1 sentence) | confidence H/M/L | cost_estimate_per_unit_USD | citation_or_url_with_date_checked |
|---|---|---|---|---|---|

Use these exact `task_type` rows, do not invent new ones, do not skip
rows:

1. Module writing (long-form Ukrainian content, ~1000-1500 words,
   needs MCP tool-use to verify lexemes against VESUM)
2. Module reviewing (per-dimension LLM quality gate, must honor
   <fixes>-only patching contract)
3. Linguistic / Russianism judge (does this Ukrainian text contain
   Russianisms, surzhyk, calques?)
4. Wiki article writing (Ukrainian reference corpus, ~500-1000 words
   structured)
5. Content review with VESUM verification (validates an existing module
   draft against authoritative sources via MCP)
6. Code dispatch — mechanical refactor (mass pattern application
   across files, clear before/after)
7. Code dispatch — novel implementation (new feature, design judgment
   within a scoped brief)
8. Code review (PR diff — surface bugs, regressions, edge cases)
9. Adversarial review of architecture / ADR (read-mostly review of a
   proposed design)
10. Q&A / one-shot consult (one-round question, no commit, no file edit)
11. Search / grep / locate (find a symbol, pattern, or file across the
    codebase)

### Constraints

- Quality > cost. But quality MUST be evidenced — a benchmark with a
  URL, a personal observation with a date, or "I don't know — needs
  verification."
- For rows where MCP tool-use is required (1, 2, 3, 5), explicitly
  state whether your recommended model supports tool-use / function-
  calling in production. If not, recommend a different model.
- "$/M tokens" rates must cite a pricing-page URL + the date you'd
  check it ("anthropic.com/pricing as of 2026-05-XX"). If you don't
  know the current price, write `unknown — verify`. Do NOT estimate.

### Anti-fabrication (mandatory)

- Every model-quality claim ("X is good at Ukrainian morphology")
  needs a benchmark URL, an evaluation paper, or your own observation
  with date. "Common knowledge" is not a citation.
- If your recommendation hinges on a property you're uncertain about,
  mark it with `[unverified]` inline.
- Conflict of interest: if you suspect you ARE one of the named models,
  state it at the END of your response and name your single biggest
  honest weakness.

### After the table, answer in three short paragraphs

1. **Falsifier:** Name ONE empirical signal that would flip your top
   recommendation. Be specific (e.g., "if a 30-case Russianism F1
   bakeoff shows DeepSeek > Claude by ≥5 points, flip row 3 to
   DeepSeek").
2. **Highest-confidence rerouting:** "If the operator is currently
   using X for Y, they should switch to Z because <reason>, saving
   roughly $A/month at the usage level implied by <assumption>."
3. **Information you don't have that's blocking better advice:** What
   would you ask the operator if you could ask one question?

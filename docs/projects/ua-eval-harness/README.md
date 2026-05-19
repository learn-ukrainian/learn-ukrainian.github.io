# Project: Ukrainian Calque + Grammar Evaluation Harness

> **Status:** Scoping. We want to build this for **UNLP 2027** publication. Scope: a dedicated LLM evaluation harness covering both **calque** (Russianism / contact-borrowing patterns) and **grammar** in Ukrainian generation.

> **For future sessions: this is the canonical pick-up entrypoint.** When the user says "let's continue the eval harness work" or asks about the UNLP project, read this file first.

## TL;DR

Build a **dedicated LLM evaluation harness for Ukrainian calques AND grammar errors** on top of the **UA-GEC** gold-tagged subset. Open-source, non-commercial, CC-BY-4.0 attribution preserved. **Publication target: UNLP 2027** (UNLP 2026 submission window already closed).

Two coupled dimensions because (a) no dedicated harness exists for either today, (b) UA-GEC already tags both calques (F/Calque) and grammar (G/Case, G/Gender, etc.), and (c) a single harness with two scoring axes is cheaper and more useful than two separate harnesses.

## Why this exists

LLMs reliably produce Russianisms, calques, and grammar errors when generating Ukrainian text, even when prompts explicitly forbid them. The curriculum project ran into this firsthand: Claude Opus 4.7, asked to translate English → Ukrainian with explicit "avoid Russianisms," still produced 3 Russianisms in 70 words (`приймати участь`, `слідуючі пункти`, `у любий момент`). Public reproducer: `anthropics/claude-code#59146`.

The public landscape (verified 2026-05-19):

- **UA-GEC** has 2,397 human-annotated F/Calque examples plus G/Case, G/Gender, F/Collocation, and other grammar/fluency tags. Only Ukrainian gold-tagged corpus with this shape. License CC BY 4.0. ([github.com/grammarly/ua-gec](https://github.com/grammarly/ua-gec))
- **LanguageTool** has a rule-based Ukrainian module — adjacent rules, not LLM-eval-shaped.
- **lang-uk leaderboard** benchmarks LLM *adaptation* to Ukrainian (translation/reasoning/QA/IFEval) — explicitly does NOT cover calque or grammar. ([huggingface.co/spaces/lang-uk/ukrainian-llm-leaderboard](https://huggingface.co/spaces/lang-uk/ukrainian-llm-leaderboard))
- **Karpov & Chernodub (UNLP 2026):** *"How Far Can Prompting Go for Minimal-Edit Ukrainian Grammatical Error Correction?"* — adjacent work on UA grammar error CORRECTION. Different shape (correction, not eval-as-leaderboard).
- **Pravopysnyk** has a synthetic *corrupter* (uk → ru → heuristic) — useful for prompt augmentation, not scoring.
- **Curriculum project** has the *scorer* — a deterministic ~50-pattern Russianism + calque detector currently running as a build-time gate across the V7 module pipeline.

**The gap:** no LLM-evaluation harness with prompts engineered to elicit calques + grammar errors, paired with cross-model leaderboard scoring against UA-GEC gold tags. That is what we want to build.

## Scope

1. **Two scoring axes:** calque (F/Calque + adjacent F/* tags) AND grammar (G/* tags from UA-GEC).
2. **UA-GEC** as the gold set. Full attribution + CC-BY-4.0 propagation.
3. **Source-language-agnostic schema** from day one: `source_lang: ru | pl | en | …`. Russian first because that is where the empirical LLM harm concentrates today.
4. **Permanently non-commercial open-source** (matches the curriculum project's posture; see `CLAUDE.md` non-commercial-permanent decision 2026-04-19).
5. **Target UNLP 2027** for publication.

## Adjacent assets we already have

These are NOT the harness, but they are the scorer-side foundation:

- **Deterministic calque detector** — ~50 patterns + scoring function, gating every V7 module build. Russian-only, smaller pattern set than UA-GEC's gold data. Lives in `scripts/audit/` (Russianism gate). Worth wiring as one of the scorers in the harness.
- **Multi-model writer bakeoff** — `audit/2026-05-19-multi-agent-routing-assessment/REPORT.html` covers ~12 frontier models (Claude, GPT-5.5, Gemini, Grok closed-source; DeepSeek, Qwen, Mistral, Kimi, MiniMax, Ring, GLM open). Calque/Russianism signal is graded; generation-side data the lang-uk leaderboard does not cover.
- **VESUM** — 6.7M Ukrainian forms, used for morphological verification. Available via `mcp__sources__verify_word`.
- **Антоненко-Давидович** — 342 structured Russianism entries + 169 prose chunks. Available via `mcp__sources__search_style_guide` and `mcp__sources__search_text source=antonenko-davydovych-yak-my-hovorymo`.
- **СУМ-11 + Грінченко + ЕСУМ + slovnyk.me** — heritage-defense layer (`mcp__sources__search_heritage`) to avoid false-positives on authentic Ukrainian archaisms/dialectisms.
- **UA-GEC errors index** — already MCP-exposed via `mcp__sources__search_ua_gec_errors` (filtered to F/Calque, F/Collocation, G/Case, G/Gender). 8,937 rows.

## Design TBD (these are the questions next session should answer)

### Eval shape — calque axis
- Prompt-elicitation: what task family elicits calques best? (Translation EN→UK? Free generation in UK? Continuation from UK seed? Conversation-completion?)
- Coverage: how many UA-GEC F/Calque examples form the eval set? Hold-out for validation?
- Scoring: exact-match against gold edit-pairs? F1 over flagged spans? Semantic-equivalence aware?
- Calibration: how do we compare LLM output to UA-GEC's human-edit format (which is corrective, not generative)?

### Eval shape — grammar axis
- Which G/* tags do we score? G/Case, G/Gender, G/Number, G/Aspect, G/Verb? All?
- Same prompt family as calque axis, or separate prompts that elicit grammar mistakes specifically?
- Joint vs separate leaderboard: one ranking with two columns, or two separate rankings?

### Models in scope
- Closed-source frontier: Claude, GPT-5.5, Gemini, Grok
- Open-source frontier: DeepSeek, Qwen, Mistral, Kimi, MiniMax
- Plus open-weight UA-fine-tuned: Lapa, MamayLM (covered by lang-uk leaderboard)
- Cost ceiling per full eval pass

### Repo layout
- Standalone repo or sub-project of `learn-ukrainian`?
- Naming: `ua-eval-harness`? `uk-russian-shadow-eval`? `ua-gec-llm-eval`?
- Reproducibility: requirements pinned, results-versioned, model-version-captured

## Out of scope for this project

- **Surzhyk-specific eval (spoken register)** — calques are a subset of Surzhyk patterns; an eval scoped narrowly to spoken-register Surzhyk is a different shape and could be a follow-on project.
- **Polonisms, anglicisms as primary scope** — schema supports them via `source_lang`, but Russian is priority-1 because that is where empirical LLM harm concentrates today.
- **General Ukrainian LLM capability** — covered by the lang-uk leaderboard.

## Timeline anchors (loose)

- **2026-05** — scoping (this doc).
- **2026-mid to 2026-late** — eval design draft + early results.
- **2027-Q1** — paper draft.
- **2027-05 (typical UNLP timing)** — UNLP 2027 conference.

These are loose. Adjust as design firms up.

## Cross-references

- v1 multi-agent routing audit: `audit/2026-05-19-multi-agent-routing-assessment/REPORT.html`
- Curriculum non-commercial-permanent decision: `CLAUDE.md` (2026-04-19)
- UA-GEC repo: https://github.com/grammarly/ua-gec
- UA-GEC license: CC BY 4.0
- Anthropic Russianism reproducer: anthropics/claude-code#59146
- UNLP: https://unlp.org.ua/
- lang-uk leaderboard: https://huggingface.co/spaces/lang-uk/ukrainian-llm-leaderboard
- Karpov & Chernodub (UNLP 2026 paper): TBD URL when published
- GitHub tracker: see "Issue tracker" section below.

## Pick-up checklist (for the next session that resumes this)

When you come back to this in a week / month / quarter:

1. Read this file in full.
2. Check the GitHub issue (linked below) for any inbound comments / status changes.
3. Check `docs/decisions/` for any related decisions filed since.
4. Read `audit/2026-05-19-multi-agent-routing-assessment/REPORT.html` §5 (writer bakeoff) and §1 finding #4 — the closest existing data points.
5. Confirm UNLP 2027 timing — adjust the timeline section above if dates have firmed up.
6. If the eval design has not been drafted yet, that is the next-action item.
7. If a draft exists, link it from the "Design TBD" sections above.

## Issue tracker

Primary GitHub issue: **[#2156 — Project: UA calque + grammar eval harness (UNLP 2027 target)](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/2156)** (filed 2026-05-19).

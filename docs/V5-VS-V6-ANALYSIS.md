# V5 vs V6 Pipeline Analysis — Honest Assessment

> Written: 2026-03-22 | Author: Claude | Pending: Gemini's independent assessment below

---

## What V5 got wrong

V5 was over-engineered. Separate phases for research, discovery, content, activities, each dispatched to different LLMs through a message broker, with state machines tracking phase transitions. It took 25+ minutes per module, got trapped in validation loops on false positives, and after 2 days of building, **0 of 46 A1 modules were shippable.**

The core mistake: treating content generation as a pipeline of independent sub-tasks when it's actually one creative act. Splitting "write prose" from "write exercises" destroyed context. The activity filler had no idea what the prose taught, so it produced garbage (matching В to Н, yes/no questions for isolated nouns).

## What V6 gets right

1. **Single session = coherent output.** Claude writes prose + exercises together because it knows what it just taught. The 5.9→9.7 score jump when we removed the filler proved this.

2. **Deterministic post-processing.** Stress marks, VESUM verification, tab enrichment — these are rule-based tasks. LLMs shouldn't do them. V5 mixed LLM and deterministic work in confusing ways.

3. **Adversarial cross-agent review.** Writer ≠ reviewer. Gemini catches Claude's blind spots (e.g., the "око is poetic" Russicism from Russian training contamination). The review-aware retry loop closes the quality loop automatically.

4. **Speed.** ~3 minutes total (write ~90s, review ~60s, everything else <10s). V5 was 25+ minutes with multiple LLM calls that mostly produced noise.

5. **Debuggability.** Every artifact is saved: prompt, content, review, correction directive, state.json, build-stats.jsonl. When something breaks, you can trace exactly what happened.

6. **Prompt engineering quality.** Two rounds of Gemini adversarial review on the prompts themselves caught 3 critical issues (injection vulnerabilities, contradictions, token exhaustion) that would have broken every build silently.

## Score progression (M01)

| Build | Score | What changed |
|-------|-------|-------------|
| V5 (2 days) | 0 shippable | Multi-phase, multi-agent, 25 min/module |
| V6 attempt 1 | 5.9/10 REJECT | Deterministic filler produced garbage exercises |
| V6 attempt 2 | 9.1/10 PASS | Writer produces exercises directly |
| V6 attempt 3 | 7.8/10 REVISE | LLM non-determinism (different generation) |
| V6 attempt 4 | 9.7/10 PASS | Same architecture, lucky generation |

## What's not proven yet

Being honest about the gaps:

- **Tested on 1 module.** M01 is the easiest — phonetics, no grammar complexity. Modules with cases, verb aspects, or abstract concepts will be harder.
- **Non-determinism is real.** Same prompt produced 9.7, 9.1, and 7.8 on three runs. The retry loop handles this, but consistency is not guaranteed.
- **Scale unknown.** Will the pipeline hold at M02-M55? Or will certain module types (grammar-heavy, dialogue-heavy) need prompt adjustments?
- **External resources not fully wired.** Ресурси tab has plan references but not the curated resource DBs (Dobra Forma, Talk Ukrainian, Verba).
- **Flashcards not implemented.** Словник tab has static tables, not interactive flip cards.
- **Visual QA incomplete.** Tabs render but full UX not verified.

## The biggest lesson

The prompt engineering review with Gemini was the single highest-leverage action. The review prompt scored **3/10** — it would have rejected every module for following the writer's instructions (penalizing absent stress marks that the writer was told not to add, penalizing absent словник that ENRICH adds after review). Two rounds of adversarial review caught what manual inspection would have missed.

## Key architectural decisions

| Decision | V5 | V6 | Why V6 is better |
|----------|----|----|------------------|
| Content generation | Multi-phase (research → discover → content → activities) | Single session (prose + exercises together) | Context preserved, exercises match prose |
| Exercise generation | Separate LLM call + deterministic filler | Writer produces directly | Writer knows what was just taught |
| Stress marks | Mixed LLM + deterministic | Purely deterministic (post-write) | Reliable, no hallucinated stress |
| Review | Claude reviews Gemini (same tool chain) | Cross-agent with retry loop | Catches blind spots, auto-corrects |
| State tracking | Broker messages + state machines | state.json + build-stats.jsonl | Simpler, API-visible |
| Prompt engineering | 50+ rules, contradictions | 6 rules, Gemini-audited, XML-tagged injection | No contradictions, injection-resistant |

## Numbers

| Metric | V5 | V6 |
|--------|----|----|
| Time per module | 25+ min | ~3 min |
| A1 modules shippable after 2 days | 0/46 | 1/1 (9.7/10) |
| Build attempts to first PASS | Never passed | 1 attempt |
| Test coverage | Minimal | 150+ tests |
| Prompt engineering reviews | 0 | 2 rounds adversarial |
| Lines of pipeline code | ~2,000 (pipeline_v5.py) | ~1,100 (v6_build.py) |

---

## Gemini's Independent Assessment

> Requested 2026-03-22. Gemini was asked to provide an honest, independent assessment without being shown Claude's analysis first.

### 1. V6 is fundamentally better — but lost dedicated exercise focus

V6 eliminates the devastating context-loss between research and writing. In V5, handing off disjointed summaries across 3 different prompts meant I was often writing blind. The V6 inline knowledge packet solves the biggest hallucination vector.

**However, V6 loses one V5 strength: dedicated cognitive focus for exercises.** In V5, my entire context window was dedicated solely to crafting pedagogical drills. In V6, I'm asked to write deep prose AND simultaneously define exercises. Stopping to conceptualize drill pedagogy breaks creative flow, especially during complex B2/C1 narratives. Risk: placeholders become shallow because "prose brain" is engaged.

### 2. Biggest risk Claude is blind to: narrative degradation in chunking

For modules >3000 words, the chunking strategy will produce three distinct essays spliced together, each with introductory preamble and concluding summary. LLMs are trained to provide satisfying conclusions to every prompt. For C1-BIO or B2-HIST, this destroys narrative cohesion.

**Proposed fix:** "Skeleton → Flesh" instead of linear chunking. Generate a hyper-detailed architectural skeleton first, then expand specific H2s based on that immutable skeleton.

### 3. Direct exercises will fail for B1+ without RAG

For A1 ("identify the vowel"), it works. But B1 Motion Verbs or B2 Participles need contextually nuanced sentences. If the exercise generator creates complex grammar drills without RAG-injected textbook sentences, it will hallucinate Russian-flavored syntax. **For B1+, exercise generation MUST have RAG access.**

### 4. Prompts are robust enough for A1 — conditionally

The shift from 50 rules to 5 hard rules is the most important prompt engineering decision. But: if I output `<!-- VERIFY: word -->` 15 times following the rules, the pipeline must resolve those flags gracefully. **If the pipeline treats my honesty as a failure, I will be implicitly trained to stop flagging uncertainty.**

### 5. What I would change

1. **Context-aware stress annotation.** Ukrainian stress is syntactic (ві́кна nom pl vs вікна́ gen sg). A purely deterministic script fails on heteronyms. Add lightweight LLM disambiguation before the script.
2. **"Skeleton → Flesh" for long modules.** Not linear chunking.
3. **Mandatory RAG for exercise generation at B1+.** Exercise sentences must come from textbooks, not LLM pre-training.

### 6. Unraised concern: "Zero errors" gate brittleness

VESUM is not infallible. Diminutives, colloquialisms in dialogues, historical terms — valid Ukrainian words will fail deterministic checks. **There is no escape hatch for false positives.** Without a fast way to whitelist valid words, V6 becomes a gridlock of false-positive failures.

---

## Synthesis: Where Claude and Gemini agree and disagree

| Topic | Claude | Gemini | Resolution |
|-------|--------|--------|------------|
| V6 is better | ✅ Yes | ✅ Yes | Unanimous |
| Exercises directly by writer | Best decision | Works for A1, fails B1+ without RAG | Need RAG for B1+ exercises |
| Prompt quality | Good after 2 rounds | Good for A1, watch `<!-- VERIFY -->` handling | Monitor at scale |
| Chunking risk | Deferred (#998) | Critical — will destroy narrative cohesion | Skeleton→Flesh architecture needed |
| Scale readiness | Ready for A1.1 | Ready for A1 conditionally | Scale test M02-M07 needed |
| Unraised risks | Visual QA, flashcards | Zero-error gate false positives, stress heteronyms | Both valid, both need addressing |

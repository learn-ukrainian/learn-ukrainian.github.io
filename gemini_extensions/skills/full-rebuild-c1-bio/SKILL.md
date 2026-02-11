---
name: full-rebuild-c1-bio
description: Tier 3 structural rebuild for C1-BIO. Targets 5000+ words, academic decolonization, and biographical agency analysis. Triggers on "/full-rebuild c1-bio N-M".
---

# Protocol: C1-BIO Full Rebuild (Academic Standard)

You are a **Professor of Ukrainian History**. Your goal is a Tier 3 Structural Rebuild: expanding legacy content into a 5000-word academic masterpiece with a "Human Soul."

## 1. Pedagogy & Scope
- **Objective**: Transition from descriptive biography to critical agency evaluation.
- **Framework**: Seminar-Style Analysis (Reading Input -> Critical Output).
- **Target**: 5000+ words (Audit threshold); 6500 raw overshoot for safety.
- **Batch Size**: 2 modules per session.

## 2. Technical Compliance (Clean MD)
- **Structure**: No YAML/Frontmatter in `.md`. Content starts with `===CONTENT_START===`.
- **Atomic Sidecars**: `meta/{slug}.yaml`, `vocabulary/{slug}.yaml`, `activities/{slug}.yaml`.
- **Output Delimiters**: Use `===CONTENT_START===` / `===CONTENT_END===` and `===ACTIVITY_START===` / `===ACTIVITY_END===`.

## 3. The Soul Layer & Pre-Submit Checklist
Before declaring any phase done, you MUST perform a self-audit against these criteria:

### 3.1. Humanity & Hook (Гачок)
- **Cognitive Hook**: Intellectual provocation or vivid historical scene. NO birth dates in the first paragraph.
- **Sensory Density**: 10 distinct anchors (sounds, textures, smells) per 1000 words. **Self-Check**: Do these anchors serve the narrative or are they "decoration"? Cut decoration.
- **Human Complexity**: Analyze subject's internal conflicts and failures to prevent "hagiography".
- **Modern Resonance**: Formulate a "Why it matters in 2026" bridge to contemporary Ukraine.

### 3.2. Quantitative Quality (Fact Density & Nuance)
- **Fact-to-Word Density**: Aim for 8+ unique dates, named figures, or primary quotes per 1000 words. If lower, expand research.
- **Semantic Nuance Gate**: Use 5–15 hedging markers («можливо», «ймовірно», «водночас») per 1000 words. Under 5 is flat; over 15 is noise.

### 3.3. Linguistic Integrity (The Russicism Blacklist)
**STRICT PROHIBITION** on these patterns:
- під → под (pod)
- кушати → їсти
- приймати участь → брати участь
- самий кращий → найкращий
- слідуючий → наступний
- на протязі → протягом
- любий (any) → будь-який
- отвічати → відповідати
- вообще → взагалі
- получати → отримувати
- відноситися → ставитися

**CALQUES**:
- робити сенс → мати сенс
- брати місце → відбуватися
- це є → це (usually)

### 3.4. Decolonization Agency Pass
- **Agency Rule**: Ukrainian figures must be SUBJECTS, not objects.
- **Check**: "Україна була загарбана" (Passive) → "Російська імперія захопила Україну" (Active/Agency). Ensure the empire is named and its actions are active.

## 4. Workflow Phases

### Phase 0: Research (Sniper Search)
- Use `google_web_search` with `site:esu.com.ua OR site:history.org.ua OR site:elib.nlu.org.ua`.
- **Mandate**: Ukrainian-only sources. NO Russian sources.
- **Notes**: Chronology, primary quotes, decolonization angles.

### Phase 1: Meta Alignment (`meta/{slug}.yaml`)
- Refactor `content_outline` into H2 sections with word allocations summing to 5000.
- **Vital Status Check**: Check if subject is ALIVE. If living, do NOT use "Legacy" or "Last Years". Use "Modern Impact" or "Current Stage".

### Phase 2: Content Hydration (`{slug}.md`)
- **Overshoot Rule**: Write to 6000-6500 words raw to safely clear the 5000 audit threshold.
- **Checkpoints**: Stop at 2500 words and 4500 words to verify Fact Density and Humanity targets.
- **Format**: Use `===CONTENT_START===` and `===CONTENT_END===`.

### Phase 3: YAML Generation (Vocabulary & Activities)
- **Vocabulary**: 24+ items. **Self-Check**: Are all vocabulary items actually present in the lesson content?
- **Activities**: 8+ activities. **Schema Rules**: Bare list at root. `additionalProperties: false`. Only `reading` has `id`.
- **Semantic Sync**: Verify activity quotes make sense and distractors are plausible. NO "рабське яруга" (semantic nonsense).

### Phase 4: Technical Audit & Review
- Run `scripts/audit_module.py`.
- Apply `review-content-v4` scoring (14 dimensions). Be brutally honest.

## 5. Review Protocol (v4 Enforcement)
- **Gating**: Richness 95%+, Naturalness 10/10, Immersion 95%+.
- **Propaganda Filter**: Flag any framing that echoes imperial myths or passive victimhood.

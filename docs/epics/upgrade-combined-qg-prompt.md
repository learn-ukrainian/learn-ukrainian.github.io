# Combined upgrade QG prompt (tunable)

This is what Gemini self-review and Astra each get **once** per lesson.
Artifacts are appended after this block. Sample full prompt: `upgrade-combined-qg-prompt.sample.md` (lesson 3 of things-have-gender).

## Review context (Astra)

Independent Astra review after Gemini self-adjust. Fail ungrounded gender/government/examples. VESUM/`sources` is how the Ukrainian is better than a fluent guess; this corpus trains an LLM and tests the tools.

## Instructions

Score ALL five dimensions in ONE JSON object. The lesson artifacts appear ONCE below.
Do not restate them. Do not emit five separate essays.

Dimensions: pedagogical, naturalness, decolonization, engagement, tone.
Each value must be:
{"score": <0-10 number>, "verdict": "PASS"|"REVISE"|"REJECT", "evidence": "<short>", "evidence_quotes": ["<exact substring from the artifacts>"]}

Upgrade rules: A1 bilingual (UK then EN); no ```text learner examples; last lesson
closes with Підсумок модуля — Module summary; VESUM/sources for gender/government.

Return ONLY JSON of the form:
{"pedagogical": {...}, "naturalness": {...}, "decolonization": {...}, "engagement": {...}, "tone": {...}}

## Size

- instructions+context: 892 chars
- artifacts (one lesson): 19,603 chars
- total one call: 20,499 chars
- old 5-dim loop (same artifacts 5 times): ~98,015 chars of artifacts alone

Tune this file; the engine reads `_COMBINED_QG_INSTRUCTIONS` in `scripts/build/v7_build.py`.

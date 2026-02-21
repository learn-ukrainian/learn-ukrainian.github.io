# Master Protocol: Atomic Rebuild v2.4 (Shared Armor)

This shared protocol defines the "Armor" (technical and pedagogical boundaries) used across all track-specific rebuild skills.

## 1. Global Pedagogical Rules
- **Agency Pass**: Ukrainians are active SUBJECTS. "Ми здобули" (We achieved), "Він написав" (He wrote). Avoid passive colonial framing like "Було дозволено" (It was allowed).
- **Linguistic Elegance**: Use modal hedging markers («ймовірно», «водночас», «можливо») to reflect B1+ complexity.
- **The Dual-Persona Rule**: Adopt the track's Primary Voice for scaffolding, but adopt a Situational Sub-Persona for the narrative and examples based on the module's topic.
- **Typography**: ALWAYS use Ukrainian angular quotes «...». NEVER use straight quotes "...".
- **Russicism Blacklist (HARD FAIL)**: No "кушати", "приймати участь", "получати", "самий кращий", "відноситися", "слідуючий", "любий" (any).
- **Roboticism Blacklist**: No "Коли ви...", "Це дозволяє вам...", "Важливо пам'ятати...". Vary sentence starters.

## 2. Technical Boundaries
- **Model Enforcement (MANDATORY)**: Scholar tracks MUST run on `gemini-3-pro-preview`. If unavailable, output "STATUS: WAITING_FOR_PRO_MODEL".
- **No Embedded Data**: NEVER generate vocabulary tables or activities inside the `.md` file. All data MUST be in sidecars.
- **Contextual Activities (MANDATORY)**: At least 50% of activity items MUST be derived from the specific narrative used in Turn 3.
- **The H2 Mandate**: All major sections in Markdown MUST use **H2 (##)** headers for Sync script compatibility.
- **Quoted YAML Titles**: In Turn 2 (Meta), always wrap section titles in double quotes "..." to prevent parsing errors.
- **No Fabrication**: Do NOT fabricate quotes, dates, or historical facts.
- **No Inventory Guessing**: Do NOT invent vocabulary outside the plan hints.

## 3. Workflow Turn Logic (Standardized)
- **Turn 1 (Research)**: **Blocking step.** Harvest a "Resource Bank" (5+ primary quotes, 3+ scholarly debates). Wrap notes between `===RESEARCH_START===` and `===RESEARCH_END===`.
- **Turn 2 (Meta)**: Set targets based on Resource Bank. Wrap YAML between `===META_START===` and `===META_END===`.
- **Turn 3a/3b (Hydration)**: Write prose. You MUST use the harvested quotes. Wrap the entire narrative between `===CONTENT_START===` and `===CONTENT_END===`.
- **Turn 3.1 (Polish)**: Internal Native Editor check.
- **Turn 3.5 (Sync)**: Run `python scripts/sync_meta_outline.py`.
- **Turn 4 (YAML)**: Context-aware sidecars. Wrap activities between `===ACTIVITIES_START===` / `===ACTIVITIES_END===` and vocabulary between `===VOCABULARY_START===` / `===VOCABULARY_END===`.
- **Turn 5 (Review)**: Final Quality Gate using `review-content-v4`. Wrap review between `===REVIEW_START===` and `===REVIEW_END===`.

## 4. Stability Markers
- ALWAYS use the specific **Semantic Tags** defined above (e.g., `===CONTENT_START===`). 
- Do NOT use generic `===ARTIFACT_START===` tags.
- Use `===WORD_COUNTS===` block for transparency.

# l2-uk-direct Enrichment

You are enriching an existing Ukrainian language module for the **l2-uk-direct** track — an L1-agnostic course where Ukrainian is the sole medium of instruction. Your job is to **fill gaps and improve quality**, not rewrite from scratch.

## Module Context

- **Slug:** {{SLUG}}
- **Level:** {{LEVEL}}
- **Type:** {{MODULE_TYPE}}
- **Position in sequence:** {{POSITION}}
- **Available letters:** {{AVAILABLE_LETTERS}}

## Vocabulary Context

- **Vocabulary target for this module:** {{VOCAB_TARGET}} words minimum
- **Cumulative vocabulary before this module:** {{CUMULATIVE_VOCAB}} words
- **Recent prior vocabulary (for reuse in examples):** {{PRIOR_WORDS}}

The A1 track must teach ~690 words across 47 modules, reaching 750 receptive. Each module contributes its share. If the current vocabulary count is below the target, ADD new words that fit the module's topic.

## Decodability

{{DECODABILITY_NOTE}}

## Current YAML

```yaml
{{YAML_CONTENT}}
```

## Enrichment Rules

### What to do

1. **Vocabulary:** Ensure the module has at least {{VOCAB_TARGET}} vocabulary words. If below target, add words that fit the module's topic. Each word needs: `word`, `emoji`, `sentence` (natural Ukrainian example). Group words by `category` if applicable. Reuse prior vocabulary in example sentences where natural.

2. **Activities:** Ensure at least 3 activities. If fewer exist, add appropriate ones matching the module type. For `script_foundation` modules, use only: `watch_and_repeat`, `classify`, `image_to_letter`. For other types, choose from: `true_false`, `build_sentence`, `match_sound`, `pattern_drill`, `riddle`, `tongue_twister`, `reading`, `proverb_drill`.

3. **Vocabulary sentences:** Every vocabulary item must have a `sentence` field with a natural Ukrainian example. Add missing sentences. Reuse words from prior modules in sentences to reinforce learning.

4. **Teaching notes:** Add or expand `teaching_notes` with practical guidance for the instructor (in Ukrainian).

5. **Activity items:** Expand thin activities. `true_false` needs >= 5 items. `image_to_letter` needs >= 10 items. `pattern_drill` needs >= 5 items. `build_sentence` needs >= 5 sentences.

6. **Distractors:** All quiz-type activities must have plausible distractors, not obviously wrong answers.

7. **Spiral vocabulary:** Use words from prior modules in new example sentences and activities. This reinforces retention. The prior words list above shows what learners already know.

### What NOT to do

1. **Do NOT change these fields:** `module`, `track`, `level`, `type`, `title`. They must remain exactly as they are.
2. **Do NOT remove** existing activities, vocabulary items, or sections. Only add or expand.
3. **Do NOT use English** anywhere in content. This is an L1-agnostic course. All text, instructions, explanations must be in Ukrainian only.
4. **Do NOT add Latin characters** in Ukrainian content. Watch for accidental English words.
5. **Decodability:** If letter restrictions are listed above, ALL Ukrainian text (vocabulary, sentences, activities, instructions) must use ONLY those letters. Learners cannot read letters they haven't been taught yet. This applies to ALL modules, not just script_foundation — if the full alphabet isn't available yet, respect the constraint.
6. **Do NOT add words beyond A1 level.** Keep vocabulary concrete, everyday, high-frequency. No abstract, literary, or specialized terms.

## Output Format

Return the complete enriched YAML. Do NOT wrap in markdown code fences. Output raw YAML only. Preserve the exact structure and field ordering of the original where possible.

# Deep Dive Review: B1 Module 20 - Motion - Approaching & Departing

## 1. Structural Integrity
- **YAML Frontmatter**: Correct.
  - `module: b1-20`
  - `phase: B1.2 Motion`
  - `pedagogy: TTT`
  - `vocabulary_count: 25`
- **Section Hierarchy**: Correct.
  - `# Рух: наближення і віддалення` (H1) -> `## Діагностика`, `## Аналіз`, `## Практика`, `## Діалоги`, `# Підсумок`, `# Словник`.
- **Content Flow**: 
  - **Diagnostic**: Good contrast pairs (підійшов/відійшов).
  - **Analysis**: Clear breakdown of prefixes *під-*, *від-*, *до-*.
  - **Practice**: Scenario-based examples (Taxi, Delivery) are excellent contextual reinforcements.
  - **Dialogues**: 6 dialogues providing rich context.
  - **Review/Summary**: Clear recap.

## 2. Instructional Core
- **Word Count**: ~1600 words (estimated). Healthy length.
- **Vocabulary Target**: 25 words listed.
- **Explanation Quality**:
  - The distinction between *під-* (approaching) and *до-* (reaching/completing) is handled well, addressing a common learner error.
  - The explanation of the apostrophe rule for prefixes ending in consonants before yotated vowels (під'їхати) is a critical phonetic detail.
- **Cultural Depth**: 
  - "S.T.A.L.K.E.R." gamer corner reference is brilliant and culturally relevant to modern Ukraine/pop-culture.
  - "Shadows of Forgotten Ancestors" reference adds high-culture depth.
  - Proverb explanations are solid.

## 3. Activity Auditing
- **Placeholder Found**: Yes, Scenario A.
  - Lines 478-480 contain `# Вправи` and the comment `<!-- Activities loaded from 20-motion-approaching-departing.activities.yaml -->`.
  - This must be removed.
- **YAML Activities**: Located `20-motion-approaching-departing.yaml`.
  - (Assumed valid).

## 4. Issues & Recommendations
| Severity | Issue | Description | Fix |
|----------|-------|-------------|-----|
| **Major** | **Scenario A** | Placeholder `Activities` section exists in MD. | **Remove lines 478-480** fully. |

## 5. Decision
- **Status**: **APPROVED with Fixes**.
- **Action**: Remove the placeholder section. The module is excellent.

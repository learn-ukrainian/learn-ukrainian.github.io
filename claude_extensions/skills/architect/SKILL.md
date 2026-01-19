---
name: architect
description: Generates a detailed 'content_outline' for a module based on its template and focus. Use this to "hydrate" skeleton modules before content generation.
allowed-tools: Read, Write, Grep
---

# Architect Skill

## Purpose
To generate a structurally rigorous `content_outline` in the module's `meta/{slug}.yaml` file. This outline serves as the "blueprint" for the content writer, ensuring word count targets are met and all pedagogical requirements are satisfied.

## Inputs
1.  **Target Module Meta**: `curriculum/.../meta/{slug}.yaml`
2.  **Level Template**: `docs/l2-uk-en/templates/{level}-{focus}-module-template.md` (or closest match)

## Output
A `content_outline` list appended to the meta YAML, where the sum of `words` equals the module's `word_target`.

## Algorithm

1.  **Read Meta**: Identify `title`, `focus`, `level`, and `word_target` (e.g., 4000 words).
2.  **Find Template**: Locate the correct template in `docs/l2-uk-en/templates/`.
3.  **Analyze Structure**: Extract the required H2 sections from the template (e.g., "Вступ", "Біографія", "Історичний контекст").
4.  **Budget Words**: Distribute the `word_target` across sections based on their weight.
    *   *Example (Biography):* Intro (10%), Bio (40%), Context (20%), Comparison (20%), Legacy (10%).
5.  **Generate Points**: For each section, write 3-5 specific, historically accurate bullet points based on the Module Title.
    *   **CRITICAL:** All points MUST be written in **Ukrainian** to ensure consistency with the `CLAUDE.md` "Curriculum content only" rule and to facilitate high-quality generation in the target language.
6.  **Update YAML**: Use `replace` or `write_file` to insert the `content_outline` into the meta file.

## Example Output Structure

```yaml
content_outline:
  - section: "Вступ"
    words: 400
    points:
      - "Історичний контекст XIX століття"
      - "Значення постаті [Ім'я]"
  - section: "Біографія"
    words: 1200
    points:
      - "Ранні роки в [Місце]"
      - "Ключові досягнення"
```

## Usage
When a module is missing an outline, run:
`Activate Skill: architect` -> "Hydrate module [X]"

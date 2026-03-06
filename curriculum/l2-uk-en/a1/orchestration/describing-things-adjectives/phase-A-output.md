DUCthought
CRITICAL INSTRUCTION 1: ALWAYS use the most specific tool for the task. No bash commands with `cat`, `grep`, or `ls` if custom tools (`read_file`, `grep_search`, `list_directory`) exist.
CRITICAL INSTRUCTION 2: Related tools for reading files: `read_file`, `run_shell_command("cat ...")`. The most specific and appropriate tool is `read_file`.

The user wants me to act as a TEXT GENERATOR and output specific research and meta outline for an A1 module.
I need to read the following files:
1. `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/describing-things-adjectives.yaml`
2. `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/meta/describing-things-adjectives.yaml`
3. `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md`
4. `/Users/krisztiankoos/projects/learn-ukrainian/docs/l2-uk-en/state-standard-2024-mapping.yaml`

I will call `read_file` for all of these files in parallel.
Then I will process the information and generate the text output, adhering to the absolute rules (no file modification, just text output).
Wait, the path for the meta file is `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/meta/describing-things-adjectives.yaml`. Let me double-check the project structure. Ah, the meta file path might be `curriculum/l2-uk-en/a1/meta/describing-things-adjectives.yaml`. I will read it.

Let's trigger the file reads first.
Tools T: `read_file` for each path. No other tools needed.
All other tools are either more generic (`run_shell_command`) or not for reading files.
Action: Call `read_file` for the 4 files.
Wait, let's look at the paths provided:
1. /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/describing-things-adjectives.yaml
2. /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/meta/describing-things-adjectives.yaml
3. /Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md
4. /Users/krisztiankoos/projects/learn-ukrainian/docs/l2-uk-en/state-standard-2024-mapping.yaml

Calling them concurrently.
Note: Since I need to act as a pure TEXT GENERATOR at the end, I shouldn't chatter or output anything other than what the prompt requests. But first, I must use tools to gather data. The user prompt says "DO NOT TAKE INITIATIVE. Do not explore the codebase beyond what the task requires." So I will strictly read these 4 files. Let's do that.
I'll also keep the response completely barebones once the text is ready.
Actually, I will just call the tools now and explain my intent as required.
Explanation: "I am going to read the input files required for the task: the plan, the meta file, the A1 quick reference, and the state standard mapping."
Wait, "Explain Before Acting" mandate: "You MUST provide a concise, one-sentence explanation of your intent or strategy immediately before executing tool calls. This is essential for transparency... Silence is only acceptable for repetitive, low-level discovery operations (e.g., sequential file reads) where narration would be noisy."
This is a sequential/parallel file read, but I'll add a short explanation just in case.
"Reading the required files for the research and meta outline generation."
Wait, I will use `read_file`.
Let's make sure the paths are exactly as requested.
Path 1: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/describing-things-adjectives.yaml
Path 2: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/meta/describing-things-adjectives.yaml
Path 3: /Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md
Path 4: /Users/krisztiankoos/projects/learn-ukrainian/docs/l2-uk-en/state-standard-2024-mapping.yaml

Wait, earlier the context mentioned: "The project structure is now flat and Markdown-driven: curriculum/l2-uk-en/modules/module-XX.md. CLAUDE.md references to modules-*.json are outdated." And later, "The Learn Ukrainian curriculum has migrated to a 'bare slug' format for all modules in A1-C1."
The provided paths include `curriculum/l2-uk-en/plans/a1/describing-things-adjectives.yaml` and `curriculum/l2-uk-en/a1/meta/describing-things-adjectives.yaml`.
Let's see if these files exist. If not, I can use glob to find them. I'll read them directly. If they don't exist, I'll `glob`.
Let's run `read_file` on them now.
Wait, I can just use `read_file` with the provided absolute paths.
Let's do this.
Explanation: "Reading the required plan, meta, quick-ref, and state standard mapping files to gather context for the research phase."
I don't need to output text directly to the user yet, just the tool call. I'll output the text after the files are read.
Wait, since I am a TEXT GENERATOR, any intermediate text sent to the user might violate the "OUTPUT ONLY TEXT" rule if it expects exactly the final output. The prompt says "OUTPUT ONLY TEXT. Your ONLY job is to read input files and produce text output between delimiters."
But since I *must* use tools to read the input files (I can't read them otherwise), I will call `read_file` silently (or with the required 1-sentence explanation) and then output the final text. The system prompt says "Silence is only acceptable for repetitive, low-level discovery operations (e.g., sequential file reads)". So I can be silent here.
Let's proceed with the tool calls.
I'll use the format required.
"
===RESEARCH_START===

# Дослідження: Describing Things - Adjectives

## State Standard Reference
§4.2.1.2: "Adjective declension — hard/soft groups, gender agreement"
Alignment: Introduces basic adjective agreement in gender (masculine, feminine, neuter) and number (plural) in the Nominative case, addressing both hard and soft stem groups.

## Vocabulary Frequency
| Word | Notes | Key collocations |
|------|-------|------------------|
| новий (new) | Top 100 high-frequency adjective | новий рік, новий день, нове життя |
| старий (old/ancient) | Essential for historical/physical descriptions | старий будинок, стара книга |
| гарний (beautiful/nice) | High-frequency social descriptor | гарна погода, гарний день, гарна дівчина |
| великий (big/grand) | Essential for indicating scale | велике місто, велика родина, великий привіт |
| синій (blue) | Primary anchor for soft stem (-ій) | синя лінія (Kyiv Metro) |

## Cultural Hooks
1. St. Sophia's Cathedral (Софійський собор) serves as a prominent physical example of "старий" (ancient) and "великий" (grand) architecture in Kyiv.
2. The folklore figure Mavka (Мавка) from Lesya Ukrainka's "Forest Song" provides an engaging context for feminine adjectives like "молода", "гарна", "цікава", and "зелена".

## Common Learner Errors
1. Gender mismatch → *нова машина* (not *новий машина*) — Learners often mistakenly use the dictionary (masculine) form for all nouns regardless of the noun's actual gender.
2. Hard/Soft stem orthography → *синій* (not *синий*) — Phonetic spelling habits often cause English speakers to use the hard '-ий' ending instead of the correct soft '-ій' ending.
3. Plural inconsistency → *гарні дні* (not *гарний дні*) — Learners may default to singular adjectives when describing plural nouns, forgetting that plurals take '-і' across all genders.

## Cross-References
- Builds on: a1-07 (The Gender Code), a1-38 (My Daily Routine)
- Prepares for: a1-12 (Colors and Clothing), a1-42 (Description: Adverbs)

## Notes for Content Writing
- Rely exclusively on verb-free Ukrainian patterns (e.g., "Це нова книга", "гарне місто", "Який це дім?"). Do not use conjugated verbs (є, має), imperatives, or infinitives.
- English must be used for all instructional language ("Remember that...", "Look at...") — no Ukrainian imperative commands like "Запам'ятайте" or "Подивіться".
- The 'Який? Яка? Яке? Які?' question forms are critical for introducing this grammar.

===RESEARCH_END===

===META_OUTLINE_START===
content_outline:
  - title: "Вступ: Світ прикметників (Introduction: The World of Adjectives)"
    slug: introduction-world-of-adjectives
    words: 250
    points:
      - "Scaffolding: Use English to explain the concept of adjective agreement, emphasizing that adjectives must match the noun's gender and number."
      - "Bridge: Briefly review the 'Gender Code' (masculine, feminine, neuter) introduced in module a1-07."
      - "Introduction: Introduce the question words 'Який? Яка? Яке? Які?' using verb-free phrases like 'Який це дім?'."
      - "Cultural Hook: Mention St. Sophia's Cathedral as an example to demonstrate 'старий' and 'великий'."
  - title: "Презентація: Тверда група прикметників (Presentation: Hard Stem Adjectives)"
    slug: hard-stem-adjectives
    words: 350
    points:
      - "Paradigm: Present the Hard Stem endings (-ий, -а, -е, -і) using a clear visual table and color-coded gender markers."
      - "Examples: Provide high-frequency, verb-free examples such as 'новий дім', 'нова книга', 'нове вікно'."
      - "Error Correction: Explicitly warn against using the dictionary form for all nouns, contrasting *новий машина* with the correct 'нова машина'."
      - "Usage: Explain adjective placement by contrasting attributive ('гарна погода') with predicative ('Погода — гарна') positions."
  - title: "Презентація 2: М'яка група та множина (Presentation: Soft Stem and Plurals)"
    slug: soft-stem-and-plurals
    words: 300
    points:
      - "Paradigm: Introduce the Soft Stem endings (-ій, -я, -є, -і) using 'синій' as the primary anchor, referencing the 'синя лінія' of the Kyiv Metro."
      - "Orthography Note: Address the common spelling error of writing '-ий' instead of '-ій' after soft consonants."
      - "Plural Consistency: Emphasize that all plural adjectives take '-і' regardless of gender, supported by verb-free examples like 'нові дні' and 'великі міста'."
  - title: "Практика: Люди і місця (Practice: People and Places)"
    slug: practice-people-and-places
    words: 200
    points:
      - "Cultural Practice: Describe the folklore figure Mavka using feminine adjectives like 'молода', 'гарна', and 'цікава'."
      - "Roleplay Context: Adopt a Real Estate Agent persona to describe a 'нова квартира' or 'великий будинок', reinforcing descriptive vocabulary in a functional setting."
  - title: "Підсумок (Summary & Self-Check)"
    slug: summary-self-check
    words: 100
    points:
      - "Summary: Recap the 'Який?' question-answer pattern and the primary adjective endings."
      - "Self-Check 1: What is the correct form of 'новий' for the masculine noun 'телефон'?"
      - "Self-Check 2: What is the correct form of 'великий' for the feminine noun 'книга'?"
      - "Self-Check 3: What is the correct form of 'синій' for the neuter noun 'море'?"
      - "Self-Check 4: What is the correct plural form of 'гарний' for 'квіти'?"
===META_OUTLINE_END===

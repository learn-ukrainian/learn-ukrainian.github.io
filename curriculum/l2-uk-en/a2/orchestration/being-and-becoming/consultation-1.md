root_cause: |
  1. **Complexity Violation**: The template's example for the `unjumble` activity uses a 3-word sentence (`["книга", "Це", "нова"]`), which directly trains the LLM to generate items that fail the 5-10 word A2 complexity gate.
  2. **Metalanguage Violation**: While the template forbids grammar terminology, it isn't explicit that this rule extends to the translated answer keys in the Summary's self-check questions, leading the LLM to use terms like "Орудний відмінок".
  3. **Low Immersion**: The "Structural Containment" section strictly enforces "Paragraphs = English" and bans Ukrainian from "flowing prose paragraphs", making it mathematically impossible to reach the 45-65% A2 immersion target. It also contains a contradiction, falsely claiming that tables have the "highest immersion density" right after stating that tables are stripped from the immersion calculation.

proposed_changes:
  - find: |
      **unjumble** — sentence word reorder (M11+ ONLY, not M1-M10):
      ```yaml
      - type: unjumble
        title: "Put the Words in Order"
        items:  # minItems: 8
          - words: ["книга", "Це", "нова"]        # array of strings
            answer: "Це нова книга"               # single string
      ```
    replace: |
      **unjumble** — sentence word reorder (M11+ ONLY, not M1-M10):
      ```yaml
      - type: unjumble
        title: "Put the Words in Order"
        items:  # minItems: 8
          - words: ["Студенти", "читають", "нову", "книгу", "разом"]        # array of strings (5-10 words)
            answer: "Студенти читають нову книгу разом"               # single string
      ```
    file: "claude_extensions/phases/gemini/beginner-full-rag.md"
    rationale: "Updates the example to use 5 words, preventing the LLM from mimicking the 3-word pattern which triggers complexity violations."

  - find: |
      Do NOT use Ukrainian grammar terminology (іменник, дієслово, голосний) — students don't know these yet. Do NOT write IPA or Latin transliteration.
    replace: |
      Do NOT use Ukrainian grammar terminology (іменник, дієслово, голосний, відмінок, орудний) — students don't know these yet. This applies to the ENTIRE text, including summaries and self-check questions. Do NOT write IPA or Latin transliteration.
    file: "claude_extensions/phases/gemini/beginner-full-rag.md"
    rationale: "Explicitly adds case terminology to the ban list and ensures the rule applies to the self-check questions at the end of the module."

  - find: |
      1. **Paragraphs = English** with Ukrainian vocabulary **bolded inline**: "The informal command of **читати** (to read) is **читай**." Short phrases and grammatical fragments (e.g., comparing **Я йду** vs **Я іду**) may appear inline.

      2. **Full Ukrainian sentences = structural containers only.** Any Ukrainian sentence (3+ words with a verb) must go in one of these containers — never in flowing prose paragraphs:
         - **Tables** — paradigms, vocabulary groups, gender sorting (highest immersion density)
    replace: |
      1. **Explanatory Paragraphs = English** with Ukrainian vocabulary **bolded inline**: "The informal command of **читати** (to read) is **читай**." Short phrases and grammatical fragments (e.g., comparing **Я йду** vs **Я іду**) may appear inline.

      2. **Full Ukrainian sentences.** To hit higher immersion targets (A2+), you MUST write flowing Ukrainian narrative paragraphs and reading passages. For basic structural display, use containers:
         - **Tables** — paradigms, vocabulary groups (WARNING: tables contribute ZERO to your immersion score)
    file: "claude_extensions/phases/gemini/beginner-full-rag.md"
    rationale: "Removes the strict ban on Ukrainian prose and the contradictory claim about tables having high density, allowing the LLM to write enough natural text to meet A2 immersion targets."

scope: all_modules
action: rebuild
confidence: high

additional_notes: |
  The contradiction regarding tables (saying they are stripped but then claiming they have the highest immersion density) severely crippled the LLM's ability to hit immersion targets, as it likely prioritized tables thinking they helped. Fixing this will vastly improve A2 module naturalness and immersion scores.
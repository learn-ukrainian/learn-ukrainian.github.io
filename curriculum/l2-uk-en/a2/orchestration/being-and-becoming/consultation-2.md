root_cause: |
  1. The template's example for `unjumble` activities uses a 3-word sentence ("Це нова книга"), which directly trains the LLM to violate the 5-10 word complexity requirement for A2.
  2. The prohibition against Ukrainian grammar terminology was not comprehensive enough (omitting terms like "відмінок", "орудний") and failed to explicitly restrict usage in the summary self-check questions, leading to terminology leaks.
  3. The structural instructions for each section simply tell the LLM to "Explain... Show... Reinforce." To hit the large 2000-word target while adhering to "Paragraphs = English," the LLM pads the text with massive English essays. This naturally tanks the immersion ratio to 16.3%. The template needs an explicit instruction to scale up the Ukrainian examples instead of English padding.

proposed_changes:
  - find: |
        - words: ["книга", "Це", "нова"]        # array of strings
          answer: "Це нова книга"               # single string
    replace: |
        - words: ["Ця", "нова", "книга", "дуже", "цікава"] # array of strings, 5-10 words
          answer: "Ця нова книга дуже цікава"   # single string
    file: "claude_extensions/phases/gemini/beginner-full-rag.md"
    rationale: "Aligns the template example with the A2 complexity requirement of 5-10 words per sentence, preventing the LLM from mimicking short sentence generation."

  - find: |
      Do NOT use Ukrainian grammar terminology (іменник, дієслово, голосний) — students don't know these yet. Do NOT write IPA or Latin transliteration.
    replace: |
      Do NOT use Ukrainian grammar terminology (іменник, дієслово, голосний, відмінок, орудний тощо) anywhere in the content, activities, or summary questions — students don't know these yet. Use English for grammar terms. Do NOT write IPA or Latin transliteration.
    file: "claude_extensions/phases/gemini/beginner-full-rag.md"
    rationale: "Broadens the metalanguage restriction to include grammatical cases and explicitly applies it to summary questions, preventing terminology leaks like 'орудний'."

  - find: |
      Follow the structural containment rules above. In each section:
      1. **Explain** the concept in an English paragraph (with Ukrainian vocabulary bolded inline)
      2. **Show** the pattern in a Ukrainian structural container (table, example list, dialogue, or pattern box)
      3. **Reinforce** with a callout box (tip, warning, culture note, or fun fact)
    replace: |
      Follow the structural containment rules above. In each section:
      1. **Explain** the concept in an English paragraph (with Ukrainian vocabulary bolded inline)
      2. **Show** the pattern in EXTENSIVE Ukrainian structural containers (long example lists, multiple dialogues, or pattern boxes). To hit word count targets and maintain high immersion, generate many varied Ukrainian examples rather than writing long English essays.
      3. **Reinforce** with a callout box (tip, warning, culture note, or fun fact)
    file: "claude_extensions/phases/gemini/beginner-full-rag.md"
    rationale: "Instructs the LLM to reach high word counts by generating extensive Ukrainian examples rather than padding with English grammar theory, structurally fixing the low immersion ratio."

scope: all_modules
action: rebuild
confidence: high

additional_notes: |
  The immersion issue at A2.1 is systemic because the module target (2000 words) combined with the 'Keep paragraphs short' and strict 'Paragraphs = English' rules naturally funnels the LLM into writing 80% English. The proposed fix directly combats this by explicitly instructing the LLM to use extensive Ukrainian examples as the primary means to hit the word count. The unjumble and metalanguage fixes are direct corrections to misleading examples and incomplete constraints in the base template.
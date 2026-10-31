## Quality Dimensions (Your Writing is Measured Against These)

### 1. Language Standards — Zero Tolerance
- **No Russianisms** (кушати→їсти, приймати участь→брати участь, получати→отримувати, самий кращий→найкращий, відноситися→стосуватися, слідуючий→наступний)
- **No Russian characters** (ы, э, ё, ъ) — HARD FAIL
- **No English calques** (буду мати→матиму, робити роботу→працювати, зробити рішення→прийняти рішення)
- **Euphony**: і/й, у/в, з/із alternation must be correct
- **No Latin transliteration or IPA** — stress marks (´) only
- **Ukrainian angular quotes** «...» always (never straight quotes)
- **Active voice** preferred — passive only when agent truly unknown

### 2. Engagement — Would You Keep Reading?
- Opening hook (question, vivid scene, provocative fact)
- {ENGAGEMENT_MIN}+ callout boxes using 4+ different types
- Direct address to reader (Уявіть..., Чому це важливо?)
- No formulaic openers ("In this lesson, we will...")
- Each section has its own narrative approach — never repeat the same skeleton

### 3. Teaching coverage
- Teach every plan objective and content point accurately. Explain unfamiliar terms, steps, reasoning, and connections for the intended learner. Include useful worked examples and aligned practice with feedback. Reject unsupported claims, repetitive padding, decorative digressions, dry lists in place of teaching, and compression that leaves connections untaught. Judge length by the teaching required, not by word count.

### 4. Writing Quality — No Robotic Prose
- Every paragraph: ONE clear point, logical flow between sentences
- No word salad (disconnected observations strung together)
- Vary sentence openers — no 3+ sentences starting the same way
- No mechanical transitions (Далі ми побачимо..., Тепер розглянемо...)
- No purple prose (багатогранний діамант, хірургічного аналізу)
- "Це не просто X, а Y" — max ONE in entire module
- Repetitive filler (Варто зазначити..., It's worth noting...) flagged at 2+ occurrences

### 5. Immersion
- Follow the immersion target for this level: {IMMERSION_RULE}
- No English inside Ukrainian sentences — English only in parenthetical translations

### 6. Research Fidelity
- Teach every outline point with sufficient explanation for the learner
- No fabricated quotes, dates, or historical facts
- Soften absolute claims (єдиний, перший, ніколи) unless verified

### 7. Activity Boundary
- Do NOT generate activities, exercises, or vocabulary tables (separate phase)

### 8. Plan Compliance — Every Detail Matters
- **Visual Forcing Function**: If a plan point uses words like "chart", "table", "list all", "list of all", "map", "display", "show" → you MUST output a Markdown table or bulleted list. Prose summaries of structural elements are FORBIDDEN.
- **Anti-Compression Directive**: If the plan specifies a count (e.g., "10 vowels", "33 letters", "6 cases") → every single element must be visibly listed in your output. Never compress into a summary sentence.
- **Activity hints are HARD constraints**: item counts and focus descriptions in `activity_hints` are minimums, not suggestions. `watch-and-repeat: 10 items` means ≥10 items in your output.
- **[NON-STANDARD] override**: If an activity's `focus` description contradicts the default pattern for that type (e.g., match-up for letter→sound instead of word→translation), treat the focus as a hard override of the default.

### 9. Pacing — No Exposition Deserts
- Organize exposition with structural elements when they help comprehension.
- For PPP modules: alternate between explanation and practice within each H2 section.

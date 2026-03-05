**Phase**: Beginner Content
**Step**: Resolving guideline conflicts
**Friction Type**: DOC_CONFLICT
**Raw Error**: None
**Self-Correction**: `claude_extensions/quick-ref/A1.md` stated that M01-M10 require full Latin transliteration (e.g., слово (slovo)). However, the explicit system prompt for this turn contained a strict ALL-CAPS ban on Latin transliteration ("Latin transliterations are BANNED at ALL levels"). Following the hierarchical context rules, I prioritized the explicit prompt instructions and omitted all Latin transliteration, providing only English translations in parentheses.
**Proposed Tooling Fix**: Update `claude_extensions/quick-ref/A1.md` to remove the outdated transliteration rule for M01-M10 so it aligns with the global ban on Latin transliteration.
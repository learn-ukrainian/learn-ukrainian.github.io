# Bug Autopsy: Gemini Vision-LLM OCR Hallucinations

**Date:** 2026-05-21
**Issue:** #2177 (Follow-up to killed #2001 OCR handoff)

## What broke
During the now-abandoned Gemini-2.5 re-OCR project for the ESUM dictionary, the vision-LLM (Gemini-2.5-flash) exhibited severe hallucination patterns on dense print pages. The model consistently emitted etymologically-plausible content for a DIFFERENT page than the one present in the input image. This resulted in an estimated ~97% wrong-page rate.

We quarantined 17 distinct hallucination samples, which break down into three failure modes:
1. **Large repetition-loops** (10 samples): The model loops over a paragraph or multi-line block indefinitely.
2. **Single-line repetition-loops** (6 samples): The model repeats a single line or short substring (e.g., `**пра́во** ... полаб. *provü*, схв. *пра̏во* ...`) over and over.
3. **Semantic hallucination** (1 sample): The model confidently invents fake cognates (e.g., inventing `дінд. *smárati* «пам’ятає»` and `гр. κίνδυνος` for the word `сму́шок`), which requires RAG fact-checking against the actual ESUM text to detect.

## Why
Vision-LLMs operating on dense print at scale tend to conflate "what this kind of page typically looks like" with "what THIS specific page says." When faced with dense, highly structured lexicographic text (abbreviations, italicized proto-forms, multiple languages), the model's language priors override its visual grounding, causing it to hallucinate plausible-looking dictionary entries instead of transcribing the image.

The cross-validation bake-off report confirms this: traditional OCR (Tesseract) scored a 0.92 semantic accuracy, while Gemini scored 0.03.

## Detection gaps
The original `is_low_quality_output` check (the "shadow uniqueness" check) successfully caught the 10 large repetition loops, but it had a guard clause (`if len(lines) < 10`) that caused it to skip short files. This allowed the single-line repetition loops to slip through. Furthermore, semantic hallucinations are fundamentally undetectable by static substring/repetition checks and require an active RAG fact-check against a trusted baseline.

## Prevention
1. **Always verify existing digital layers:** Before launching an expensive and slow vision-LLM OCR pipeline, check if the source host already provides a clean text layer (the Internet Archive already had clean text layers for ESUM — issue #2001 was solving a problem that was already solved).
2. **Implement semantic-diff gating:** For any future visual-OCR experiment, always ship a semantic-diff gate against a baseline traditional OCR (like Tesseract). If the vision-LLM output diverges massively from the traditional OCR baseline without a verifiable reason, it is likely hallucinating.
3. **Robust Repetition Checks:** The hallucination detector now includes both the legacy shadow uniqueness check (for large loops) and a new substring-repetition check (`window=15`, `threshold=4`) to catch short, single-line loops.

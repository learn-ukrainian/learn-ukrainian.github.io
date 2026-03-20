# Writer Comparison: Gemini's Blind Review of Claude's Output

**Date:** 2026-03-20
**Reviewer:** gemini-3.1-pro-preview (blind — did not know which model wrote it)

## Scores

| Dimension | Score | Key Issue |
|-----------|-------|-----------|
| Linguistic accuracy | 3/10 | кон (Russicism), метро needs Р, В→[ў] at word end |
| Pedagogical quality | 7/10 | Good progression, but 14 videos clutter the page |
| Natural voice | 8/10 | Warm, encouraging tone |
| Research usage | 3/10 | "unknown" citations are meaningless placeholders |
| Exercise placeholders | 5/10 | Items count mismatch, but well-placed |
| Ukrainian-first thinking | 8/10 | Good use of звуки/літери categories |

**Overall: ~5.7/10**

## Specific errors found
1. **кон** — Russian word, should be removed (was in stale prompt — plan already fixed)
2. **метро** listed as readable with only А,О,К,М,Т,Е — needs Р
3. **В at end of Київ** — vocalizes to [ў], not [в]
4. **"unknown" citations** — knowledge packet source field issue, not Claude's fault
5. **Exercise items: 6 but vocabulary has 5 letters** — math error

## Notes
- Error #1 (кон) was from stale prompt content — plan was already fixed but build used cached version
- Error #4 (unknown citations) is a pipeline issue — RAG returns "unknown" as source name
- Errors #2, #3, #5 are genuine Claude errors the review correctly caught

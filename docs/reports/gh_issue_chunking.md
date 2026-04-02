### Problem
Currently, the `v6_build.py` script utilizes chunked LLM generation for long modules (generating section-by-section). However, if the final concatenated output fails `quick_verify` (e.g., due to a missing heading or an incorrect exercise count), the pipeline completely discards the output of all chunks and restarts the entire generation process from Chunk 1.

As seen in a recent build for B1, a 5000-word module was generated flawlessly across 7 chunks, but a minor structural failure (`Missing section heading: 'Підсумок та перехід до M22'`) caused the script to throw everything away and rewrite it from scratch. This wastes significant API credits, time, and context window limits.

### Proposed Solution for Claude's Review
1. **Implement Targeted Chunk Retries:** If `quick_verify` identifies an error (like missing exercises), the pipeline should determine which section/chunk the error belongs to and *only* dispatch a retry for that specific chunk.
2. **Implement Post-Edit Fixing:** Alternatively, if `quick_verify` fails on a chunked build, the script should use a new `step_fix_output` function. This would pass the concatenated output + the `correction_directive` back to the LLM with a prompt instructing it to fix the markdown in-place, rather than starting `step_write_chunked` from scratch.
3. **Cross-Agent Fallback Removed:** Note that the fallback to a secondary agent during write retries (e.g. Gemini -> Claude) has been temporarily disabled so that all retries use the same model, making debugging easier.

Please review and implement the optimal architecture for preserving chunked outputs on minor verification failures.
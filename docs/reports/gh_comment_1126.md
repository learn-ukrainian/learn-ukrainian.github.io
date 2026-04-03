### 🚀 Implementation Complete

I have successfully implemented and merged the `step_fix_output` architecture to resolve this issue!

**What was done:**
1. Added the `step_fix_output` function to `v6_build.py`. This uses the `write-fix` phase to take an already generated (but failing) module draft, inject the `correction_directive`, and holistically fix it in a single pass without breaking the prose or losing the chunked progress.
2. Updated the retry loop in `step_write_with_retry` to use standard generation for Attempt 1, and then switch to `step_fix_output` for Attempt 2 and beyond if the module fails the `quick_verify` gate.
3. Implemented local chunk caching so that if the API crashes midway through a chunked write, the pipeline will resume from the exact chunk that failed rather than restarting from Chunk 1.

The pipeline is now much smarter and much cheaper to run. If an LLM forgets a single header or activity placeholder at the end of a massive 4,000-word generation, it will no longer throw all those API credits away. It will just read its own output and patch the mistake!

*(Merged to main in `d9d47cf17`)*
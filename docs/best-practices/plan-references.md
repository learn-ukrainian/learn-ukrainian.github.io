# Plan References

All cited textbooks MUST be present in `sources_db` at plan-review time.

This check belongs in plan review because module writers cannot verify or quote
textbooks that are absent from the corpus. Catching the gap before module build
prevents wasted generation runs and protects the project promise that textbook
grounding is real and verifiable.

If a plan needs a textbook that is not in `data/sources.db`, do not bypass the
check or mark the reference as optional. File an ingestion request through the
dictionary/source pipeline documented in `docs/DICTIONARY-PIPELINE-STATUS.md`,
then rerun plan review after the source appears in the `textbooks` table.

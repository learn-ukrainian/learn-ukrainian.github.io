The critical audit failure was **not a content problem** — it was a missing meta YAML sidecar file. The audit system looks for `curriculum/l2-uk-en/a1/meta/stress-and-intonation.yaml` to load frontmatter, and this file didn't exist (unlike all other A1 modules which have their meta files).

I created the sidecar with all required metadata fields (`duration`, `transliteration`, `tags`, `objectives`, `grammar`, `pedagogy`) populated from the plan file, matching the format of sibling modules like `consonant-sounds.yaml` and `syllables-and-word-division.yaml`.

The VESUM misses (`да`, `ка`, `шко`) are fragments from stress examples (вода́ → -да́, рука́ → -ка́, школа → шко́-) — these are not real words, just syllable fragments in the content, so they're expected non-matches.

===REVIEW_START===
## Fix Applied

**Root cause:** Missing meta YAML sidecar file at `curriculum/l2-uk-en/a1/meta/stress-and-intonation.yaml`. The audit system requires either embedded YAML frontmatter or a sidecar meta file. All other A1 modules have sidecar files; this one was missing.

**Fix:** Created `curriculum/l2-uk-en/a1/meta/stress-and-intonation.yaml` with all required metadata fields (`duration`, `transliteration`, `tags`, `objectives`, `grammar`, `pedagogy`) sourced from the plan file, matching sibling module format.

**No content changes needed.** The `.md` file content is correct. The VESUM misses (`да`, `ка`, `шко`) are syllable fragments from stress notation, not actual word errors.
===REVIEW_END===
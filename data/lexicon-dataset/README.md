# Word Atlas Lexicon Dataset

This directory contains the open, sharded dataset of the Word Atlas lexicon.

## Structure

The data is provided in JSONL (JSON Lines) format, sharded by the first letter of the Ukrainian headword (`lemma`), located in the `dataset/` directory.

- `dataset/А.jsonl`, `dataset/Б.jsonl`, etc.
- Each line in the `.jsonl` files is a standalone JSON object representing a single lemma.

## Schema

Each entry represents a single word (lemma) and contains:
- `lemma` (string): The Ukrainian headword.
- `url_slug` (string): Slug used for routing.
- `gloss` (string): English translation/gloss.
- `pos` (string): Part of speech.
- `ipa` (string): International Phonetic Alphabet representation.
- `course_usage` (array): List of course modules where this word is taught.
- Plus any available enriched fields (`etymology`, `definitions`, `paradigm`, `heritage_status`, etc.).

Provenance is tracked per-field where applicable. For full attribution details, see [ATTRIBUTION.md](./ATTRIBUTION.md) and [NOTICE.md](./NOTICE.md).

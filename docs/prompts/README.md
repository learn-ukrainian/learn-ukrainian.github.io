# Prompt Templates

Reusable prompts for curriculum work live here. Keep one-off dispatch prompts in
`.agent/prompts/`; keep pipeline phase templates in `scripts/build/phases/`.

Track templates should be maintained as stable production prompts, not as
single-run transcripts. When a module build exposes a recurring failure mode,
update the relevant track template so the next run inherits the fix.

## Available Templates

- [B1 sequential batch build](b1-sequential-batch-build-template.md) - production
  prompt for building a small B1 batch while preserving module-tailored quality.

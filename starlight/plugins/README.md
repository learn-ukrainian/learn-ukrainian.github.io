# Starlight Plugins

## `vocab-etymology-link.mjs`

Build-time remark plugin that links Starlight vocabulary tables to checked-in
ESUM etymology pages.

The plugin only edits tables inside `<TabItem label="Vocabulary">` or
`<TabItem label="Словник">`. The first header cell must be `Word` or `Слово`.
For each data row, the first cell is linked when the word is a single token and
resolves to an existing `starlight/src/data/etymology-manifest.json` slug.
Multi-word phrases are left unchanged.

Resolution order:

1. Direct normalized manifest lemma match.
2. `starlight/src/data/vesum-vocab-lemmas.json` form→lemma fallback.
3. No link.

Regenerate the VESUM subset after adding lesson vocabulary:

```bash
.venv/bin/python scripts/etymology/build_vesum_vocab_lemmas.py
```

Opt out for an entire tab:

```mdx
<TabItem label="Vocabulary" data-etymology-links="false">
```

Opt out for one table with an adjacent MDX comment:

```mdx
{/* vocab-etymology: off */}
| Word | IPA | English |
| --- | --- | --- |
| кава |  | coffee |
```

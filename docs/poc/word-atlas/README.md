# Word Atlas POC Route Map

The legacy Word Atlas POC has been split into one design source per HTML file.
Each file is the single source for the route or route variant listed here.

| HTML file | Route | Preserved source view |
| --- | --- | --- |
| `landing.html` | `/lexicon/` | Original default `князь` Word Atlas surface |
| `detail.html` | `/lexicon/{lemma}` | `прапор` lemma detail with Soviet-definition warning |
| `heritage-defense.html` | `/lexicon/файний` | `файний` heritage-defense detail variant |

All three files share `word-atlas.css`, which contains the light/dark `--lu-*`
tokenized styles extracted from the original POC. The legacy top-level POC path
is kept as a short compatibility stub for existing links.

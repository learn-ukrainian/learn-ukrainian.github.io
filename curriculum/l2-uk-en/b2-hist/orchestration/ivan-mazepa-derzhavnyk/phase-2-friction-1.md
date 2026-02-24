**Phase**: Phase 2: Content
**Step**: Structuring the H2 sections based on `content_outline`.
**Friction Type**: YAML_SCHEMA_VIOLATION (Potential)
**Raw Error**: None (Preventative Action)
**Self-Correction**: The `meta.yaml` file contained duplicate phrases in the `content_outline` for sections 3 and 4 ("Гетьман-будівничий (1687-1708)"). To comply with the strict downstream audit rule "no two H2s sharing the same keyword", I renamed the markdown H2s to "Державотворення: Суспільство та Економіка" and "Культурне відродження та Дипломатія" ensuring full keyword uniqueness while preserving semantic intent.
**Proposed Tooling Fix**: Update the `content_outline` in the `meta.yaml` generation script to enforce unique keywords in section names to prevent conflicts between the outline structure and the Markdown validation audit gates.
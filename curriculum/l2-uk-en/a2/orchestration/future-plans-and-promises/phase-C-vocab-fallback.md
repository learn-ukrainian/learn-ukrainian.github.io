You are a TEXT GENERATOR. Generate ONLY vocabulary YAML for a Ukrainian language module.

Read the lesson content:
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/future-plans-and-promises.md
```


**Plan file** (vocabulary_hints — follow this list):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a2/future-plans-and-promises.yaml
```

**Meta file** (vocab count target):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/meta/future-plans-and-promises.yaml
```

## Task

Generate vocabulary YAML for the key terms taught in this lesson. Follow vocabulary_hints from the plan file if available.

## Format

Each entry uses: `lemma` (Ukrainian), `translation` (English), `pos` (part of speech).
Optional: `gender` (m/f/n for nouns), `aspect` (perfective/imperfective for verbs), `notes`, `usage`, `example`.

Do NOT include `ipa` fields.

## Output

You MUST output BOTH the opening AND closing delimiters. The closing delimiter is MANDATORY.

===VOCABULARY_START===

items:
  - lemma: "слово"
    translation: "word"
    pos: "noun"
    gender: "n"

===VOCABULARY_END===

CRITICAL: You MUST end your output with the line ===VOCABULARY_END=== — the pipeline CANNOT extract your work without it.
Output NOTHING else. No commentary, no explanation. Just the delimited vocabulary YAML.

# Wiki Coverage Baseline: a1/my-morning

Command:

```bash
/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python scripts/audit/measure_wiki_coverage.py wiki/pedagogy/a1/my-morning.md curriculum/l2-uk-en/a1/my-morning/module.md
```

Summary:

| Obligation type | Covered | Total |
| --- | ---: | ---: |
| L2 errors | 0 | 6 |
| Sequence steps | 1 | 5 |
| Phonetic rules | 0 | 3 |

Raw output excerpt:

```json
{
  "wiki_path": "wiki/pedagogy/a1/my-morning.md",
  "module_path": "curriculum/l2-uk-en/a1/my-morning/module.md",
  "l2_errors": {
    "covered": 0,
    "total": 6,
    "coverage": "0/6"
  },
  "sequence_steps": {
    "covered": 1,
    "total": 5,
    "coverage": "1/5"
  },
  "phonetic_rules": {
    "covered": 0,
    "total": 3,
    "coverage": "0/3"
  }
}
```

Interpretation: the current module confirms the empirical failure mode. It
does not implement any wiki-named L2 contrast pair and does not give the
learner-facing IPA-style pronunciation rules extracted from the wiki page.


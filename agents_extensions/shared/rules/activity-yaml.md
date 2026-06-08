---
paths:
  - "curriculum/**/*.yaml"
  - "curriculum/**/*.yml"
  - "scripts/yaml_activities.py"
  - "scripts/generate_mdx/**"
---

# Activity YAML Rules

<critical>

Bare list at root (NOT `activities:` wrapper). Full schema: [`vocabulary-activity-standards.md`](docs/best-practices/vocabulary-activity-standards.md) and `docs/ACTIVITY-YAML-REFERENCE.md`

```yaml
# CORRECT                    # WRONG
- type: quiz                 activities:
  title: ...                   - type: quiz
```

</critical>

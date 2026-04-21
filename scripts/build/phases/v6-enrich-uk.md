---
suite: uk
lesson_tab_label: Урок
vocab_tab_label: Словник
workbook_tab_label: Зошит
resources_tab_label: Ресурси
slovnyk_mode: definition
allow_plan_fallback: false
flashcards: true
---

# V6 Enrich Profile — Ukrainian Canonical

Цей профіль керує пост-write збагаченням, яке після `#1124` виконується
в `PUBLISH`, а не окремим LLM-кроком.

## Правила

- Вкладки лишаються повністю українськими.
- Словник показує **українські тлумачення**, а не англійські переклади.
- Якщо writer не згенерував словник із тлумаченнями, таб `Словник` краще
  пропустити, ніж підставляти англомовний fallback із plan YAML.
- Жодних bilingual tab headers.

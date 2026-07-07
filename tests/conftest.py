"""
Pytest configuration and shared fixtures for audit tests.

Provides reusable content snippets and module templates for testing.
"""

import os
import sys

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(autouse=True)
def _isolate_llm_qg_runtime_stores(tmp_path, monkeypatch):
    """Every test writes llm_qg runtime state (DB + circuit sidecar) to tmp_path.

    Root cause (2026-07-07): llm_qg_store resolves its stores via env-var-or-
    PROJECT_ROOT-default; tests exercising qg_workflow/store paths without
    overriding the env minted data/telemetry/llm_qg_live_circuit.json in every
    checkout/worktree they ran in — one such stray got swept into PR #4743 by
    git add -A. Hermetic by default; tests that need a specific path still
    monkeypatch their own.
    """
    monkeypatch.setenv("LEARN_UKRAINIAN_LLM_QG_DB", str(tmp_path / "llm_qg.db"))
    monkeypatch.setenv("LEARN_UKRAINIAN_LLM_QG_CIRCUIT", str(tmp_path / "llm_qg_live_circuit.json"))


# =============================================================================
# MODULE TEMPLATES
# =============================================================================

@pytest.fixture
def minimal_module_b1():
    """Minimal valid B1 module structure."""
    return """---
module: 1
title: Test Module
level: B1
pedagogy: PPP
cefr: B1.1
phase: Grammar
objectives:
  - Test objective
---

# Presentation

This is the presentation section with content.

# Practice

Practice content here.

# Production

Production content here.

# Vocabulary

| Слово | Переклад | Примітки |
|-------|----------|----------|
| слово | word | noun |
"""


@pytest.fixture
def minimal_module_a1():
    """Minimal valid A1 module structure."""
    return """---
module: 1
title: Test Module
level: A1
pedagogy: PPP
cefr: A1.1
phase: Basics
objectives:
  - Test objective
---

# Presentation

This is the presentation section with content.

# Practice

Practice content here.

# Production

Production content here.

# Vocabulary

| Word | IPA | English | POS | Gender | Note |
|------|-----|---------|-----|--------|------|
| слово | /ˈslɔwɔ/ | word | noun | n | - |
"""


# =============================================================================
# ACTIVITY SNIPPETS
# =============================================================================

@pytest.fixture
def valid_quiz_b1():
    """Valid B1 quiz with proper word counts."""
    return """
## quiz: Частини мови

1. Яка частина мови в українській граматиці називає предмети та поняття для опису світу?
   - [x] Іменник
   - [ ] Дієслово
   - [ ] Прикметник
   - [ ] Прислівник

2. Яка частина мови в українській мові позначає дію або стан суб'єкта речення?
   - [ ] Іменник
   - [x] Дієслово
   - [ ] Прикметник
   - [ ] Прислівник
"""


@pytest.fixture
def valid_error_correction():
    """Valid error-correction with all required callouts."""
    return """
## error-correction: Виправлення

1. Він ходить до школа.
   > [!error] школа
   > [!answer] школи
   > [!options] школа | школи | школу | школою
   > [!explanation] Після прийменника "до" вживаємо родовий відмінок.

2. Вона читає книгу на стіл.
   > [!error] стіл
   > [!answer] столі
   > [!options] стіл | столі | столу | столом
   > [!explanation] Після прийменника "на" (місце) вживаємо місцевий відмінок.
"""


@pytest.fixture
def valid_unjumble():
    """Valid unjumble with answer callout."""
    return """
## unjumble: Речення

1. я / люблю / Україну / дуже / сильно
   > [!answer] Я дуже сильно люблю Україну.

2. вона / читає / книгу / цікаву / про / історію
   > [!answer] Вона читає цікаву книгу про історію.
"""


@pytest.fixture
def valid_match_up():
    """Valid match-up with proper pairs."""
    return """
## match-up: Терміни

| Термін | Переклад |
|--------|----------|
| слово | word |
| речення | sentence |
| граматика | grammar |
| відмінок | case |
| дієслово | verb |
| іменник | noun |
| прикметник | adjective |
| прислівник | adverb |
| займенник | pronoun |
| сполучник | conjunction |
"""


# =============================================================================
# VOCABULARY FIXTURES
# =============================================================================

@pytest.fixture
def valid_vocab_table_b1():
    """Valid B1 vocabulary table (3 columns)."""
    return """
# Словник

| Слово | Переклад | Примітки |
|-------|----------|----------|
| граматика | grammar | noun |
| відмінок | case | noun |
| дієслово | verb | noun |
| іменник | noun | noun |
"""


@pytest.fixture
def valid_vocab_table_a1():
    """Valid A1 vocabulary table (6 columns with IPA)."""
    return """
# Vocabulary

| Word | IPA | English | POS | Gender | Note |
|------|-----|---------|-----|--------|------|
| слово | /ˈslɔwɔ/ | word | noun | n | - |
| книга | /ˈknɪɦa/ | book | noun | f | - |
| читати | /tʃɪˈtatɪ/ | to read | verb | - | impf |
"""


@pytest.fixture
def invalid_vocab_missing_ipa():
    """Invalid A1 vocabulary - missing IPA."""
    return """
# Vocabulary

| Word | IPA | English | POS | Gender | Note |
|------|-----|---------|-----|--------|------|
| слово | | word | noun | n | - |
| книга | /ˈknɪɦa/ | book | noun | f | - |
"""


# =============================================================================
# CONTENT WITH ISSUES
# =============================================================================

@pytest.fixture
def content_with_russian_chars():
    """Content with Russian-only characters."""
    return """---
module: 1
title: Test
level: B1
---

# Test

Прикметник "красивый" не є українським.
"""


@pytest.fixture
def content_clean_ukrainian():
    """Clean Ukrainian content without Russian chars."""
    return """---
module: 1
title: Test
level: B1
---

# Test

Прикметник "красивий" є українським словом.
Граматика української мови цікава.
"""


@pytest.fixture
def quiz_with_short_prompts():
    """Quiz with prompts that are too short for B1."""
    return """
## quiz: Тест

1. Яка це частина мови?
   - [x] Іменник
   - [ ] Дієслово

2. Що це таке?
   - [x] Граматика
   - [ ] Лексика
"""


# =============================================================================
# PPP STRUCTURE FIXTURES
# =============================================================================

@pytest.fixture
def valid_ppp_structure():
    """Content with valid PPP structure."""
    return """---
module: 1
title: Test
level: B1
pedagogy: PPP
---

# Presentation

Content here.

# Practice

Practice content.

# Production

Production content.
"""


@pytest.fixture
def invalid_ppp_missing_section():
    """PPP content missing Production section."""
    return """---
module: 1
title: Test
level: B1
pedagogy: PPP
---

# Presentation

Content here.

# Practice

Practice content.
"""

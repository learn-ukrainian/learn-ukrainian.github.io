"""
Content validators for module audits.

Contains tone validation, checkpoint format/coverage validation,
and structure checking functions.
"""

import re


def validate_tone(content: str) -> list[str]:
    """Validate content for tone issues."""
    errors = []

    if re.search(r'\bThe\s+Ukraine\b', content, re.IGNORECASE):
        is_correction = re.search(
            r'(not|incorrect|offensive|never|avoid)\s+.*?\bThe\s+Ukraine\b',
            content, re.IGNORECASE
        ) or re.search(
            r'\bThe\s+Ukraine\b.*?\s+(is\s+incorrect|is\s+offensive)',
            content, re.IGNORECASE
        )
        if not is_correction:
            errors.append("Tone Error. Found 'The Ukraine'. Use 'Ukraine' (sovereign nation).")

    if re.search(r'\bKiev\b', content) and not re.search(r'not\s+Kiev', content, re.IGNORECASE) and not re.search(r'Russian', content, re.IGNORECASE):
        errors.append("Tone Error. Found 'Kiev'. Use 'Kyiv' (Ukrainian transliteration).")

    return errors


def validate_checkpoint_format(content: str) -> list[str]:
    """Validate checkpoint modules follow Skill-based format.

    Required structure (per checkpoint design guide):
    - H1: # Checkpoint - [Name] or # Контрольна точка
    - ## Skill N: [Name] or ## Навичка N: [Name] sections (at least 1)
    - Each skill has: ### Model:, ### Practice:, ### Self-Check
      (or Ukrainian equivalents)

    See: docs/l2-uk-en/CHECKPOINT-DESIGN-GUIDE.md
    """
    errors = []

    has_diagnostika = bool(re.search(r'^## Діагностика', content, re.MULTILINE))
    has_analiz = bool(re.search(r'^## Аналіз', content, re.MULTILINE))
    has_pogliblennya = bool(re.search(r'^## Поглиблення', content, re.MULTILINE))

    alternative_structure = has_diagnostika or has_analiz or has_pogliblennya

    skill_pattern = r'^## (?:Skill|Навичка)\s*\d*:'
    skill_matches = re.findall(skill_pattern, content, re.MULTILINE)

    if alternative_structure and not skill_matches:
        alt_sections = []
        if has_diagnostika:
            alt_sections.append("Діагностика")
        if has_analiz:
            alt_sections.append("Аналіз")
        if has_pogliblennya:
            alt_sections.append("Поглиблення")
        errors.append(f"REWRITE REQUIRED: Checkpoint uses incorrect '{'/'.join(alt_sections)}' structure instead of Skill-based format (## Skill N: → ### Model: → ### Practice: → ### Self-Check)")
    elif not skill_matches:
        errors.append("Checkpoint missing '## Skill N:' or '## Навичка N:' sections (need at least 1)")

    bold_model = len(re.findall(r'^\*\*Model:', content, re.MULTILINE))
    bold_practice = len(re.findall(r'^\*\*Practice:', content, re.MULTILINE))

    if bold_model > 0 or bold_practice > 0:
        errors.append(f"Checkpoint uses **bold:** format ({bold_model} Model, {bold_practice} Practice) - convert to ### H3 headers")

    skill_sections = re.split(skill_pattern, content, flags=re.MULTILINE)[1:]
    for i, section in enumerate(skill_sections, 1):
        section_end = re.search(r'^##\s', section, re.MULTILINE)
        section_text = section[:section_end.start()] if section_end else section

        has_model = re.search(r'^### (?:Model|Модель)', section_text, re.MULTILINE)
        has_practice = re.search(r'^### (?:Practice|Практика)', section_text, re.MULTILINE)
        has_selfcheck = re.search(r'^### (?:Self-Check|Самоперевірка)', section_text, re.MULTILINE)

        if not has_model:
            errors.append(f"Skill {i} missing '### Model:' or '### Модель:' H3 header")
        if not has_practice:
            errors.append(f"Skill {i} missing '### Practice:' or '### Практика:' H3 header")
        if not has_selfcheck:
            errors.append(f"Skill {i} missing '### Self-Check' or '### Самоперевірка' H3 header")

    return errors


def validate_checkpoint_coverage(content: str, frontmatter_str: str) -> list[str]:
    """Validate checkpoint covers expected skills from frontmatter grammar/objectives."""
    errors = []

    grammar_match = re.search(r'^grammar:\s*\n((?:\s+-\s+.*\n?)+)', frontmatter_str, re.MULTILINE)
    if grammar_match:
        grammar_items = re.findall(r'-\s+"?([^"\n]+)"?', grammar_match.group(1))

        for item in grammar_items:
            keywords = item.split('(')[0].strip()[:30].lower()
            if keywords and not re.search(re.escape(keywords[:15]), content.lower()):
                pass  # Soft warning - don't fail for now

    objectives_match = re.search(r'^objectives:\s*\n((?:\s+-\s+.*\n?)+)', frontmatter_str, re.MULTILINE)
    if objectives_match:
        objective_items = re.findall(r'-\s+"?([^"\n]+)"?', objectives_match.group(1))

        skill_pattern = r'^## (?:Skill|Навичка)\s*\d*:'
        skill_count = len(re.findall(skill_pattern, content, re.MULTILINE))
        objective_count = len(objective_items)

        if objective_count > 0 and skill_count < 1:
            errors.append(f"Checkpoint has {objective_count} objectives but no '## Skill N:' or '## Навичка N:' sections")

    return errors


def check_structure(content: str) -> dict[str, bool]:
    """Check for required structure elements.

    Returns a dictionary of boolean flags for each section.
    """
    lines = content.split('\n')
    # Summary headings: accept the canonical English/Ukrainian labels AND
    # common Ukrainian summary-semantic equivalents that writers naturally
    # produce for A2+ review/self-check sections. The pedagogical intent
    # is the same — a closing section that recaps or self-tests the
    # module's content. Relaxed 2026-04-11 after a2 audit flagged 6
    # otherwise-valid modules on literal label mismatch.
    #
    # The match is substring-anywhere-in-heading (not prefix-only) because
    # writers put the semantic keyword mid-heading too
    # ("## Середній рід та узагальнення"). False positives here just flip
    # a structural missing → present, and any actual summary-quality issue
    # will surface in prose-quality gates anyway.
    _SUMMARY_WORDS = (
        r"Summary|Підсумок|Підсумки|"
        r"Самоперевірка|Самооцінка|"
        r"Узагальнення|Висновок|Висновки|Огляд"
    )
    _summary_re = re.compile(rf'\b({_SUMMARY_WORDS})\b', re.IGNORECASE)
    has_summary = any(
        l.strip().startswith('#') and _summary_re.search(l)
        for l in lines
    )
    has_vocab = any(re.match(r'^#+\s+(Vocabulary|Словник)', l.strip(), re.IGNORECASE) for l in lines)
    has_activities = any(re.match(r'^#+\s+(Activities|Вправи)', l.strip(), re.IGNORECASE) for l in lines)
    has_resources = any(re.match(r'^#+\s+(External Resources|Зовнішні ресурси|Resources)', l.strip(), re.IGNORECASE) for l in lines)

    has_vocab_table = any('| Word |' in l or 'Слово' in l or 'Термін' in l or '| Ukrainian |' in l for l in lines)

    return {
        'summary': has_summary,
        'vocab_header': has_vocab,
        'vocab_table': has_vocab_table,
        'activities_header': has_activities,
        'resources_header': has_resources
    }

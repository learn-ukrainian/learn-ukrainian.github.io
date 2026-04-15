"""Deterministic contract-compliance checks for contract-first module builds."""

from __future__ import annotations

import re

_SECTION_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)
_ACTIVITY_RE = re.compile(r"<!--\s*INJECT_ACTIVITY:\s*(.+?)\s*-->")
_META_PATTERNS = (
    re.compile(r"\bIn this (?:section|module|lesson)\b", re.IGNORECASE),
    re.compile(r"\bLet us\b", re.IGNORECASE),
    re.compile(r"\bNow let'?s\b", re.IGNORECASE),
)
_BANNED_TOKENS = (
    "пожалуйста",
    "спасибо",
    "хорошо",
    "конечно",
    "ничего",
    "сейчас",
    "здесь",
    "тоже",
    "приймати участь",
    "приймати рішення",
)


def _normalize_section_title(title: str) -> str:
    """Normalize H2 titles for contract matching.

    Parenthetical English glosses like ``(Dialogues)`` are optional for the
    written module and should not create false contract failures.
    """
    text = str(title or "").strip()
    return re.sub(r"\s*\([^)]*\)\s*$", "", text).strip()


def _parse_sections(content: str) -> list[dict]:
    matches = list(_SECTION_RE.finditer(content or ""))
    sections: list[dict] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        body = content[start:end].strip()
        sections.append({
            "title": match.group(1).strip(),
            "normalized_title": _normalize_section_title(match.group(1)),
            "body": body,
            "word_count": len(re.sub(r"<!--.*?-->", "", body).split()),
        })
    return sections


def _normalize_marker(marker: str) -> str:
    token = marker.strip().lower()
    if "," in token:
        token = token.split(",", 1)[0].strip()
    return token


def _activity_marker_matches(expected: dict, marker: str) -> bool:
    """Match a content activity marker against a contract obligation entry.

    Contract entries may pin the activity by `id` (exact match required) or
    only by `type` (bare kind like "fill-in"). Writers emit descriptive full
    markers such as "fill-in-khotity-conjugation", so bare types match when
    the content marker equals the type or begins with ``f"{type}-"``.
    """
    exp_id = expected.get("id") or ""
    if exp_id and marker == exp_id:
        return True
    exp_type = expected.get("type") or ""
    return bool(exp_type) and (marker == exp_type or marker.startswith(exp_type + "-"))


def _missing_terms(text: str, terms: list[str]) -> list[str]:
    lowered = text.lower()
    required = [term.strip() for term in terms if str(term).strip()]
    return [term for term in required if term.lower() not in lowered]


def _surface_variants(term: str) -> list[str]:
    """Return simple acceptable surface forms for a required lemma."""
    base = re.split(r"\s*\(", str(term))[0].strip().lower()
    if not base:
        return []
    variants = [base]
    if base.endswith("а") and len(base) > 1:
        variants.append(base[:-1] + "у")
    elif base.endswith("я") and len(base) > 1:
        variants.append(base[:-1] + "ю")
    return variants


def _missing_vocab_terms(text: str, terms: list[str]) -> list[str]:
    lowered = text.lower()
    missing: list[str] = []
    for term in terms:
        variants = _surface_variants(term)
        if variants and not any(variant in lowered for variant in variants):
            missing.append(term)
    return missing


def check_contract_compliance(content: str, contract: dict) -> list[dict]:
    """Return blocking and non-blocking compliance violations."""
    violations: list[dict] = []
    sections = _parse_sections(content)
    section_map = {section["normalized_title"]: section for section in sections}
    expected_titles = contract.get("teaching_beats", {}).get("section_order") or []
    actual_titles = [section["normalized_title"] for section in sections]
    normalized_expected_titles = [_normalize_section_title(title) for title in expected_titles]

    if normalized_expected_titles and actual_titles != normalized_expected_titles:
        violations.append({
            "type": "SECTION_ORDER",
            "severity": "ERROR",
            "section": "(whole module)",
            "message": f"Expected H2 order {normalized_expected_titles}, found {actual_titles}",
        })

    teaching_sections = {
        _normalize_section_title(str(item.get("name") or "").strip()): item
        for item in (contract.get("teaching_beats", {}).get("sections") or [])
        if str(item.get("name") or "").strip()
    }
    budgets = contract.get("section_word_budgets") or {}
    normalized_budgets = {
        _normalize_section_title(key): value
        for key, value in budgets.items()
    }
    for original_title, title in zip(expected_titles, normalized_expected_titles, strict=False):
        section = section_map.get(title)
        if section is None:
            violations.append({
                "type": "MISSING_SECTION",
                "severity": "ERROR",
                "section": original_title,
                "message": f"Missing required H2 section '{original_title}'",
            })
            continue
        budget = normalized_budgets.get(title) or {}
        lower = int(budget.get("min") or 0)
        if lower and section["word_count"] < lower:
            violations.append({
                "type": "WORD_BUDGET",
                "severity": "ERROR",
                "section": original_title,
                "message": (
                    f"Section '{original_title}' has {section['word_count']} words; "
                    f"contract minimum is {lower}"
                ),
            })
        required_terms = teaching_sections.get(title, {}).get("required_terms") or []
        missing_terms = _missing_terms(section["body"], required_terms)
        if missing_terms:
            violations.append({
                "type": "TEACHING_BEATS",
                "severity": "ERROR",
                "section": original_title,
                "message": (
                    f"Section '{original_title}' misses required teaching-beat terms "
                    f"{missing_terms[:6]}"
                ),
            })

    must_introduce = contract.get("vocab_grammar_targets", {}).get("must_introduce") or []
    missing_vocab = _missing_vocab_terms(content, must_introduce)
    if missing_vocab:
        violations.append({
            "type": "VOCAB_TARGETS",
            "severity": "ERROR",
            "section": "(whole module)",
            "message": f"Missing contract vocabulary targets: {missing_vocab[:6]}",
        })

    activity_obligations = contract.get("activity_obligations") or []
    markers = [_normalize_marker(marker) for marker in _ACTIVITY_RE.findall(content)]
    # Contract may specify an activity by `id` (exact full marker like
    # "fill-in-khotity-conjugation") or by `type` (bare kind like "fill-in"),
    # while writers emit descriptive full IDs. Match IDs exactly, and bare
    # types against the marker prefix so e.g. `type: fill-in` satisfies
    # `<!-- INJECT_ACTIVITY: fill-in-khotity-conjugation -->`.
    expected_entries = [
        {
            "id": str(item.get("id") or "").strip().lower(),
            "type": str(item.get("type") or "").strip().lower(),
        }
        for item in activity_obligations
        if item.get("id") or item.get("type")
    ]
    if expected_entries:
        if len(markers) < len(expected_entries):
            violations.append({
                "type": "ACTIVITY_ORDER",
                "severity": "ERROR",
                "section": "(whole module)",
                "message": f"Only {len(markers)} activity markers found; contract requires {len(expected_entries)}",
            })
        else:
            actual_prefix = markers[: len(expected_entries)]
            failed_positions = [
                (i + 1, exp, got)
                for i, (exp, got) in enumerate(zip(expected_entries, actual_prefix, strict=False))
                if not _activity_marker_matches(exp, got)
            ]
            if failed_positions:
                mismatches = [
                    f"position {idx} (expected type '{exp.get('id') or exp.get('type')}', found '{got}')"
                    for idx, exp, got in failed_positions
                ]
                violations.append({
                    "type": "ACTIVITY_ORDER",
                    "severity": "ERROR",
                    "section": "(whole module)",
                    "message": f"Activity order mismatch at {' and '.join(mismatches)}",
                })

    dialogue_acts = contract.get("dialogue_acts") or []
    for item in dialogue_acts:
        # Setting/function are scenario metadata and may be stored in English.
        # Requiring those literal strings creates false failures. Speakers are
        # the reliable deterministic grounding signal here.
        required_terms = [speaker for speaker in (item.get("speakers") or []) if speaker]
        missing_terms = _missing_terms(content, required_terms)
        if missing_terms:
            violations.append({
                "type": "DIALOGUE_ACT",
                "severity": "ERROR",
                "section": "(whole module)",
                "message": f"Dialogue situation not grounded in content; missing {missing_terms[:6]}",
            })
            break

    factual_anchors = contract.get("factual_anchors") or []
    for anchor in factual_anchors[:6]:
        title = str(anchor.get("section") or "")
        section = section_map.get(title)
        if section is None:
            continue
        terms = list(anchor.get("matched_terms") or [])
        missing_terms = _missing_terms(section["body"], terms)
        if missing_terms:
            violations.append({
                "type": "FACTUAL_ANCHOR",
                "severity": "ERROR",
                "section": title,
                "message": (
                    f"Section '{title}' misses factual anchor terms {missing_terms[:4]} "
                    f"from {anchor.get('citation', '?')}"
                ),
            })

    lowered = content.lower()
    found_banned = [token for token in _BANNED_TOKENS if token in lowered]
    if found_banned:
        violations.append({
            "type": "BANNED_PATTERN",
            "severity": "ERROR",
            "section": "(whole module)",
            "message": f"Banned contract patterns present: {found_banned}",
        })

    for pattern in _META_PATTERNS:
        match = pattern.search(content)
        if match:
            violations.append({
                "type": "META_NARRATION",
                "severity": "WARNING",
                "section": "(whole module)",
                "message": f"Formulaic meta-narration present: {match.group(0)}",
            })
            break

    return violations


def has_blocking_violations(violations: list[dict]) -> bool:
    return any(item.get("severity") == "ERROR" for item in violations)


def build_contract_correction_directive(violations: list[dict]) -> str:
    if not violations:
        return ""
    lines = [
        "<correction_directive>",
        "CRITICAL: The draft violates the shared module contract. Fix ONLY these contract items.",
    ]
    for violation in violations:
        section = violation.get("section", "(whole module)")
        lines.append(f"- FIX [{section}] {violation.get('message', '')}")
    lines.append("</correction_directive>")
    return "\n".join(lines)

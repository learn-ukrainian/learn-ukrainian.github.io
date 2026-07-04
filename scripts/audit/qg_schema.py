"""Source-language-agnostic quality-gate finding schema for issue #4307.

Defines a new canonical finding shape for curriculum QG and UA-GEC-backed
calque/grammar scoring (#2156). This module does not migrate existing evidence
files or replace legacy evidence schema constants in ``llm_qg_store`` or
``curriculum_qg_harness``.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

FINDING_SCHEMA_VERSION = "ua_qg_finding.v1"

LEGACY_EVIDENCE_SCHEMA_VERSIONS: tuple[str, ...] = (
    "llm_qg_evidence.v1",
    "curriculum_ua_qg_evidence.v1",
)

CONTACT_SOURCE_LANGS: frozenset[str] = frozenset({"ru", "pl", "en", "unknown"})
DEFAULT_CONTACT_SOURCE_LANG = "ru"

SEVERITIES: frozenset[str] = frozenset({"critical", "warning", "info"})
UA_GEC_DEFAULT_SEVERITY = "info"

CURRICULUM_DIMENSIONS: frozenset[str] = frozenset(
    {
        "surface_leakage",
        "level_policy",
        "ukrainian_style",
        "tone_register",
        "seminar_sensitivity",
    }
)
EVAL_DIMENSIONS: frozenset[str] = frozenset({"calque", "grammar"})
DIMENSIONS: frozenset[str] = CURRICULUM_DIMENSIONS | EVAL_DIMENSIONS

CHECKER_SOURCES: frozenset[str] = frozenset(
    {
        "deterministic",
        "ua_gec",
        "semantic_false_friend",
        "russicism_pattern",
        "llm",
    }
)

UA_GEC_TAGS: frozenset[str] = frozenset(
    {
        "F/Calque",
        "F/Collocation",
        "G/Case",
        "G/Gender",
        "G/Number",
        "G/Aspect",
        "G/Verb",
    }
)

UA_GEC_TAG_MAP: dict[str, dict[str, str]] = {
    "F/Calque": {
        "dimension": "calque",
        "issue_id": "UA_GEC_CALQUE",
        "contact_source_lang": DEFAULT_CONTACT_SOURCE_LANG,
    },
    "F/Collocation": {
        "dimension": "calque",
        "issue_id": "UA_GEC_COLLOCATION",
        "contact_source_lang": DEFAULT_CONTACT_SOURCE_LANG,
    },
    "G/Case": {
        "dimension": "grammar",
        "issue_id": "UA_GEC_GRAMMAR_CASE",
        "contact_source_lang": "unknown",
    },
    "G/Gender": {
        "dimension": "grammar",
        "issue_id": "UA_GEC_GRAMMAR_GENDER",
        "contact_source_lang": "unknown",
    },
    "G/Number": {
        "dimension": "grammar",
        "issue_id": "UA_GEC_GRAMMAR_NUMBER",
        "contact_source_lang": "unknown",
    },
    "G/Aspect": {
        "dimension": "grammar",
        "issue_id": "UA_GEC_GRAMMAR_ASPECT",
        "contact_source_lang": "unknown",
    },
    "G/Verb": {
        "dimension": "grammar",
        "issue_id": "UA_GEC_GRAMMAR_VERB",
        "contact_source_lang": "unknown",
    },
}

_B1_27_PHRASE_RULES: dict[str, dict[str, str]] = {
    "b1_awkward_passive_result_state": {
        "issue_id": "AWKWARD_PASSIVE_RESULT_STATE",
        "dimension": "ukrainian_style",
        "severity": "critical",
        "message": (
            "Use an active or impersonal Ukrainian instruction instead of a literal "
            "passive state."
        ),
        "quoted_bad_form": "застосунок має бути відкритий",
    },
    "b1_unnatural_anthropomorphic_warning": {
        "issue_id": "UNNATURAL_ANTHROPOMORPHISM",
        "dimension": "ukrainian_style",
        "severity": "critical",
        "message": "Abstract lesson metalanguage should not be anthropomorphized as a speaker.",
        "quoted_bad_form": "Застереження каже: будь обережним",
    },
    "b1_bad_behavior_government": {
        "issue_id": "UKRAINIAN_GRAMMAR_CALQUE",
        "dimension": "ukrainian_style",
        "severity": "critical",
        "message": "The government and nominalized behavior phrase are translated and unnatural.",
        "quoted_bad_form": "радить не робити певної поведінки",
    },
    "b1_abstract_result_process_calque": {
        "issue_id": "UNNATURAL_META_REGISTER",
        "dimension": "ukrainian_style",
        "severity": "critical",
        "message": "This abstract prompt-like sentence is not natural learner-facing Ukrainian.",
        "quoted_bad_form": "дія має дати конкретний результат чи описати процес?",
    },
    "b1_window_result_calque": {
        "issue_id": "UKRAINIAN_GRAMMAR_CALQUE",
        "dimension": "ukrainian_style",
        "severity": "critical",
        "message": "The metaphor and argument structure are literal and unidiomatic.",
        "quoted_bad_form": "доконаний вид дає результат із вікном",
    },
    "b1_kitchen_locative_context": {
        "issue_id": "CALQUED_PREPOSITION",
        "dimension": "ukrainian_style",
        "severity": "critical",
        "message": "In this ordinary locative teaching context, use the idiomatic На кухні.",
        "quoted_bad_form": "У кухні",
    },
}


class QGSchemaError(ValueError):
    """Raised when a finding payload violates the #4307 schema."""


@dataclass(frozen=True, slots=True)
class Span:
    """Byte/char span within a source file."""

    start: int | None
    end: int | None

    def as_dict(self) -> dict[str, int | None]:
        return {"start": self.start, "end": self.end}


@dataclass(frozen=True, slots=True)
class Disposition:
    """False-positive disposition metadata for a finding."""

    defect: bool = True
    teaching_contrast: bool = False
    quoted_bad_form: bool = False
    heritage_allowed: bool = False
    suppressed_fp: bool = False

    def as_dict(self) -> dict[str, bool]:
        return {
            "defect": self.defect,
            "teaching_contrast": self.teaching_contrast,
            "quoted_bad_form": self.quoted_bad_form,
            "heritage_allowed": self.heritage_allowed,
            "suppressed_fp": self.suppressed_fp,
        }


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def normalize_contact_source_lang(value: Any, *, default: str = DEFAULT_CONTACT_SOURCE_LANG) -> str:
    """Normalize contact-source language codes."""
    if value is None:
        return default
    clean = str(value).strip().lower()
    if not clean:
        return default
    if clean not in CONTACT_SOURCE_LANGS:
        raise QGSchemaError(f"unsupported contact_source_lang: {value!r}")
    return clean


def ua_gec_mapping_for_tag(tag: str) -> dict[str, str]:
    """Return dimension/issue defaults for one UA-GEC error tag."""
    clean = str(tag).strip()
    if clean not in UA_GEC_TAGS:
        raise QGSchemaError(f"unsupported ua_gec_tag: {tag!r}")
    return dict(UA_GEC_TAG_MAP[clean])


def finding_id(
    *,
    module_id: str,
    rule_id: str,
    file: str,
    excerpt: str,
    line: int | None = None,
    ua_gec_tag: str | None = None,
) -> str:
    """Return a stable finding identifier for deduplication."""
    payload = {
        "schema_version": FINDING_SCHEMA_VERSION,
        "module_id": module_id,
        "rule_id": rule_id,
        "file": file,
        "line": line,
        "excerpt": excerpt[:160],
        "ua_gec_tag": ua_gec_tag,
    }
    digest = hashlib.sha256(_json_dumps(payload).encode("utf-8")).hexdigest()
    return f"qg-{digest[:16]}"


def _span_dict(span: Span | Mapping[str, Any] | None) -> dict[str, int | None]:
    if span is None:
        return {"start": None, "end": None}
    if isinstance(span, Span):
        return span.as_dict()
    if isinstance(span, Mapping):
        start = span.get("start")
        end = span.get("end")
        return {
            "start": int(start) if isinstance(start, int) else None,
            "end": int(end) if isinstance(end, int) else None,
        }
    raise QGSchemaError("span must be a Span or mapping")


def _disposition_dict(
    disposition: Disposition | Mapping[str, Any] | None,
    *,
    quoted_bad_form: bool | None = None,
) -> dict[str, bool]:
    if disposition is None:
        base = Disposition(quoted_bad_form=bool(quoted_bad_form)).as_dict()
        return base
    if isinstance(disposition, Disposition):
        return disposition.as_dict()
    if isinstance(disposition, Mapping):
        merged = Disposition().as_dict()
        for key in merged:
            if key in disposition:
                merged[key] = bool(disposition[key])
        if quoted_bad_form is not None:
            merged["quoted_bad_form"] = bool(quoted_bad_form)
        return merged
    raise QGSchemaError("disposition must be a Disposition or mapping")


def _attribution_dict(attribution: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if attribution is None:
        return None
    if not isinstance(attribution, Mapping):
        raise QGSchemaError("attribution must be a mapping")
    out: dict[str, Any] = {}
    for key in ("corpus", "license", "doc_id", "pair_id", "attribution"):
        if key in attribution and attribution[key] is not None:
            out[key] = attribution[key]
    return out or None


def validate_finding(finding: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and normalize one finding payload."""
    if not isinstance(finding, Mapping):
        raise QGSchemaError("finding must be a mapping")

    schema_version = finding.get("schema_version", FINDING_SCHEMA_VERSION)
    if schema_version != FINDING_SCHEMA_VERSION:
        raise QGSchemaError(f"unsupported schema_version: {schema_version!r}")

    dimension = str(finding.get("dimension") or "").strip()
    if dimension not in DIMENSIONS:
        raise QGSchemaError(f"unsupported dimension: {dimension!r}")

    severity = str(finding.get("severity") or "").strip().lower()
    if severity not in SEVERITIES:
        raise QGSchemaError(f"unsupported severity: {severity!r}")

    checker = str(finding.get("checker") or finding.get("source") or "").strip()
    if checker not in CHECKER_SOURCES:
        raise QGSchemaError(f"unsupported checker/source: {checker!r}")

    contact_source_lang = normalize_contact_source_lang(finding.get("contact_source_lang"))

    ua_gec_tag = finding.get("ua_gec_tag")
    if ua_gec_tag is not None:
        clean_tag = str(ua_gec_tag).strip()
        if clean_tag not in UA_GEC_TAGS:
            raise QGSchemaError(f"unsupported ua_gec_tag: {ua_gec_tag!r}")
        ua_gec_tag = clean_tag

    issue_id = str(finding.get("issue_id") or "").strip()
    rule_id = str(finding.get("rule_id") or "").strip()
    if not issue_id:
        raise QGSchemaError("issue_id is required")
    if not rule_id:
        raise QGSchemaError("rule_id is required")

    file_name = str(finding.get("file") or "").strip()
    if not file_name:
        raise QGSchemaError("file is required")

    excerpt = str(finding.get("excerpt") or "").strip()
    if not excerpt:
        raise QGSchemaError("excerpt is required")

    line = finding.get("line")
    line_value = int(line) if isinstance(line, int) else None

    finding_key = str(finding.get("finding_id") or "").strip()
    if not finding_key:
        finding_key = finding_id(
            module_id=str(finding.get("module_id") or ""),
            rule_id=rule_id,
            file=file_name,
            excerpt=excerpt,
            line=line_value,
            ua_gec_tag=ua_gec_tag,
        )

    normalized: dict[str, Any] = {
        "schema_version": FINDING_SCHEMA_VERSION,
        "finding_id": finding_key,
        "issue_id": issue_id,
        "rule_id": rule_id,
        "dimension": dimension,
        "severity": severity,
        "checker": checker,
        "source": checker,
        "contact_source_lang": contact_source_lang,
        "file": file_name,
        "line": line_value,
        "span": _span_dict(finding.get("span")),
        "excerpt": excerpt[:160],
        "message": str(finding.get("message") or "").strip(),
        "disposition": _disposition_dict(
            finding.get("disposition"),
            quoted_bad_form=bool(finding.get("quoted_bad_form"))
            if "quoted_bad_form" in finding and not isinstance(finding.get("disposition"), Mapping)
            else None,
        ),
    }

    if ua_gec_tag is not None:
        normalized["ua_gec_tag"] = ua_gec_tag

    if finding.get("module_id"):
        normalized["module_id"] = str(finding["module_id"])

    for optional_key in (
        "suggested_form",
        "quoted_bad_form",
        "matched_form",
        "sense_context",
    ):
        if finding.get(optional_key) is not None:
            normalized[optional_key] = str(finding[optional_key])

    attribution = _attribution_dict(finding.get("attribution"))
    if attribution is not None:
        normalized["attribution"] = attribution

    false_friend = finding.get("false_friend")
    if false_friend is not None:
        if not isinstance(false_friend, Mapping):
            raise QGSchemaError("false_friend must be a mapping")
        normalized["false_friend"] = {
            key: str(false_friend[key])
            for key in (
                "word",
                "contact_meaning",
                "ukrainian_meaning",
                "replacement",
                "replacement_translation",
                "sense_context",
            )
            if false_friend.get(key) is not None
        }
        if not normalized["false_friend"].get("word"):
            raise QGSchemaError("false_friend.word is required")

    return normalized


def build_deterministic_phrase_finding(
    *,
    module_id: str,
    rule_id: str,
    file: str,
    line: int,
    excerpt: str,
    span: Span | Mapping[str, int | None] | None = None,
    contact_source_lang: str = DEFAULT_CONTACT_SOURCE_LANG,
    disposition: Disposition | Mapping[str, bool] | None = None,
) -> dict[str, Any]:
    """Build a validated B1-27-style deterministic phrase finding."""
    rule = _B1_27_PHRASE_RULES.get(rule_id)
    if rule is None:
        raise QGSchemaError(f"unknown deterministic phrase rule_id: {rule_id!r}")

    quoted_bad = rule["quoted_bad_form"]
    finding = {
        "schema_version": FINDING_SCHEMA_VERSION,
        "module_id": module_id,
        "issue_id": rule["issue_id"],
        "rule_id": rule_id,
        "dimension": rule["dimension"],
        "severity": rule["severity"],
        "checker": "deterministic",
        "contact_source_lang": contact_source_lang,
        "file": file,
        "line": line,
        "span": _span_dict(span),
        "excerpt": excerpt,
        "message": rule["message"],
        "quoted_bad_form": quoted_bad,
        "disposition": _disposition_dict(
            disposition,
            quoted_bad_form=quoted_bad.casefold() in excerpt.casefold(),
        ),
    }
    return validate_finding(finding)


def build_ua_gec_finding(
    *,
    module_id: str,
    ua_gec_tag: str,
    file: str,
    line: int,
    excerpt: str,
    message: str,
    error_form: str,
    suggested_form: str,
    span: Span | Mapping[str, int | None] | None = None,
    contact_source_lang: str | None = None,
    severity: str | None = None,
    attribution: Mapping[str, Any] | None = None,
    disposition: Disposition | Mapping[str, bool] | None = None,
    doc_id: str | None = None,
    pair_id: str | None = None,
) -> dict[str, Any]:
    """Build a validated UA-GEC F/* or G/* finding with attribution."""
    mapping = ua_gec_mapping_for_tag(ua_gec_tag)
    merged_attribution: dict[str, Any] = {
        "corpus": "UA-GEC",
        "license": "CC-BY-4.0",
        "attribution": "Syvokon et al., UNLP 2023",
    }
    if isinstance(attribution, Mapping):
        merged_attribution.update(
            {key: attribution[key] for key in attribution if attribution[key] is not None}
        )
    if doc_id:
        merged_attribution["doc_id"] = doc_id
    if pair_id:
        merged_attribution["pair_id"] = pair_id

    finding = {
        "schema_version": FINDING_SCHEMA_VERSION,
        "module_id": module_id,
        "issue_id": mapping["issue_id"],
        "rule_id": f"ua_gec_{ua_gec_tag.replace('/', '_').lower()}",
        "dimension": mapping["dimension"],
        "severity": severity or UA_GEC_DEFAULT_SEVERITY,
        "checker": "ua_gec",
        "contact_source_lang": contact_source_lang or mapping["contact_source_lang"],
        "ua_gec_tag": ua_gec_tag,
        "file": file,
        "line": line,
        "span": _span_dict(span),
        "excerpt": excerpt,
        "message": message,
        "matched_form": error_form,
        "suggested_form": suggested_form,
        "quoted_bad_form": error_form,
        "attribution": merged_attribution,
        "disposition": _disposition_dict(disposition),
    }
    return validate_finding(finding)


def build_semantic_false_friend_finding(
    *,
    module_id: str,
    file: str,
    line: int,
    excerpt: str,
    word: str,
    contact_meaning: str,
    ukrainian_meaning: str,
    replacement: str,
    replacement_translation: str,
    sense_context: str,
    span: Span | Mapping[str, int | None] | None = None,
    contact_source_lang: str = DEFAULT_CONTACT_SOURCE_LANG,
    severity: str = "critical",
    disposition: Disposition | Mapping[str, bool] | None = None,
) -> dict[str, Any]:
    """Build a validated #912 semantic false-friend finding."""
    finding = {
        "schema_version": FINDING_SCHEMA_VERSION,
        "module_id": module_id,
        "issue_id": "SEMANTIC_FALSE_FRIEND",
        "rule_id": f"semantic_false_friend_{re.sub(r'[^a-z0-9]+', '_', word.casefold()).strip('_')}",
        "dimension": "ukrainian_style",
        "severity": severity,
        "checker": "semantic_false_friend",
        "contact_source_lang": contact_source_lang,
        "file": file,
        "line": line,
        "span": _span_dict(span),
        "excerpt": excerpt,
        "message": (
            f"'{word}' is paired with the {contact_source_lang} meaning "
            f"'{contact_meaning}' instead of the Ukrainian meaning "
            f"'{ukrainian_meaning}'."
        ),
        "quoted_bad_form": word,
        "sense_context": sense_context,
        "false_friend": {
            "word": word,
            "contact_meaning": contact_meaning,
            "ukrainian_meaning": ukrainian_meaning,
            "replacement": replacement,
            "replacement_translation": replacement_translation,
            "sense_context": sense_context,
        },
        "suggested_form": replacement,
        "disposition": _disposition_dict(disposition),
    }
    return validate_finding(finding)

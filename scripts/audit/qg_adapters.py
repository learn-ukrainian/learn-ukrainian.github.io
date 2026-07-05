"""Adapter layer for normalizing quality-gate scorer signals.

The adapters in this module are intentionally thin: they route existing scorer
outputs into the canonical ``qg_schema`` finding shape and keep cheap
deterministic checks separate from future LLM judgment. They do not bulk-run
curriculum modules and they do not dispatch prompts.
"""

from __future__ import annotations

import contextlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from scripts.audit import qg_schema
from scripts.audit.checks.russicism_detection import check_russicisms
from scripts.audit.curriculum_qg_harness import scan_curriculum_module
from scripts.pipeline.semantic_russianisms import scan_plan_for_russianisms

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UA_GEC_GOLD_PATH = PROJECT_ROOT / "data" / "ua-gec-gold" / "ua-gec-gold.json"

_LEGACY_DIMENSION_ALIASES = {
    "tone_register": "tone",
}


@dataclass(frozen=True, slots=True)
class ScorerInput:
    """One bounded scorer target for adapter normalization.

    ``module_dir`` triggers a single deterministic curriculum scan when paired
    with ``level``. ``text`` triggers the existing Russicism/calque gate.
    ``plan_path`` triggers the #912 semantic false-friend linter. LLM judgments
    must be supplied as structured data; this layer never calls a model.
    """

    text: str | None = None
    file: str = "module.md"
    module_dir: Path | None = None
    level: str | None = None
    slug: str | None = None
    plan_path: Path | None = None
    fixture_id: str | None = None
    llm_judgments: Sequence[Mapping[str, Any]] = field(default_factory=tuple)


class FindingAdapter(Protocol):
    """Small interface shared by deterministic, lookup, and LLM adapters."""

    name: str
    confidence: str

    def findings(self, target: ScorerInput) -> list[dict[str, Any]]:
        """Return canonical ``qg_schema`` findings for one bounded target."""


def _schema_dimension(value: str) -> str:
    return _LEGACY_DIMENSION_ALIASES.get(value, value)


def _first_excerpt(text: str, fallback: str) -> str:
    for line in text.splitlines():
        clean = line.strip()
        if clean:
            return clean[:160]
    return fallback[:160] or "deterministic scorer finding"


def _locate_excerpt(text: str, excerpt: str) -> tuple[int | None, dict[str, int | None]]:
    start = text.find(excerpt)
    if start < 0:
        return None, qg_schema.make_span(None, None)
    return text.count("\n", 0, start) + 1, qg_schema.make_span(start, start + len(excerpt))


class DeterministicRuleAdapter:
    """Normalize cheap deterministic curriculum and Russianism/calque findings.

    Sources:
    - `scan_curriculum_module()` for the B1-27 deterministic fixture rules.
    - `check_russicisms()` for the existing Russianism/calque text gate.
    - `scan_plan_for_russianisms()` from #912 for semantic false friends in
      plan `vocabulary_hints`.
    """

    name = "deterministic_rules"
    confidence = "deterministic"

    def findings(self, target: ScorerInput) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        if target.module_dir is not None:
            findings.extend(self._curriculum_findings(target))
        if target.text is not None:
            findings.extend(self._russicism_findings(target.text, target.file))
        if target.plan_path is not None:
            findings.extend(self._semantic_plan_findings(target.plan_path))
        return findings

    def _curriculum_findings(self, target: ScorerInput) -> list[dict[str, Any]]:
        if not target.level:
            raise ValueError("DeterministicRuleAdapter requires level with module_dir")
        evidence = scan_curriculum_module(
            target.module_dir,
            level=target.level,
            slug=target.slug,
            fixture_id=target.fixture_id,
        )
        normalized: list[dict[str, Any]] = []
        for finding in _iter_dimension_findings(evidence):
            normalized.append(
                qg_schema.build_deterministic_curriculum_finding(
                    issue_id=str(finding["issue_id"]),
                    rule_id=str(finding.get("rule_id") or finding["issue_id"]),
                    dimension=_schema_dimension(str(finding["dimension"])),
                    severity=str(finding["severity"]),
                    file=str(finding["file"]),
                    line=int(finding["line"]),
                    span=finding["span"],
                    excerpt=str(finding["excerpt"]),
                    message=str(finding["message"]),
                    contact_source_lang="unknown",
                )
            )
        return normalized

    def _russicism_findings(self, text: str, file: str) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for violation in check_russicisms(text, file_path=file):
            excerpt = str(violation.get("matched") or _first_excerpt(text, str(violation.get("issue") or "")))
            normalized.append(
                qg_schema.build_finding(
                    issue_id=str(violation.get("type") or "RUSSICISM_DETECTED"),
                    issue_class="calque",
                    dimension="contact_calque",
                    severity=str(violation.get("severity") or "warning"),
                    file=file,
                    line=None,
                    span=None,
                    excerpt=excerpt,
                    message=str(violation.get("issue") or "Russicism/calque detected."),
                    contact_source_lang="ru",
                    confidence=self.confidence,
                    detector={
                        "adapter": "russicism_detection",
                        "rule_id": str(violation.get("type") or "RUSSICISM_DETECTED"),
                        "pattern_id": str(violation.get("type") or "RUSSICISM_DETECTED"),
                    },
                    attribution={
                        "corpus": "scripts.audit.checks.russicism_detection",
                        "license": None,
                        "evidence": "deterministic Russianism/calque regex gate",
                    },
                    metadata={
                        "deterministic_gate": {
                            "raw_type": violation.get("type"),
                            "fix": violation.get("fix"),
                        }
                    },
                )
            )
        return normalized

    def _semantic_plan_findings(self, plan_path: Path) -> list[dict[str, Any]]:
        if not plan_path.exists():
            return []
        plan_text = plan_path.read_text(encoding="utf-8")
        normalized: list[dict[str, Any]] = []
        for finding in scan_plan_for_russianisms(plan_path):
            excerpt = str(finding.get("original_entry") or finding.get("word") or "semantic false friend")
            line, span = _locate_excerpt(plan_text, excerpt)
            normalized.append(
                qg_schema.build_semantic_false_friend_finding(
                    word=str(finding["word"]),
                    russian_meaning=str(finding["meaning_found"]),
                    ukrainian_meaning=str(finding["ukrainian_meaning"]),
                    replacement=finding.get("replacement"),
                    matched_gloss_pattern=excerpt,
                    file=str(plan_path),
                    line=line,
                    span=span,
                    excerpt=excerpt,
                    severity="critical",
                )
            )
        return normalized


class UaGecGoldFixtureAdapter:
    """Normalize curated UA-GEC gold-fixture rows without re-labeling gold tags."""

    name = "ua_gec_gold_fixture"
    confidence = "lookup_heuristic"

    def __init__(self, fixture_path: Path = UA_GEC_GOLD_PATH, contested_sidecar_path: Path | None = None) -> None:
        self.fixture_path = fixture_path
        self.contested_sidecar_path = contested_sidecar_path
        self._payload_cache: dict[str, Any] | None = None

    def findings(self, target: ScorerInput) -> list[dict[str, Any]]:
        items = self._load_items()
        if target.fixture_id:
            items = [item for item in items if item.get("id") == target.fixture_id]
        known_limitations = self.known_limitations

        # Load sidecar if present
        contested_flags = {}
        sidecar_path = self.contested_sidecar_path or self.fixture_path.with_suffix(".contested.json")
        if sidecar_path.exists():
            with contextlib.suppress(Exception):
                contested_flags = json.loads(sidecar_path.read_text(encoding="utf-8"))

        return [self._normalize_item(item, known_limitations, contested_flags) for item in items]

    @property
    def known_limitations(self) -> dict[str, Any]:
        payload = self._load_payload()
        limitations = payload.get("known_limitations")
        return dict(limitations) if isinstance(limitations, Mapping) else {}

    def _load_payload(self) -> dict[str, Any]:
        if self._payload_cache is None:
            payload = json.loads(self.fixture_path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("UA-GEC gold fixture must be a JSON object")
            self._payload_cache = payload
        return self._payload_cache

    def _load_items(self) -> list[dict[str, Any]]:
        payload = self._load_payload()
        items = payload.get("items")
        if not isinstance(items, list):
            raise ValueError("UA-GEC gold fixture missing items list")
        return [item for item in items if isinstance(item, dict)]

    def _normalize_item(
        self,
        item: Mapping[str, Any],
        known_limitations: Mapping[str, Any],
        contested_flags: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        finding = dict(item.get("finding") or {})
        finding["confidence"] = self.confidence
        detector = dict(finding.get("detector") or {})
        detector["adapter"] = self.name
        finding["detector"] = detector
        metadata = dict(finding.get("metadata") or {})

        item_id = item.get("id")
        contested_flag = None
        if contested_flags and isinstance(contested_flags, Mapping) and item_id in contested_flags:
            contested_flag = contested_flags[item_id].get("contested")

        metadata["ua_gec_gold"] = {
            "fixture_id": item_id,
            "gold_tag": item.get("tag"),
            "gold_relabelled": False,
            "known_limitations": dict(known_limitations),
            "contested_flag": contested_flag,
            "contested_flag_follow_up": "#4364",
        }
        finding["metadata"] = metadata
        qg_schema.validate_finding(finding)
        return finding


class LlmJudgmentAdapter:
    """Placeholder normalizer for future #4309 LLM judgments.

    The adapter accepts already-structured judgments and tags them with
    `llm_judgment` confidence. Prompt construction, model dispatch, and profile
    policy stay out of this layer.
    """

    name = "llm_judgment_placeholder"
    confidence = "llm_judgment"

    def findings(self, target: ScorerInput) -> list[dict[str, Any]]:
        return [self._normalize_judgment(judgment) for judgment in target.llm_judgments]

    def _normalize_judgment(self, judgment: Mapping[str, Any]) -> dict[str, Any]:
        return qg_schema.build_finding(
            issue_id=str(judgment["issue_id"]),
            issue_class=str(judgment["issue_class"]),
            dimension=str(judgment["dimension"]),
            severity=str(judgment["severity"]),
            file=str(judgment.get("file") or "llm-review"),
            line=judgment.get("line"),
            span=judgment.get("span"),
            excerpt=str(judgment["excerpt"]),
            message=str(judgment["message"]),
            contact_source_lang=judgment.get("contact_source_lang") or judgment.get("source_lang") or "unknown",
            ua_gec_tag=judgment.get("ua_gec_tag"),
            confidence=self.confidence,
            disposition=str(judgment.get("disposition") or "defect"),
            suggested_replacement=judgment.get("suggested_replacement"),
            detector={
                "adapter": self.name,
                "rule_id": str(judgment.get("rule_id") or judgment["issue_id"]),
                "pattern_id": str(judgment.get("pattern_id") or judgment["issue_id"]),
            },
            attribution=judgment.get("attribution"),
            sense_context=judgment.get("sense_context"),
            metadata={
                "llm": {
                    "provider": judgment.get("provider"),
                    "model": judgment.get("model"),
                    "prompt_version": judgment.get("prompt_version"),
                    "placeholder_only": True,
                }
            },
        )


def _iter_dimension_findings(evidence: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    dimensions = evidence.get("dimensions")
    if not isinstance(dimensions, Mapping):
        return []
    findings: list[Mapping[str, Any]] = []
    for entry in dimensions.values():
        if isinstance(entry, Mapping) and isinstance(entry.get("findings"), list):
            findings.extend(item for item in entry["findings"] if isinstance(item, Mapping))
    return findings


def dimensions_from_findings(findings: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    """Group canonical findings into schema-valid dimension records."""

    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for finding in findings:
        qg_schema.validate_finding(finding)
        grouped.setdefault(str(finding["dimension"]), []).append(finding)
    return {
        dimension: qg_schema.build_dimension(verdict=_verdict_for_findings(items), findings=items)
        for dimension, items in grouped.items()
    }


def _verdict_for_findings(findings: Sequence[Mapping[str, Any]]) -> str:
    if any(finding.get("severity") == "critical" for finding in findings):
        return "FAIL"
    if findings:
        return "WARN"
    return "PASS"

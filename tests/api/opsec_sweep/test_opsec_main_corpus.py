"""Freeze origin/main's route-wide rewrite contract for repository prose (#9899).

The reference only reproduces the baseline's filesystem rewrite projection;
other scanner findings are never rewritten by opsec_sanitize. Keeping this
small reference local lets the regression run in shallow CI without fetching
Git history or deriving expectations from the implementation under test.
Baseline: e467138966bff83cec3edaff87f103d5bda07b84.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.api.opsec_sanitize import opsec_path_sanitizer_middleware, sanitize_document, sanitize_text

pytestmark = pytest.mark.repo_invariant

_ROOT = Path(__file__).resolve().parents[3]
# A fixed corpus of 73 public documents, not a repository tree scanner.
_CORPUS_PATHS = [
    _ROOT / relative
    for relative in (
        "agents_extensions/shared/rules/_load-via-api.md",
        "agents_extensions/shared/rules/activity-yaml.md",
        "agents_extensions/shared/rules/cli-help-standard.md",
        "agents_extensions/shared/rules/core-curriculum.md",
        "agents_extensions/shared/rules/core.md",
        "agents_extensions/shared/rules/critical-rules.md",
        "agents_extensions/shared/rules/delegate-must-use-worktree.md",
        "agents_extensions/shared/rules/fleet-comms-coordination.md",
        "agents_extensions/shared/rules/fleet-driver-routing.md",
        "agents_extensions/shared/rules/mcp-sources-and-dictionaries.md",
        "agents_extensions/shared/rules/model-assignment.md",
        "agents_extensions/shared/rules/non-negotiable-rules.md",
        "agents_extensions/shared/rules/operator-expectations.md",
        "agents_extensions/shared/rules/pipeline.md",
        "agents_extensions/shared/rules/storage-topology.md",
        "agents_extensions/shared/rules/task-scoped-reading.md",
        "agents_extensions/shared/rules/ukrainian-linguistics.md",
        "agents_extensions/shared/rules/workflow.md",
        "docs/best-practices/activity-pedagogy.md",
        "docs/best-practices/adr-management.md",
        "docs/best-practices/agent-activity-matrix.md",
        "docs/best-practices/agent-bridge.md",
        "docs/best-practices/agent-cooperation.md",
        "docs/best-practices/api-ui-improvements-proposal.md",
        "docs/best-practices/atlas-source-presentation.md",
        "docs/best-practices/audit-standards.md",
        "docs/best-practices/b2-c2-plan-architecture.md",
        "docs/best-practices/bio-image-rights.md",
        "docs/best-practices/bio-naming-canonical.md",
        "docs/best-practices/bio-research-source-tiers.md",
        "docs/best-practices/ci-health.md",
        "docs/best-practices/code-quality.md",
        "docs/best-practices/codex-thread-handoff.md",
        "docs/best-practices/context-engineering.md",
        "docs/best-practices/decision-journal.md",
        "docs/best-practices/derivational-morphology-gate.md",
        "docs/best-practices/deterministic-over-hallucination.md",
        "docs/best-practices/dialogue-situations.md",
        "docs/best-practices/dual-mode-design-tokens.md",
        "docs/best-practices/fleet-role-scorecard.md",
        "docs/best-practices/fleet-shared-doctrine.md",
        "docs/best-practices/force-flag-audit-2026-04-22.md",
        "docs/best-practices/git-hygiene.md",
        "docs/best-practices/gitflow.md",
        "docs/best-practices/guardrail-lifecycle.md",
        "docs/best-practices/harness-engineering.md",
        "docs/best-practices/heritage-attestation-engine.md",
        "docs/best-practices/hermes-usage.md",
        "docs/best-practices/hook-audit.md",
        "docs/best-practices/issue-tracking.md",
        "docs/best-practices/lesson-schema.md",
        "docs/best-practices/local-api-server.md",
        "docs/best-practices/local-ci-replay.md",
        "docs/best-practices/module-content-quality.md",
        "docs/best-practices/openai-compat-proxy.md",
        "docs/best-practices/plan-references.md",
        "docs/best-practices/plan-version-drift.md",
        "docs/best-practices/politically-charged-bios.md",
        "docs/best-practices/postmortem-management.md",
        "docs/best-practices/pr-issue-references.md",
        "docs/best-practices/prompt-engineering.md",
        "docs/best-practices/seminar-reading-links.md",
        "docs/best-practices/strict-reviewer-persona.md",
        "docs/best-practices/task-quality.md",
        "docs/best-practices/track-architecture.md",
        "docs/best-practices/typesafe-jev.md",
        "docs/best-practices/ulp-presentation-pattern.md",
        "docs/best-practices/universal-rules-registry.md",
        "docs/best-practices/v7-design-and-corpus.md",
        "docs/best-practices/vocabulary-activity-standards.md",
        "docs/best-practices/wiki-plan-review-and-lock.md",
        "docs/best-practices/word-atlas-design.md",
        "docs/best-practices/writer-prompt-appendix.md",
    )
]
# Literal detector patterns captured from the baseline, independent of the
# current scanner's constants, helpers, imports and findings.
_MAIN_PATH = re.compile(
    "(?<![A-Za-z0-9/])/(?P<root>home|Users|Volumes|private|opt|srv|tmp|var)(?![A-Za-z0-9_-])(?P<tail>/[^\\s\\\"'<>]*)?"
)
_MAIN_PROTECTED = tuple(
    re.compile(pattern, flags)
    for pattern, flags in (
        ("(?<![0-9A-Fa-f])(?:[0-9A-Fa-f]{40}|[0-9A-Fa-f]{64})(?![0-9A-Fa-f])", 32),
        (
            "(?<![A-Za-z0-9_])[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\\.[0-9]+)?(?:Z|[+-][0-9]{2}:[0-9]{2})(?![A-Za-z0-9_])",
            32,
        ),
        ("(?i)(?<![A-Za-z0-9_])epic:[0-9]+(?![A-Za-z0-9_])", 34),
        ("(?i)(?<![A-Za-z0-9_])/api(?:/[^\\s\\\"'<>]*)?", 34),
        (
            "(?<![A-Za-z0-9_])-?P(?=(?:[0-9]+(?:\\.[0-9]+)?[YMWD]|T[0-9]+(?:\\.[0-9]+)?[HMS]))(?:[0-9]+(?:\\.[0-9]+)?Y)?(?:[0-9]+(?:\\.[0-9]+)?M)?(?:[0-9]+(?:\\.[0-9]+)?W)?(?:[0-9]+(?:\\.[0-9]+)?D)?(?:T(?:[0-9]+(?:\\.[0-9]+)?H)?(?:[0-9]+(?:\\.[0-9]+)?M)?(?:[0-9]+(?:\\.[0-9]+)?S)?)?(?![A-Za-z0-9_])",
            34,
        ),
    )
)


def _origin_main_sanitize_text(text: str) -> str:
    protected = [match.span() for pattern in _MAIN_PROTECTED for match in pattern.finditer(text)]
    findings = []
    for match in _MAIN_PATH.finditer(text):
        token = match.group().rstrip(".,;:!?)]}")
        start, end = match.start(), match.start() + len(token)
        if token and not any(start < right and left < end for left, right in protected):
            findings.append((start, end))
    for start, end in reversed(findings):
        text = text[:start] + "[redacted-path]" + text[end:]
    return text


@pytest.mark.parametrize("path", _CORPUS_PATHS, ids=lambda path: str(path.relative_to(_ROOT)))
def test_sanitizer_equals_origin_main_for_repository_corpus(path):
    text = path.read_text(encoding="utf-8")
    expected = _origin_main_sanitize_text(text)
    assert sanitize_text(text) == expected
    assert sanitize_document({"markdown": text, "nested": [text]}) == {
        "markdown": expected,
        "nested": [expected],
    }


@pytest.mark.parametrize("route", ["/api/rules", "/api/state/example", "/synthetic-docs"])
def test_route_wide_middleware_equals_origin_main_without_rules_exemption(route):
    assert _CORPUS_PATHS
    corpus = {str(path.relative_to(_ROOT)): path.read_text(encoding="utf-8") for path in _CORPUS_PATHS}
    expected = {path: _origin_main_sanitize_text(text) for path, text in corpus.items()}
    app = FastAPI()
    app.middleware("http")(opsec_path_sanitizer_middleware)
    app.get(route)(lambda: corpus)
    response = TestClient(app).get(route)
    assert response.status_code == 200
    assert response.json() == expected


@pytest.mark.parametrize(
    "text",
    [
        "open ~/.ssh/fixture-key denied",
        "open ~fixture/private/key.pem denied",
        r"open C:\Users\fixture\key.pem denied",
        "open C:/Users/fixture/key.pem denied",
        r"open \\fixture-server\private\key.pem denied",
        "getaddrinfo ENOTFOUND node.example.invalid",
        "".join(("auth ", "https", "://", "u:", "Ab3dE/fG+h9=", "@node.example.invalid/r.git denied")),
        "open `/home/fixture/file`next.",
        # Path data under test, not a scratch-directory producer; keep its bytes.
        "".join(("open /", "tmp/fixture/file; /api/rules?file=/home/fixture/file")),
        "Budget ~500K/1M, fraction ~2/3, split ~50/50, cost ~35/module",
    ],
)
def test_sanitizer_equals_origin_main_for_diagnostic_shapes_outside_lane_health(text):
    assert sanitize_text(text) == _origin_main_sanitize_text(text)

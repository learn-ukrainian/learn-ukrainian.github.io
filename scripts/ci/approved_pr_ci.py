"""Exact PR-head full CI proof from complete GitHub Actions metadata."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit

from scripts.opsec.prepublish import catalog, normalize_repository

REQUIRED = frozenset({
    'Approved head identity', 'CI Gate', 'Checks', 'Secret scan', 'Dependency audit',
    'Frontend', 'Refresh pytest durations', 'pytest report', 'PR changed tests and guards',
    *(f'pytest ({i})' for i in range(1, 25)),
})


def applies(repo: str) -> bool:
    """Only the configured public monorepo has this workflow contract."""
    return any(row.get('role') == 'public-monorepo'
               and normalize_repository(row['github']) == normalize_repository(repo)
               for row in catalog().values())


@dataclass(frozen=True)
class Proof:
    state: str
    run_id: int | None = None


def title(number: int, head: str) -> str:
    return f'Approved PR #{number} head {head}'


def inspect(repo: str, number: int, head: str, get_json) -> Proof:
    """Malformed external metadata is unknown, never permission to dispatch or enqueue."""
    try:
        return _inspect(repo, number, head, get_json)
    except (KeyError, TypeError, ValueError, AttributeError):
        return Proof('unknown')


def _inspect(repo: str, number: int, head: str, get_json) -> Proof:
    """Absence requires a complete read; a known unsuccessful run never means absence."""
    repo = normalize_repository(repo).removeprefix('github.com/')
    root = f'repos/{repo}'
    workflow = get_json(f'{root}/actions/workflows/ci.yml')
    page = get_json(f'{root}/actions/workflows/ci.yml/runs?event=workflow_dispatch&head_sha={head}&per_page=100')
    if (not isinstance(workflow, dict) or type(workflow.get('id')) is not int or workflow['id'] < 1
            or workflow.get('path') != '.github/workflows/ci.yml' or workflow.get('name') != 'CI'
            or not isinstance(page, dict) or type(page.get('total_count')) is not int
            or not isinstance(page.get('workflow_runs'), list)
            or page['total_count'] != len(page['workflow_runs'])):
        return Proof('unknown')
    matching = []
    for run in page['workflow_runs']:
        if not isinstance(run, dict):
            return Proof('unknown')
        if (run.get('head_sha') != head or run.get('workflow_id') != workflow['id']
                or run.get('path') != '.github/workflows/ci.yml' or run.get('name') != 'CI'
                or run.get('event') != 'workflow_dispatch'
                or not isinstance(run.get('repository'), dict) or run['repository'].get('full_name', '').lower() != repo):
            return Proof('unknown')
        if run.get('display_title') == title(number, head):
            matching.append(run)
    if not matching:
        return Proof('absent')
    if len(matching) != 1:
        return Proof('unknown')
    run = matching[0]
    run_id = run.get('id')
    if type(run_id) is not int or run_id < 1:
        return Proof('unknown')
    if run.get('status') in {'queued', 'in_progress', 'waiting', 'pending', 'requested'}:
        return Proof('pending', run_id)
    if run.get('status') != 'completed':
        return Proof('unknown', run_id)
    if run.get('conclusion') != 'success':
        return Proof('failed', run_id)
    suite_id = run.get('check_suite_id')
    if type(suite_id) is not int or suite_id < 1:
        return Proof('unknown', run_id)
    # GitHub selects the latest effective check per name within this suite.
    # A commit-wide latest read can instead select a later admission suite.
    checks = get_json(f'{root}/check-suites/{suite_id}/check-runs?filter=latest&per_page=100')
    if (not isinstance(checks, dict) or type(checks.get('total_count')) is not int
            or not isinstance(checks.get('check_runs'), list)
            or checks['total_count'] != len(checks['check_runs'])):
        return Proof('unknown', run_id)
    found = []
    for check in checks['check_runs']:
        if not isinstance(check, dict):
            return Proof('unknown', run_id)
        suite = check.get('check_suite')
        if not isinstance(suite, dict):
            return Proof('unknown', run_id)
        if type(suite.get('id')) is not int or suite['id'] != suite_id:
            return Proof('unknown', run_id)
        if check.get('name') not in REQUIRED:
            continue
        app = check.get('app')
        if not isinstance(app, dict):
            return Proof('unknown', run_id)
        url = urlsplit(str(check.get('details_url') or ''))
        if (check.get('head_sha') != head or app.get('id') != 15368
                or app.get('slug') != 'github-actions'
                or url.netloc != 'github.com' or not url.path.startswith(f'/{repo}/actions/runs/{run_id}/')
                or check.get('status') != 'completed' or check.get('conclusion') != 'success'):
            return Proof('unknown', run_id)
        found.append(check.get('name'))
    return Proof('success' if set(found) >= REQUIRED and len(found) == len(set(found)) else 'unknown', run_id)

#!/usr/bin/env python3
"""Durable, single-process ULIF DictUA fetch phase for Atlas 20k (#5230).

This is intentionally fetch-only.  It never imports the enrichment engine or
opens ``sources.db``: its durable state is the run ledger and network cache
below ``--work-dir``.  A logical work unit is one DictUA lookup (the initial
WebForms page, search postback, and any available relation-tab postbacks).
The complete raw response envelope is content-addressed by ``NetworkCache``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

EXPECTED_COHORT_SHA256 = "858f0c7ce34d0d1e27c3519695073ea3e62bc0623010c03683137b7b730dcab4"
EXPECTED_COHORT_COUNT = 20_323
PHASE = "network_fetch"
HOST = "lcorp.ulif.org.ua"
ULIF_URL = "https://lcorp.ulif.org.ua/dictua/"
ADAPTER_VERSION = "ulif-dictua-fetch-v1"
POLITENESS_DELAY_SECONDS = 1.0
REQUEST_TIMEOUT_SECONDS = 20
COOLDOWN_SECONDS = 120.0
LEASE_TTL_SECONDS = 60.0


def _load_runner(repo: Path) -> None:
    """Import runner modules only after the explicit repository path is known."""
    sys.path.insert(0, str(repo))


@dataclass(frozen=True, slots=True)
class RetryableFetch(Exception):
    error_code: str
    cooldown_seconds: float


class DictUAClient:
    """One polite, sequential WebForms client; it holds no corpus/database handle."""

    def __init__(self, *, delay_seconds: float, timeout_seconds: int) -> None:
        self.session = requests.Session()
        self.delay_seconds = delay_seconds
        self.timeout_seconds = timeout_seconds
        self.last_request_at = 0.0
        self.session.headers.update(
            {
                "User-Agent": (
                    "learn-ukrainian-atlas/1.0 "
                    "(noncommercial educational ULIF per-lemma fetch; issue #5230)"
                )
            }
        )

    def _wait_turn(self) -> None:
        elapsed = time.monotonic() - self.last_request_at
        if self.last_request_at and elapsed < self.delay_seconds:
            time.sleep(self.delay_seconds - elapsed)

    @staticmethod
    def _retry_after(response: requests.Response) -> float:
        try:
            return max(COOLDOWN_SECONDS, float(response.headers.get("Retry-After", "")))
        except ValueError:
            return COOLDOWN_SECONDS

    @staticmethod
    def _headers(response: requests.Response) -> dict[str, str]:
        return {
            key.lower(): value
            for key, value in response.headers.items()
            if key.lower() in {"content-type", "retry-after", "server", "date"}
        }

    def _request(self, method: str, **kwargs: Any) -> requests.Response:
        self._wait_turn()
        try:
            response = self.session.request(method, ULIF_URL, timeout=self.timeout_seconds, **kwargs)
        except requests.RequestException as exc:
            raise RetryableFetch("network_error", COOLDOWN_SECONDS) from exc
        finally:
            self.last_request_at = time.monotonic()

        if response.status_code in {403, 408, 425, 429} or response.status_code >= 500:
            code = "http_429" if response.status_code == 429 else f"http_{response.status_code}"
            raise RetryableFetch(code, self._retry_after(response))
        return response

    @staticmethod
    def _tokens(html: str) -> dict[str, str] | None:
        soup = BeautifulSoup(html, "html.parser")
        values: dict[str, str] = {}
        for name in ("__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION"):
            node = soup.find("input", attrs={"name": name})
            if node is not None and node.get("value") is not None:
                values[name] = str(node.get("value"))
        return values if values.get("__VIEWSTATE") and values.get("__EVENTVALIDATION") else None

    @staticmethod
    def _has_control(html: str, control_name: str) -> bool:
        soup = BeautifulSoup(html, "html.parser")
        return soup.find("input", attrs={"name": control_name}) is not None

    @staticmethod
    def _headword(html: str, requested_word: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        article = soup.find(id="ContentPlaceHolder1_article")
        if article is not None:
            article_text = " ".join(article.get_text(" ", strip=True).split())
            for separator in (" – ", " — ", " - "):
                if separator in article_text:
                    candidate = article_text.split(separator, 1)[0].strip()
                    if candidate:
                        return candidate
        input_control = soup.find("input", attrs={"name": "ctl00$ContentPlaceHolder1$tsearch"})
        if input_control is None:
            return requested_word
        return str(input_control.get("value", requested_word)).strip() or requested_word

    @staticmethod
    def _search_result_matches(html: str, requested_word: str) -> bool | None:
        """Distinguish a real DictUA match from its unrelated-article 200 miss."""
        soup = BeautifulSoup(html, "html.parser")
        result_list = soup.find(id="ContentPlaceHolder1_dgv")
        if result_list is None:
            return None
        normalized_query = requested_word.replace("\u0301", "").casefold()
        candidates = {
            " ".join(link.get_text(" ", strip=True).split()).replace("\u0301", "").casefold()
            for link in result_list.find_all("a")
        }
        return normalized_query in candidates

    @classmethod
    def _record(cls, stage: str, response: requests.Response) -> dict[str, Any]:
        return {
            "stage": stage,
            "status_code": response.status_code,
            "headers": cls._headers(response),
            "html": response.text,
        }

    def fetch_lookup(self, lemma: str) -> dict[str, Any]:
        """Return all raw WebForms pages for one lemma, or a durable parse marker."""
        initial = self._request("GET")
        tokens = self._tokens(initial.text)
        if tokens is None:
            return {"lemma": lemma, "status": "parse_error", "responses": [self._record("initial", initial)]}

        search_data = {
            **tokens,
            "ctl00$ContentPlaceHolder1$tsearch": lemma,
            "ctl00$ContentPlaceHolder1$search.x": "10",
            "ctl00$ContentPlaceHolder1$search.y": "10",
        }
        search = self._request("POST", data=search_data)
        responses = [self._record("initial", initial), self._record("paradigm", search)]
        if search.status_code == 404:
            return {"lemma": lemma, "status": "not_found", "responses": responses}
        search_match = self._search_result_matches(search.text, lemma)
        if search_match is None:
            return {"lemma": lemma, "status": "parse_error", "responses": responses}
        if not search_match:
            return {"lemma": lemma, "status": "not_found", "responses": responses}

        tab_tokens = self._tokens(search.text)
        if tab_tokens is None:
            return {"lemma": lemma, "status": "parse_error", "responses": responses}

        headword = self._headword(search.text, lemma)
        for section, control_name in (
            ("synonyms", "ctl00$ContentPlaceHolder1$syn"),
            ("phraseology", "ctl00$ContentPlaceHolder1$phras"),
            ("antonyms", "ctl00$ContentPlaceHolder1$ant"),
        ):
            if not self._has_control(search.text, control_name):
                continue
            tab_data = {
                **tab_tokens,
                "ctl00$ContentPlaceHolder1$tsearch": headword,
                f"{control_name}.x": "10",
                f"{control_name}.y": "10",
            }
            tab = self._request("POST", data=tab_data)
            responses.append(self._record(section, tab))
            next_tokens = self._tokens(tab.text)
            if next_tokens is None:
                return {"lemma": lemma, "status": "parse_error", "responses": responses}
            tab_tokens = next_tokens
        return {"lemma": lemma, "status": "ok", "responses": responses}


def _cohort(path: Path) -> tuple[list[str], str]:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    lemmas = [line.strip() for line in raw.decode("utf-8").splitlines() if line.strip()]
    if digest != EXPECTED_COHORT_SHA256:
        raise RuntimeError(f"cohort sha mismatch: got {digest}, expected {EXPECTED_COHORT_SHA256}")
    if len(lemmas) != EXPECTED_COHORT_COUNT:
        raise RuntimeError(f"cohort count mismatch: got {len(lemmas)}, expected {EXPECTED_COHORT_COUNT}")
    if len(set(lemmas)) != len(lemmas):
        raise RuntimeError("cohort contains duplicate lemma identifiers")
    return lemmas, digest


def _event(name: str, **fields: Any) -> None:
    print(json.dumps({"event": name, "at": time.time(), **fields}, ensure_ascii=False, sort_keys=True), flush=True)


def _next_lemma(ledger: Any, run_id: str) -> str | None:
    row = ledger._require().execute(  # coordinator-only query: no worker gets this ledger
        "SELECT unit_id FROM work_units WHERE run_id = ? AND phase = ? "
        "AND state IN ('pending', 'retry_scheduled') ORDER BY unit_id LIMIT 1",
        (run_id, PHASE),
    ).fetchone()
    return None if row is None else str(row["unit_id"])


def _counts(ledger: Any, run_id: str) -> dict[str, int]:
    rows = ledger._require().execute(
        "SELECT state, COUNT(*) AS n FROM work_units WHERE run_id = ? AND phase = ? GROUP BY state",
        (run_id, PHASE),
    ).fetchall()
    return {str(row["state"]): int(row["n"]) for row in rows}


def _parsed_payload(item: Any, body: bytes) -> tuple[dict[str, Any], str]:
    envelope = json.loads(body.decode("utf-8"))
    parsed = {
        "lemma_id": item.lemma_id,
        "request_key": item.request_key,
        "status": str(envelope.get("status") or "parse_error"),
        "response_count": len(envelope.get("responses") or []),
    }
    return parsed, json.dumps(parsed, ensure_ascii=False, sort_keys=True)


def _process_lookup(cache: Any, item: Any, client: DictUAClient) -> Any:
    """Network-cache equivalent of ``process_request`` for DictUA's multi-step lookup.

    DictUA has a session-bound WebForms exchange, so the request-level cache
    identity is the complete logical lookup for one lemma.  Every underlying
    HTTP operation remains sequential and rate limited by ``DictUAClient``.
    """
    from scripts.lexicon.runner.network_cache import CacheCasStatus
    from scripts.lexicon.runner.network_worker import FetchOutcome
    from scripts.lexicon.runner.sources_guard import guard_network_worker
    from scripts.lexicon.runner.transport import item_content_hash

    with guard_network_worker():
        claim = cache.claim_request(item.request_key, cache.owner_id, host=HOST)
        if claim.status is CacheCasStatus.HOST_COOLDOWN:
            return FetchOutcome(item.lemma_id, item.request_key, "retry_scheduled", error_code="host_cooldown")
        if claim.status is CacheCasStatus.ATTEMPT_CAP_EXHAUSTED:
            return FetchOutcome(item.lemma_id, item.request_key, "failed_terminal", error_code="attempt_cap_exhausted")
        if not claim.ok:
            return FetchOutcome(item.lemma_id, item.request_key, "failed_terminal", error_code=claim.status.value)

        if claim.is_cache_hit:
            assert claim.cached_body is not None and claim.body_sha256 is not None
            parsed, parsed_json = _parsed_payload(item, claim.cached_body)
            cache.put_parsed(
                request_key=item.request_key,
                body_sha256=claim.body_sha256,
                parser_version=ADAPTER_VERSION,
                normalizer_version="none",
                schema_version="ulif-raw-envelope-v1",
                parsed_payload=parsed_json,
            )
            result = {"lemma_id": item.lemma_id, "request_key": item.request_key, "result": parsed}
            return FetchOutcome(
                item.lemma_id,
                item.request_key,
                "cache_hit_parsed",
                result=parsed,
                result_hash=item_content_hash(result),
                status_code=claim.status_code,
            )

        assert claim.lease_generation is not None
        try:
            cache.record_fetch_attempt()
            envelope = client.fetch_lookup(item.lemma_id)
        except RetryableFetch as exc:
            next_allowed = time.time() + exc.cooldown_seconds
            cache.commit_retry_scheduled(
                item.request_key,
                cache.owner_id,
                claim.lease_generation,
                host=HOST,
                next_allowed_at=next_allowed,
                error_code=exc.error_code,
            )
            return FetchOutcome(item.lemma_id, item.request_key, "retry_scheduled", error_code=exc.error_code)

        body = (json.dumps(envelope, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        raw = cache.commit_raw(
            item.request_key,
            cache.owner_id,
            claim.lease_generation,
            method=item.method,
            url=item.url,
            request_body=item.request_body,
            response_affecting_headers=item.response_affecting_headers,
            adapter_version=ADAPTER_VERSION,
            status_code=200,
            response_headers={"content-type": "application/json; charset=utf-8"},
            body=body,
            meta={"logical_request": "ulif_dictua_lookup", "lemma": item.lemma_id},
        )
        if not raw.ok:
            return FetchOutcome(item.lemma_id, item.request_key, "failed_terminal", error_code=raw.status.value)
        body_sha = hashlib.sha256(body).hexdigest()
        parsed, parsed_json = _parsed_payload(item, body)
        cache.put_parsed(
            request_key=item.request_key,
            body_sha256=body_sha,
            parser_version=ADAPTER_VERSION,
            normalizer_version="none",
            schema_version="ulif-raw-envelope-v1",
            parsed_payload=parsed_json,
        )
        result = {"lemma_id": item.lemma_id, "request_key": item.request_key, "result": parsed}
        return FetchOutcome(
            item.lemma_id,
            item.request_key,
            "done",
            result=parsed,
            result_hash=item_content_hash(result),
            fetched=True,
            status_code=200,
        )


def _run(args: argparse.Namespace) -> int:
    repo = args.repo.resolve()
    _load_runner(repo)
    from scripts.lexicon.runner.ledger import CasStatus, Ledger
    from scripts.lexicon.runner.memory import MemoryPolicy, apply_worker_memory_limit
    from scripts.lexicon.runner.network_cache import NetworkCache
    from scripts.lexicon.runner.network_worker import NetworkWorkItem

    work_dir = args.work_dir.resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    lemmas, cohort_digest = _cohort(args.cohort.resolve())
    memory_policy = MemoryPolicy(high_bytes=1536 * 1024**2, max_bytes=2048 * 1024**2)
    enforcement = apply_worker_memory_limit(memory_policy)
    if enforcement == "none":
        raise RuntimeError("MemoryPolicy could not enforce a hard cap")

    config = {
        "cohort_path": str(args.cohort.resolve()),
        "cohort_sha256": cohort_digest,
        "cohort_count": len(lemmas),
        "fetch_adapter": ADAPTER_VERSION,
        "source": ULIF_URL,
        "request_delay_seconds": POLITENESS_DELAY_SECONDS,
        "request_timeout_seconds": REQUEST_TIMEOUT_SECONDS,
        "memory_high_bytes": memory_policy.high_bytes,
        "memory_max_bytes": memory_policy.max_bytes,
    }
    from scripts.lexicon.runner.ledger import compute_run_fingerprint

    fingerprint = compute_run_fingerprint(
        cohort_digest=cohort_digest,
        enrichment_config={"phase": PHASE, "fetch_adapter": ADAPTER_VERSION},
        network_versions={"source": ULIF_URL, "policy": "sequential-1s-v1"},
    )
    client = DictUAClient(delay_seconds=POLITENESS_DELAY_SECONDS, timeout_seconds=REQUEST_TIMEOUT_SECONDS)

    with Ledger(work_dir / "ledger.sqlite", lease_ttl_seconds=LEASE_TTL_SECONDS) as ledger, NetworkCache(
        work_dir / "network-cache.sqlite", lease_ttl_seconds=LEASE_TTL_SECONDS
    ) as cache:
        existing = ledger.find_incomplete_by_fingerprint(fingerprint)
        if existing:
            resumed = ledger.resume_run(existing, fingerprint)
            if not resumed.ok:
                raise RuntimeError(f"cannot resume {existing}: {resumed.status.value} {resumed.detail}")
            run_id = existing
            lifecycle = "resumed"
        else:
            started = ledger.start_run(fingerprint, config=config)
            if not started.ok or not started.run_id:
                raise RuntimeError(f"cannot start run: {started.status.value} {started.detail}")
            run_id = started.run_id
            lifecycle = "started"
        ledger.set_phase(run_id, PHASE, "running")
        for lemma in lemmas:
            ledger.register_work_unit(run_id, lemma, unit_kind="lemma", phase=PHASE)
        _event("run_ready", lifecycle=lifecycle, run_id=run_id, fingerprint=fingerprint, memory_enforcement=enforcement, counts=_counts(ledger, run_id))

        processed = 0
        while True:
            ledger.reclaim_expired(run_id)
            cool = cache.host_cooldown_active(HOST)
            if cool is not None:
                _event("cooldown_wait", run_id=run_id, until=cool, seconds=max(0.0, cool - time.time()))
                time.sleep(min(max(0.0, cool - time.time()), 60.0))
                continue
            lemma = _next_lemma(ledger, run_id)
            if lemma is None:
                counts = _counts(ledger, run_id)
                if counts.get("leased", 0):
                    time.sleep(1.0)
                    continue
                if not counts.get("failed_terminal", 0):
                    ledger.set_phase(run_id, PHASE, "done")
                    ledger.mark_run_completed(run_id)
                    _event("run_completed", run_id=run_id, counts=counts)
                    return 0
                _event("run_terminal_failures", run_id=run_id, counts=counts)
                return 2

            item = NetworkWorkItem(
                lemma_id=lemma,
                method="POST",
                url=ULIF_URL,
                request_body=json.dumps({"adapter": ADAPTER_VERSION, "lemma": lemma}, ensure_ascii=False, sort_keys=True).encode("utf-8"),
                response_affecting_headers={"user-agent": client.session.headers["User-Agent"]},
                request_meta={"logical_request": "ulif_dictua_lookup"},
            )
            claim = ledger.claim_unit(run_id, lemma, ledger.owner_id, phase=PHASE, host=HOST)
            if not claim.ok:
                if claim.status is CasStatus.ATTEMPT_CAP_EXHAUSTED:
                    _event("attempt_cap_exhausted", run_id=run_id, lemma=lemma)
                continue
            assert claim.lease_generation is not None
            outcome = _process_lookup(cache, item, client)
            if outcome.status in {"done", "cache_hit_parsed"}:
                committed = ledger.commit_result(
                    run_id, lemma, ledger.owner_id, claim.lease_generation, "done", result_hash=outcome.result_hash, phase=PHASE
                )
            elif outcome.status == "retry_scheduled":
                deadline = cache.host_cooldown_active(HOST) or (time.time() + COOLDOWN_SECONDS)
                if outcome.error_code == "http_429":
                    committed = ledger.handle_http_429(
                        run_id, lemma, ledger.owner_id, claim.lease_generation, host=HOST, next_allowed_at=deadline, phase=PHASE
                    )
                else:
                    ledger.set_host_cooldown(HOST, deadline)
                    committed = ledger.commit_result(
                        run_id, lemma, ledger.owner_id, claim.lease_generation, "retry_scheduled", error_code=outcome.error_code, phase=PHASE
                    )
            else:
                committed = ledger.commit_result(
                    run_id, lemma, ledger.owner_id, claim.lease_generation, "failed_terminal", error_code=outcome.error_code, phase=PHASE
                )
            processed += 1
            _event(
                "lemma_processed", run_id=run_id, lemma=lemma, outcome=outcome.status,
                error_code=outcome.error_code, committed=committed.status.value, counts=_counts(ledger, run_id),
            )
            if args.max_lemmas is not None and processed >= args.max_lemmas:
                _event("invocation_limit_reached", run_id=run_id, processed=processed, counts=_counts(ledger, run_id))
                return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--work-dir", type=Path, default=Path("/home/ops/atlas-runner/run-20k"))
    parser.add_argument(
        "--cohort",
        type=Path,
        default=Path("data/lexicon/cohort-20k-20260717.txt"),
    )
    parser.add_argument("--max-lemmas", type=int, default=None)
    args = parser.parse_args()
    return _run(args)


if __name__ == "__main__":
    raise SystemExit(main())

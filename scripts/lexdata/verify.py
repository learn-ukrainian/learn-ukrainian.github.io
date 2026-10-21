"""Generation invariants (design r3 §8 "Invariants", §6.5 step 2).

``verify_generation`` runs every check on an open connection and returns a
receipt of counts only (no lexical text). ``build_store`` runs it on the temp
generation before publication; ``python -m scripts.lexdata verify`` runs it
read-only on a published file. Any violation fails the generation.
"""

from __future__ import annotations

import json
import unicodedata
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

from scripts.lexdata import rule_tables, transforms
from scripts.lexdata.canonical import canonical_json, sha256_canonical
from scripts.lexdata.derive import row_sha256
from scripts.lexdata.generation import MetaMalformed, read_meta
from scripts.lexdata.normalize import ENTITY_RE, letter_script
from scripts.lexdata.records import L0Row, UnitInput

VERIFY_VERSION = "1"
_FETCH = 5000


@dataclass
class VerifyReport:
    generation: str | None
    violations: Counter[str] = field(default_factory=Counter)
    counts: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not any(self.violations.values())

    def receipt(self) -> dict[str, Any]:
        return {
            "verify_version": VERIFY_VERSION,
            "generation": self.generation,
            "ok": self.ok,
            "violations": dict(sorted((k, v) for k, v in self.violations.items() if v)),
            "counts": self.counts,
        }

    def receipt_json(self) -> str:
        return canonical_json(self.receipt())

    def receipt_sha256(self) -> str:
        return sha256_canonical(self.receipt())


def _rows(conn: Any, sql: str, params: tuple[Any, ...] = ()) -> Iterator[tuple[Any, ...]]:
    cursor = conn.execute(sql, params)
    while batch := cursor.fetchmany(_FETCH):
        yield from batch


def _scalar(conn: Any, sql: str, params: tuple[Any, ...] = ()) -> Any:
    return conn.execute(sql, params).fetchone()[0]


def candidate_set_sha256(conn: Any, link_id: int) -> str:
    """§5.4: hash of each surviving candidate's lexeme id, eligibility and entry fingerprint."""
    survivors = sorted(
        [lexeme, eligibility, fingerprint]
        for lexeme, eligibility, fingerprint in conn.execute(
            "SELECT lexeme_id, eligibility, entry_fingerprint FROM l2_candidate "
            "WHERE link_id = ? AND dropped_by_rule IS NULL", (link_id,)))
    return sha256_canonical(survivors)


def adjudication_input_fingerprint(row_sha: str, candidate_sha: str) -> str:
    return sha256_canonical([row_sha, candidate_sha])


def _key_problem(value: str | None, *, stressed: bool) -> bool:
    if value is None or not value:
        return True
    decomposed = unicodedata.normalize("NFD", value)
    if "̀" in decomposed or (not stressed and "́" in decomposed):
        return True
    if ENTITY_RE.search(value):
        return True
    return any(char.isalpha() and letter_script(char) != "cyrillic" for char in value)


def _check_l1(conn: Any, report: VerifyReport, meta: dict[str, Any], binding: transforms.TransformBinding) -> None:
    v = report.violations
    digests = meta["l1_transform_digests"]
    normalizer = binding.normalizer.impl
    units_by_source: Counter[str] = Counter()
    for unit_id, source_id, locator, fingerprint, digest, kind, parent_loc, parent_id in _rows(
            conn, "SELECT unit_id, source_id, l0_locator, unit_input_fingerprint, l1_transform_digest, unit_kind, "
                  "parent_l0_locator, parent_unit_id FROM l1_source_unit ORDER BY unit_id"):
        units_by_source[source_id] += 1
        if digests.get(source_id) != digest:
            v["l1_unit_transform_digest_mismatch"] += 1
        if parent_loc is not None and parent_id is None:
            v["l1_unit_parent_unresolved"] += 1
        inputs = tuple(L0Row(loc, fp) for loc, fp in conn.execute(
            "SELECT l0_row_locator, l0_row_fingerprint FROM l1_unit_input WHERE unit_id = ?", (unit_id,)))
        if not inputs or UnitInput(source_id, locator, kind, inputs).unit_input_fingerprint != fingerprint:
            v["l1_unit_input_fingerprint_mismatch"] += 1
    report.counts["units_by_source"] = dict(sorted(units_by_source.items()))
    v["l1_unit_without_disposition"] += _scalar(
        conn, "SELECT count(*) FROM l1_source_unit u LEFT JOIN l1_unit_disposition d USING (unit_id) "
              "WHERE d.unit_id IS NULL")
    v["l1_unit_disposition_invalid"] += sum(
        1 for (value,) in _rows(conn, "SELECT disposition FROM l1_unit_disposition")
        if not rule_tables.is_unit_disposition(value))
    v["l1_line_disposition_invalid"] += sum(
        1 for (value,) in _rows(conn, "SELECT disposition FROM l1_line")
        if not rule_tables.is_line_disposition(value))
    v["l1_refused_unit_has_items"] += _scalar(
        conn, "SELECT count(*) FROM l1_lex_item i JOIN l1_unit_disposition d USING (unit_id) "
              "WHERE d.disposition != 'imported'")
    for source_id, spec in binding.sources.items():
        if spec.expected_units is not None and units_by_source.get(source_id, 0) != spec.expected_units:
            v["l1_denominator_mismatch"] += 1
    for source_id in units_by_source:
        if source_id not in digests:
            v["l1_source_without_digest"] += 1

    leaves = accepted = refused = 0
    for (raw_span, surface, ks, ku, kf, case, grammar, marker, flags, repairs, refusal, rights,
         stored_sha, member_index, role, parent_key) in _rows(
            conn, "SELECT i.raw_span, i.surface, i.key_stressed, i.key_unstressed, i.key_fold, "
                  "i.case_signal, i.grammar_parsed, i.homonym_marker, i.norm_flags, i.proposed_repairs, "
                  "i.refusal_code, i.rights_class, i.row_sha256, i.member_index, i.role, p.item_key "
                  "FROM l1_lex_item i LEFT JOIN l1_lex_item p ON p.item_id = i.parent_item_id "
                  "ORDER BY i.item_id"):
        leaves += 1
        if surface != unicodedata.normalize("NFC", surface):
            v["l1_surface_not_nfc"] += 1
        if not rights:
            v["l1_missing_rights_class"] += 1
        if refusal is None:
            accepted += 1
            if _key_problem(ks, stressed=True) or _key_problem(ku, stressed=False) or _key_problem(kf, stressed=False):
                v["l1_accepted_key_invalid"] += 1
            if kf != (ku or "").casefold():
                v["l1_fold_not_casefold"] += 1
            again = normalizer(raw_span)
            if (again.key_stressed, again.key_unstressed, again.key_fold, again.case_signal) != (ks, ku, kf, case):
                v["l1_key_not_derived_by_bound_normalizer"] += 1
        else:
            refused += 1
            if not rule_tables.is_refusal_code(refusal):
                v["l1_refusal_code_unknown"] += 1
            if ks is not None or ku is not None or kf is not None:
                v["l1_refused_row_has_keys"] += 1
        fields = {"raw_span": raw_span, "surface": surface, "key_stressed": ks, "key_unstressed": ku,
                  "key_fold": kf, "case_signal": case, "grammar_parsed": grammar, "homonym_marker": marker,
                  "norm_flags": flags, "proposed_repairs": repairs, "refusal_code": refusal, "rights_class": rights}
        if row_sha256(fields, parent_item_key=parent_key, member_index=member_index, role=role) != stored_sha:
            v["l1_row_sha256_mismatch"] += 1
    report.counts.update({"leaves": leaves, "accepted_leaves": accepted, "refused_leaves": refused,
                          "lines": _scalar(conn, "SELECT count(*) FROM l1_line")})


def _check_l2(conn: Any, report: VerifyReport) -> None:
    v = report.violations
    links = _scalar(conn, "SELECT count(*) FROM l2_link")
    leaves = report.counts.get("leaves", 0)
    if links != leaves:
        v["l2_leaf_link_count_mismatch"] += 1
    v["l2_leaf_without_link"] += _scalar(
        conn, "SELECT count(*) FROM l1_lex_item i LEFT JOIN l2_link l USING (item_id) WHERE l.link_id IS NULL")
    v["l2_link_key_differs_from_leaf"] += _scalar(
        conn, "SELECT count(*) FROM l2_link l JOIN l1_lex_item i USING (item_id) WHERE "
              "l.key_stressed IS NOT i.key_stressed OR l.key_unstressed IS NOT i.key_unstressed "
              "OR l.key_fold IS NOT i.key_fold")
    v["l2_candidate_hash_missing"] += _scalar(conn, "SELECT count(*) FROM l2_link WHERE candidate_set_sha256 IS NULL")
    v["l2_refusal_status_mismatch"] += _scalar(
        conn, "SELECT count(*) FROM l2_link l JOIN l1_lex_item i USING (item_id) "
              "WHERE (i.refusal_code IS NOT NULL) != (l.status = 'refused')")
    v["l2_unavailable_with_candidates"] += _scalar(
        conn, "SELECT count(*) FROM l2_link l WHERE l.status = 'unavailable' AND EXISTS "
              "(SELECT 1 FROM l2_candidate c WHERE c.link_id = l.link_id)")
    v["l2_lexeme_without_resolution"] += _scalar(
        conn, "SELECT count(*) FROM l2_link l WHERE l.lexeme_id IS NOT NULL AND NOT (l.status = 'exact' OR "
              "(l.status = 'held' AND EXISTS (SELECT 1 FROM l2_adjudication a WHERE "
              "a.adjudication_id = l.adjudication_id AND a.state = 'admitted')))")
    v["l2_exact_not_single_eligible"] += _scalar(
        conn, "SELECT count(*) FROM l2_link l WHERE l.status = 'exact' AND NOT ("
              "l.lexeme_id IS NOT NULL AND "
              "(SELECT count(*) FROM l2_candidate c WHERE c.link_id = l.link_id AND c.dropped_by_rule IS NULL "
              " AND c.eligibility = 'eligible') = 1 AND "
              "(SELECT count(*) FROM l2_candidate c WHERE c.link_id = l.link_id AND c.dropped_by_rule IS NULL "
              " AND c.eligibility = 'unknown') = 0 AND "
              "EXISTS (SELECT 1 FROM l2_candidate c WHERE c.link_id = l.link_id AND c.dropped_by_rule IS NULL "
              " AND c.lexeme_id = l.lexeme_id))")
    v["l2_split_without_two_children"] += _scalar(
        conn, "SELECT count(*) FROM l2_link l WHERE l.status = 'split' AND "
              "(SELECT count(*) FROM l1_lex_item c WHERE c.parent_item_id = l.item_id) < 2")
    for link_id, stored in _rows(conn, "SELECT link_id, candidate_set_sha256 FROM l2_link "
                                       "WHERE candidate_set_sha256 IS NOT NULL"):
        if candidate_set_sha256(conn, link_id) != stored:
            v["l2_candidate_hash_mismatch"] += 1
    for link_id, target, fingerprint, state in _rows(
            conn, "SELECT link_id, target_lexeme_id, input_fingerprint, state FROM l2_adjudication"):
        if state == "invalidated":
            continue
        if link_id is None:
            v["l2_adjudication_unbound"] += 1
            continue
        row_sha, cand_sha = conn.execute(
            "SELECT i.row_sha256, l.candidate_set_sha256 FROM l2_link l JOIN l1_lex_item i USING (item_id) "
            "WHERE l.link_id = ?", (link_id,)).fetchone()
        if adjudication_input_fingerprint(row_sha, cand_sha) != fingerprint:
            v["l2_adjudication_fingerprint_drift"] += 1
        if not _scalar(conn, "SELECT count(*) FROM l2_candidate WHERE link_id = ? AND lexeme_id = ? "
                             "AND dropped_by_rule IS NULL", (link_id, target)):
            v["l2_adjudication_target_not_candidate"] += 1
    report.counts["link_status"] = dict(sorted(Counter(
        status for (status,) in _rows(conn, "SELECT status FROM l2_link")).items()))
    report.counts["adjudication_state"] = dict(sorted(Counter(
        state for (state,) in _rows(conn, "SELECT state FROM l2_adjudication")).items()))
    report.counts["l3_card_input"] = _scalar(conn, "SELECT count(*) FROM l3_card_input")


def verify_generation(conn: Any, *, binding: transforms.TransformBinding = transforms.DEFAULT_BINDING,
                      expect_status: str | None = None) -> VerifyReport:
    """Run every invariant. ``expect_status`` pins ``candidate`` (pre-publish) or ``published``."""
    try:
        meta = read_meta(conn)
    except MetaMalformed:
        report = VerifyReport(None)
        report.violations["meta_malformed"] += 1
        return report
    report = VerifyReport(None if meta is None else meta.get("generation"))
    v = report.violations
    integrity = conn.execute("PRAGMA integrity_check").fetchall()
    if integrity != [("ok",)]:
        v["sqlite_integrity"] += 1
    v["sqlite_foreign_keys"] += len(conn.execute("PRAGMA foreign_key_check").fetchall())
    if meta is None:
        v["meta_missing"] += 1
        return report
    if expect_status is not None and meta["status"] != expect_status:
        v["meta_status_unexpected"] += 1
    if meta["normalizer_digest"] != transforms.normalizer_digest(binding):
        v["meta_normalizer_digest_differs_from_verifier"] += 1
        return report
    if sha256_canonical(meta["input_manifest"]) != meta["input_manifest_sha256"]:
        v["meta_input_manifest_sha256_mismatch"] += 1
    if sha256_canonical(meta["normalizer_manifest"]) != meta["normalizer_digest"]:
        v["meta_normalizer_manifest_mismatch"] += 1
    for source_id, manifest in meta["transform_manifest"].items():
        if sha256_canonical(manifest) != meta["l1_transform_digests"].get(source_id):
            v["meta_transform_manifest_mismatch"] += 1
    _check_l1(conn, report, meta, binding)
    _check_l2(conn, report)
    return report


def receipt_text(report: VerifyReport) -> str:
    return json.dumps(report.receipt(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"

"""Steward-only Phase 4 receipt checks and immutable gold bundles (#10514).

This module validates evidence bindings. It neither grants source clearance nor
creates an OS isolation boundary. The caller supplies independently trusted pins.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, validators

from scripts.common.repo_root import main_checkout_root
from scripts.projects.open_model_data import source_completeness_manifest as accounting

TEXT = {"type": "string", "pattern": r"\S"}
SHA = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
COUNT = {"type": "integer", "minimum": 1}
VALIDATOR = validators.extend(
    Draft202012Validator,
    type_checker=Draft202012Validator.TYPE_CHECKER.redefine("integer", lambda _, value: type(value) is int),
)


def obj(properties: dict) -> dict:
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


def array(items: dict, minimum: int = 1) -> dict:
    return {"type": "array", "items": items, "minItems": minimum, "uniqueItems": True}


REF = obj({"path": TEXT, "sha256": SHA})
ACTOR_ID = {"type": "string", "pattern": "^[a-z0-9][a-z0-9._:-]*$"}
ACTOR = obj({"id": ACTOR_ID, "family": ACTOR_ID})
ADJUDICATOR = obj({"id": ACTOR_ID, "family": ACTOR_ID, "qualification": REF})
INPUT_NAMES = (*accounting.SCHEMAS, "atlas_manifest", "accounting_receipt", "census", "complete_data_receipt",
               "development_membership")
SPEC = obj({
    "schema_version": {"const": "word-card-gold-spec.v1"},
    "inputs": obj(dict.fromkeys(INPUT_NAMES, REF)),
    "universe_count": COUNT,
    "candidate_entry_count": COUNT,
    "case_count": COUNT,
    "assembler_build_sha256": SHA,
    "protected_root": TEXT,
    "strata": {"type": "object", "minProperties": 1, "propertyNames": TEXT, "additionalProperties": COUNT},
    "required_fields": array(TEXT),
    "roles": obj({"assembler": ACTOR, "steward": ACTOR, "adjudicators": array(ADJUDICATOR, 2)}),
    "selection": obj({"method": {"const": "fresh-source-side"}, "evidence": REF,
                      "assembler_outputs_seen": {"const": False}}),
})
CLEARANCE = obj({
    "schema_version": {"const": "word-card-complete-data.v1"},
    "status": {"const": "COMPLETE_DATA_APPROVED"},
    "phase1": {"const": "COMPLETE"}, "phase2": {"const": "COMPLETE"},
    "candidate": {"const": "Candidate A Lexical Universe v1"},
    "accounting_sha256": SHA, "census_sha256": SHA, "lexical_universe_sha256": SHA,
    "approved_by": ACTOR,
    "prerequisites": obj({name: REF for name in (
        "source_authority", "snapshot_boundary", "lexical_fidelity", "phase1_acceptance", "phase2_acceptance",
        "candidate_a_reconciliation",
    )}),
})
CLAIM = obj({"value": {}, "reference": REF, "pointer": TEXT, "scope": TEXT, "source_unit": accounting.LINK})
EXPECTATION = obj({
    "field": TEXT, "state": {"enum": ["value", "conflict", "abstention"]},
    "claims": array(CLAIM), "reason": TEXT,
    "votes": array(obj({"adjudicator_id": TEXT, "disposition": {"enum": ["agree", "disagree", "abstain"]}}), 2),
})
MEMBER_FIELDS = {
    "case_id": TEXT, "member_id": TEXT, "stratum": TEXT,
    "source_keys": array(TEXT), "aliases": array(TEXT, 0), "related_source_keys": array(TEXT, 0),
}
CASES = obj({"schema_version": {"const": "word-card-gold-cases.v1"},
             "cases": array(obj({**MEMBER_FIELDS, "expectations": array(EXPECTATION)}))})
MEMBERSHIP = obj({"schema_version": {"const": "word-card-gold-membership.v1"}, "cases": array(obj(MEMBER_FIELDS))})
ANSWERS = obj({"schema_version": {"const": "word-card-gold-answers.v1"},
               "cases": array(obj({"case_id": TEXT, "expectations": array(EXPECTATION)}))})
SEAL = obj({"schema_version": {"const": "word-card-gold-seal.v1"}, "spec_sha256": SHA,
            "membership_sha256": SHA, "answers_sha256": SHA, "case_count": COUNT,
            "isolation": {"const": "UNVERIFIED"}})
RESOURCES = ["membership", "answers", "aliases", "related"]
ACCESS = obj({"actor_id": ACTOR_ID, "resource": {"enum": RESOURCES},
              "operation": {"enum": ["read", "write"]}, "allowed": {"type": "boolean"}})
ISOLATION = obj({
    "schema_version": {"const": "word-card-gold-isolation.v1"},
    "spec_sha256": SHA, "seal_sha256": SHA, "assembler_build_sha256": SHA,
    "verified_by": ACTOR, "custody_evidence": array(REF),
    "readable_roots": array(TEXT), "writable_roots": array(TEXT),
    "assembler_inputs": array(obj({"role": {"enum": ["source", "mutation"]}, "reference": REF})),
    "roots_complete": {"const": True}, "log_complete": {"const": True},
    "alias_related_closure_checked": {"const": True}, "adjudication_blind": {"const": True},
    "access_log": array(ACCESS),
})


class Refusal(ValueError):
    """A fixed diagnostic safe to expose without protected identities or paths."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Refusal(message)


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode("utf-8")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def validate(value: Any, schema: dict, label: str) -> None:
    require(not next(VALIDATOR(schema).iter_errors(value), None), "Invalid " + label)


def decode(raw: bytes | str) -> Any:
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON key")
            result[key] = value
        return result

    value = json.loads(raw.decode("utf-8") if isinstance(raw, bytes) else raw, object_pairs_hook=pairs)
    canonical(value)  # Reject nonfinite values and invalid Unicode, including unused fields.
    return value


def read(path: Path, expected: str | None = None) -> tuple[bytes, Any]:
    raw = path.read_bytes()
    if expected is not None:
        validate(expected, SHA, "trusted digest")
        require(sha(raw) == expected, "Artifact digest mismatch")
    value = decode(raw)
    return raw, value


def reference(ref: dict, base: Path) -> bytes:
    validate(ref, REF, "reference")
    raw = (base / ref["path"]).read_bytes()
    require(sha(raw) == ref["sha256"], "Referenced evidence digest mismatch")
    return raw


def complete_data(spec: dict, base: Path) -> tuple[dict, set[str]]:
    """Replay accounting rather than trusting receipt status strings or output hashes."""
    refs = spec["inputs"]
    for ref in refs.values():
        reference(ref, base)
    paths = {name: base / refs[name]["path"] for name in accounting.SCHEMAS}
    outputs, receipt = accounting.account(paths, atlas_manifest=base / refs["atlas_manifest"]["path"])
    receipt.pop("_input_paths")
    for name in (*accounting.SCHEMAS, "atlas_manifest"):
        require(receipt["inputs"][name]["sha256"] == refs[name]["sha256"], "Accounting input changed during replay")
    _, supplied = read(base / refs["accounting_receipt"]["path"], refs["accounting_receipt"]["sha256"])
    require(canonical(receipt) == canonical(supplied), "Accounting receipt replay mismatch")
    require(receipt["status"] == "STRUCTURALLY_ACCOUNTED" and receipt["gap_count"] == 0,
            "Complete-data gate: source accounting has unresolved gaps")
    for output in receipt["outputs"]:
        raw = (base / refs["accounting_receipt"]["path"]).parent.joinpath(output["path"]).read_bytes()
        require(raw == outputs[output["path"]], "Accounting output replay mismatch")
    census_raw = reference(refs["census"], base)
    require(census_raw == outputs.get("atlas-census.json"), "Candidate A census replay mismatch")
    census = json.loads(census_raw)
    require(census["entry_count"] == spec["candidate_entry_count"], "Frozen Candidate A denominator mismatch")
    require(receipt["lexical_member_count"] == spec["universe_count"], "Frozen universe denominator mismatch")
    _, clearance = read(base / refs["complete_data_receipt"]["path"], refs["complete_data_receipt"]["sha256"])
    validate(clearance, CLEARANCE, "complete-data receipt")
    for key, ref_name in (("accounting_sha256", "accounting_receipt"), ("census_sha256", "census"),
                          ("lexical_universe_sha256", "lexical_universe")):
        require(clearance[key] == refs[ref_name]["sha256"], "Complete-data receipt binding mismatch")
    require(clearance["approved_by"]["id"] != spec["roles"]["assembler"]["id"], "Assembler cannot clear source data")
    clearance_base = (base / refs["complete_data_receipt"]["path"]).parent
    for ref in clearance["prerequisites"].values():
        reference(ref, clearance_base)
    _, universe = read(paths["lexical_universe"], refs["lexical_universe"]["sha256"])
    authenticated = {row["sha256"] for row in receipt["artifacts"]}
    authenticated.update(refs[name]["sha256"] for name in accounting.SCHEMAS)
    return universe, authenticated


def load_spec(path: Path, expected_sha256: str) -> tuple[dict, dict, set[str]]:
    _, spec = read(path, expected_sha256)
    validate(spec, SPEC, "frozen evaluation specification")
    protected = Path(spec["protected_root"])
    repo = main_checkout_root(Path(__file__).resolve().parents[2]).resolve()
    require(protected.is_absolute() and protected.is_dir() and not protected.resolve().is_relative_to(repo)
            and not repo.is_relative_to(protected.resolve()),
            "Protected root must be an existing directory outside the repository")
    require(not any(p.is_symlink() for p in (protected, *protected.parents)), "Symlink protected root refused")
    require(path.resolve().is_relative_to(protected.resolve()), "Specification outside protected custody")
    require(sum(spec["strata"].values()) == spec["case_count"], "Frozen stratum denominator mismatch")
    require("identity" in spec["required_fields"], "Expected identity coverage is required")
    roles = spec["roles"]
    actors = [roles["assembler"], roles["steward"], *roles["adjudicators"]]
    require(len({actor["id"] for actor in actors}) == len(actors), "Evaluation roles must be distinct")
    families = {actor["family"] for actor in roles["adjudicators"]}
    require(len(families) >= 2 and roles["assembler"]["family"] not in families,
            "Adjudicators require two independent families outside the assembler family")
    for actor in roles["adjudicators"]:
        reference(actor["qualification"], path.parent)
    reference(spec["selection"]["evidence"], path.parent)
    universe, authenticated = complete_data(spec, path.parent)
    return spec, universe, authenticated


def pointer_value(document: Any, pointer: str) -> Any:
    require(pointer.startswith("/") and re.search(r"~(?![01])", pointer) is None, "Invalid source JSON pointer")
    for token in pointer[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(document, list):
            require(re.fullmatch(r"0|[1-9][0-9]*", token) is not None, "Invalid source array index")
            document = document[int(token)]
        else:
            require(isinstance(document, dict), "Source pointer does not resolve")
            document = document[token]
    return document


def validate_cases(cases: dict, spec: dict, universe: dict, authenticated: set[str], base: Path) -> None:
    validate(cases, CASES, "gold cases")
    rows = cases["cases"]
    require(len(rows) == spec["case_count"], "Frozen case denominator mismatch")
    require(Counter(row["stratum"] for row in rows) == spec["strata"], "Frozen failure-stratum coverage mismatch")
    for field in ("case_id", "member_id"):
        require(len({row[field] for row in rows}) == len(rows), "Duplicate case or universe member")
    members = {row["member_id"]: row for row in universe["members"]}
    development = decode(reference(spec["inputs"]["development_membership"], base))
    validate(development, obj({"protected_keys": array(TEXT)}), "development membership")
    adjudicators = {actor["id"] for actor in spec["roles"]["adjudicators"]}
    source_ref, stage_ref = spec["inputs"]["source_manifest"], spec["inputs"]["stage_evidence"]
    _, sources = read(base / source_ref["path"], source_ref["sha256"])
    _, stages = read(base / stage_ref["path"], stage_ref["sha256"])
    unit_evidence = {}
    for source_range in sources["ranges"]:
        for unit in source_range["units"]:
            link = {"range_id": source_range["range_id"], "identity": unit["identity"]}
            unit_evidence[canonical(link)] = {unit["sha256"], source_range["index"]["sha256"]}
    for record in stages["records"]:
        link = {"range_id": record["range_id"], "identity": record["identity"]}
        unit_evidence[canonical(link)].update(ref["sha256"] for ref in record["evidence"])
    for row in rows:
        require(row["member_id"] in members, "Case outside frozen source universe")
        keys = {link["identity"]["key"] for link in members[row["member_id"]]["source_units"]}
        require(set(row["source_keys"]) == keys, "Case source identity coverage mismatch")
        protected = {row["case_id"], row["member_id"], *keys, *row["aliases"], *row["related_source_keys"]}
        require(not protected.intersection(development["protected_keys"]), "Development case reused as gold")
        expectations = row["expectations"]
        require(Counter(item["field"] for item in expectations) == Counter(spec["required_fields"]),
                "Expected field coverage mismatch")
        for expectation in expectations:
            votes = expectation["votes"]
            require(Counter(v["adjudicator_id"] for v in votes) == Counter(adjudicators),
                    "Independent adjudicator coverage mismatch")
            dispositions = {v["disposition"] for v in votes}
            state = expectation["state"]
            require("disagree" not in dispositions or state == "conflict", "Disagreement must remain explicit")
            require(dispositions != {"abstain"} or state == "abstention", "Abstention must remain explicit")
            values = {canonical(claim["value"]) for claim in expectation["claims"]}
            require(state != "value" or (len(values) == 1 and "agree" in dispositions), "Invalid resolved expectation")
            require(state != "conflict" or len(values) >= 2, "Conflict requires distinct source values")
            for claim in expectation["claims"]:
                ref = claim["reference"]
                require(ref["sha256"] in authenticated, "Expectation lacks authenticated source evidence")
                link = canonical(claim["source_unit"])
                require(link in {canonical(item) for item in members[row["member_id"]]["source_units"]},
                        "Expectation cites another case's source unit")
                require(ref["sha256"] in unit_evidence[link], "Evidence is not bound to the cited source unit")
                if expectation["field"] == "identity":
                    require(claim["value"] == claim["source_unit"]["identity"], "Expected identity differs from source identity")
                _, document = read(base / ref["path"], ref["sha256"])
                require(canonical(pointer_value(document, claim["pointer"])) == canonical(claim["value"]),
                        "Expected value differs from exact source evidence")


def bundle_documents(cases: dict, spec_sha256: str) -> dict[str, bytes]:
    membership = {"schema_version": "word-card-gold-membership.v1", "cases": [
        {key: row[key] for key in MEMBER_FIELDS} for row in cases["cases"]
    ]}
    answers = {"schema_version": "word-card-gold-answers.v1", "cases": [
        {"case_id": row["case_id"], "expectations": row["expectations"]} for row in cases["cases"]
    ]}
    files = {"membership.json": canonical(membership), "answers.json": canonical(answers)}
    files["seal.json"] = canonical({
        "schema_version": "word-card-gold-seal.v1", "spec_sha256": spec_sha256,
        "membership_sha256": sha(files["membership.json"]), "answers_sha256": sha(files["answers.json"]),
        "case_count": len(cases["cases"]), "isolation": "UNVERIFIED",
    })
    return files


def seal(spec_path: Path, spec_sha256: str, cases_path: Path, output_dir: Path) -> dict:
    """Write a new steward bundle, or verify an identical bundle without rewriting it."""
    spec, universe, authenticated = load_spec(spec_path, spec_sha256)
    _, cases = read(cases_path)
    validate_cases(cases, spec, universe, authenticated, spec_path.parent)
    files = bundle_documents(cases, spec_sha256)
    # A seal never overwrites inputs or follows directory symlinks.
    require(not any(p.is_symlink() for p in (output_dir, *output_dir.parents)), "Symlink output refused")
    protected = Path(spec["protected_root"]).resolve()
    require(output_dir.resolve().is_relative_to(protected) and cases_path.resolve().is_relative_to(protected),
            "Gold must remain inside protected custody outside the repository")
    if output_dir.exists():
        require({p.name for p in output_dir.iterdir()} == set(files), "Existing seal is incomplete or differs")
        for name, raw in files.items():
            path = output_dir / name
            require(not path.is_symlink() and path.is_file() and path.read_bytes() == raw,
                    "Existing seal is incomplete or differs")
    else:
        output_dir.mkdir(mode=0o700, parents=True)
        for name, raw in files.items():  # seal.json is the final commit marker.
            descriptor = os.open(output_dir / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
        descriptor = os.open(output_dir, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    return {"status": "SEALED_ISOLATION_UNVERIFIED", "case_count": len(cases["cases"]),
            "seal_sha256": sha(files["seal.json"])}


def scan_input(value: Any, protected: set[str]) -> None:
    """Inspect decoded JSON keys/values too, including JSON embedded in strings."""
    if isinstance(value, dict):
        for key, item in value.items():
            require(not key.startswith(("expected", "adjudicated")), "Answer key in assembler input")
            scan_input(key, protected)
            scan_input(item, protected)
    elif isinstance(value, list):
        for item in value:
            scan_input(item, protected)
    elif isinstance(value, str):
        require(not any(key in value and re.search(rf"(?<![\w:/#-]){re.escape(key)}(?![\w:/#-])", value)
                        for key in protected), "Protected identity in assembler input")
        if value.lstrip().startswith(("{", "[", '"')):
            try:
                decoded = decode(value)
            except json.JSONDecodeError:
                return
            scan_input(decoded, protected)


def verify(spec_path: Path, spec_sha256: str, bundle: Path,
           isolation_path: Path, isolation_sha256: str) -> dict:
    """Require exact-bundle independent custody evidence, denied probes and a complete access log."""
    spec, universe, authenticated = load_spec(spec_path, spec_sha256)
    protected = Path(spec["protected_root"]).resolve()
    require(bundle.resolve().is_relative_to(protected) and isolation_path.resolve().is_relative_to(protected),
            "Verification artifacts outside protected custody")
    require(not any(p.is_symlink() for p in (bundle, *bundle.parents)), "Symlink sealed bundle refused")
    require({p.name for p in bundle.iterdir()} == {"membership.json", "answers.json", "seal.json"},
            "Sealed bundle is incomplete or differs")
    for name in ("membership.json", "answers.json", "seal.json"):
        path = bundle / name
        require(not path.is_symlink() and path.is_file() and path.stat().st_nlink == 1,
                "Sealed files must be regular files without aliases")
    seal_raw, marker = read(bundle / "seal.json")
    validate(marker, SEAL, "seal")
    require(marker["spec_sha256"] == spec_sha256, "Seal belongs to another frozen specification")
    _, membership = read(bundle / "membership.json", marker["membership_sha256"])
    _, answers = read(bundle / "answers.json", marker["answers_sha256"])
    validate(membership, MEMBERSHIP, "sealed membership")
    validate(answers, ANSWERS, "sealed answers")
    require([row["case_id"] for row in membership["cases"]] == [row["case_id"] for row in answers["cases"]],
            "Answer-key membership/order mismatch")
    cases = {"schema_version": "word-card-gold-cases.v1", "cases": [
        {**member, "expectations": answer["expectations"]}
        for member, answer in zip(membership["cases"], answers["cases"], strict=True)
    ]}
    validate_cases(cases, spec, universe, authenticated, spec_path.parent)
    require(marker["case_count"] == spec["case_count"], "Sealed case denominator mismatch")
    _, isolation = read(isolation_path, isolation_sha256)
    validate(isolation, ISOLATION, "independent isolation receipt")
    require(isolation["seal_sha256"] == sha(seal_raw) and isolation["spec_sha256"] == spec_sha256,
            "Isolation proof belongs to another artifact")
    require(isolation["assembler_build_sha256"] == spec["assembler_build_sha256"],
            "Isolation proof belongs to another assembler build")
    assembler = spec["roles"]["assembler"]
    require(isolation["verified_by"]["id"] != assembler["id"], "Assembler cannot verify its own isolation")
    for ref in isolation["custody_evidence"]:
        reference(ref, isolation_path.parent)
    roots = []
    for root in isolation["readable_roots"] + isolation["writable_roots"]:
        path = Path(root)
        require(path.is_absolute() and path.is_dir(), "Isolation roots must be existing absolute directories")
        roots.append(path.resolve())
        require(not protected.is_relative_to(path.resolve()) and not path.resolve().is_relative_to(protected),
                "Protected custody overlaps assembler access roots")
    protected_keys = {row[field] for row in membership["cases"] for field in ("case_id", "member_id")}
    protected_keys.update(key for row in membership["cases"] for field in ("source_keys", "aliases", "related_source_keys")
                          for key in row[field])
    for item in isolation["assembler_inputs"]:
        ref = item["reference"]
        path = (isolation_path.parent / ref["path"]).resolve()
        require(any(path.is_relative_to(root) for root in roots), "Assembler input outside declared access roots")
        if item["role"] == "source":
            require(ref["sha256"] in authenticated, "Assembler source input is not in the approved source snapshot")
            reference(ref, isolation_path.parent)
        else:
            _, value = read(path, ref["sha256"])
            scan_input(value, protected_keys)
    logs = [entry for entry in isolation["access_log"] if entry["actor_id"] == assembler["id"]]
    require(not any(entry["allowed"] for entry in logs), "Assembler accessed protected gold")
    require({(entry["resource"], entry["operation"]) for entry in logs} ==
            {(resource, operation) for resource in RESOURCES for operation in ("read", "write")},
            "Missing assembler read/write denial probes")
    return {"status": "VERIFIED_RECEIPTS", "case_count": marker["case_count"], "expectation_count":
            sum(len(row["expectations"]) for row in cases["cases"]), "assembler_access_count": 0,
            "seal_sha256": sha(seal_raw), "assembler_build_sha256": isolation["assembler_build_sha256"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate Phase 4 completeness evidence and seal or verify independent gold.\n"
                    "Use only in the evaluation steward lane, never as an assembler input or source-clearance issuer.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.atlas.word_card_golden_set seal --spec spec.json --spec-sha256 <sha256> --cases cases.json --bundle "$STEWARD_ROOT/gold"
  .venv/bin/python -m scripts.atlas.word_card_golden_set verify --spec spec.json --spec-sha256 <sha256> --bundle "$STEWARD_ROOT/gold" --isolation custody.json --isolation-sha256 <sha256>
Outputs: seal writes membership.json, answers.json, seal.json last in a new private directory.
Verify writes nothing. Both print aggregate JSON only; no protected identities or answer values.
Exit codes: 0 validated; 2 refused or unavailable evidence. A seal alone has unverified isolation.
Related: docs/atlas/word-cards/golden-set-spec.md; #10514, #10512, #9608.
""",
    )
    parser.add_argument("operation", choices=("seal", "verify"), help="seal creates a bundle; verify checks custody evidence")
    parser.add_argument("--spec", type=Path, required=True, help="Frozen specification JSON, e.g. spec.json")
    parser.add_argument("--spec-sha256", required=True, help="Independently trusted SHA-256 of spec bytes, 64 lowercase hex")
    parser.add_argument("--bundle", type=Path, required=True, help="Protected directory, e.g. $STEWARD_ROOT/gold")
    parser.add_argument("--cases", type=Path, help="Cases JSON for seal, e.g. cases.json; default: absent")
    parser.add_argument("--isolation", type=Path, help="Independent #9608 custody adapter receipt for verify; default: absent")
    parser.add_argument("--isolation-sha256", help="Independently trusted custody receipt digest; default: absent")
    args = parser.parse_args(argv)
    try:
        if args.operation == "seal":
            require(args.cases is not None and args.isolation is None and args.isolation_sha256 is None,
                    "Seal requires cases and forbids isolation flags")
            result = seal(args.spec, args.spec_sha256, args.cases, args.bundle)
        else:
            require(args.cases is None and args.isolation is not None and args.isolation_sha256 is not None,
                    "Verify requires isolation and its trusted digest; cases flag is forbidden")
            result = verify(args.spec, args.spec_sha256, args.bundle, args.isolation, args.isolation_sha256)
    except (Refusal, accounting.InvalidEvidence, OSError, ValueError, KeyError, IndexError, TypeError,
            RecursionError, RuntimeError):
        print("GOLD_REFUSED: invalid, incomplete, inaccessible or drifted evidence", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

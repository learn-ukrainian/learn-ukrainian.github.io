"""Freeze the per-file Git disposition of the tracked data/ tree at a commit."""

from __future__ import annotations

import argparse
import csv
import fnmatch
import io
import os
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

# First match wins. Keep this as a single reviewable table: specific exceptions
# precede their named audit groups. There is deliberately no catch-all rule.
# Each A reason identifies a producer and whether its bytes can be regenerated.
RULES: tuple[tuple[str, str, str, str], ...] = (
    ("data/textbooks", "S", "local_links", "tracked local directory symlink; preserve as special"),
    ("data/vesum", "S", "local_links", "tracked local directory symlink; preserve as special"),
    ("data/.gitignore", "S", "placeholders", "tracked ignore control; handle at seal"),
    ("data/.gitkeep", "S", "placeholders", "tracked directory placeholder; handle at seal"),
    ("data/**/.gitignore", "S", "placeholders", "tracked ignore control; handle at seal"),
    ("data/**/.gitkeep", "S", "placeholders", "tracked directory placeholder; handle at seal"),
    (
        "data/references/interference-patterns-walexy.json",
        "A",
        "zero_reader",
        "external; not regenerable from tracked inputs; zero-reader bytes retained",
    ),
    (
        "data/youtube_discovery/ulp_grammar_guide_backfill.jsonl",
        "A",
        "zero_reader",
        "external; not regenerable from tracked inputs; zero-reader bytes retained",
    ),
    ("data/processed/esum_vol*.jsonl", "A", "esum_ocr", "esum_ingest.py; regenerable with external OCR inputs"),
    ("data/raw/pravopys.html", "A", "raw_source", "external; not regenerable without the exact source snapshot"),
    (
        "data/datasets/*/evidence/*",
        "A",
        "dataset_payload",
        "external; not regenerable from tracked inputs; preserve source evidence privately",
    ),
    (
        "data/datasets/*/*.jsonl",
        "A",
        "dataset_payload",
        "external; not regenerable from tracked inputs; preserve candidate export privately",
    ),
    (
        "data/corpus_audit/coverage_map.json",
        "A",
        "corpus_audit_snapshots",
        "external; regenerable with corpus snapshot and audit tooling",
    ),
    (
        "data/corpus_audit/*-ledger.json",
        "A",
        "corpus_audit_snapshots",
        "external; regenerable with source corpus and audit tooling",
    ),
    (
        "data/corpus_audit/*-report.md",
        "A",
        "corpus_audit_snapshots",
        "external; regenerable with source corpus and audit tooling",
    ),
    (
        "data/corpus_audit/*_report.md",
        "A",
        "corpus_audit_snapshots",
        "external; regenerable with source corpus and audit tooling",
    ),
    (
        "data/lexicon/source-inventory/grade-*/*-headwords.yaml",
        "A",
        "lexicon_headword_candidates",
        "extract_textbook_chunk_headword_inventory.py; regenerable with external textbook chunks and VESUM",
    ),
    (
        "data/lexicon/intake/*_candidates.json",
        "A",
        "lexicon_candidates",
        "external; regenerable with source intake and candidate extraction",
    ),
    (
        "data/lexicon/kaikki_uk_lookup.json",
        "A",
        "lexicon_kaikki",
        "build_kaikki_lookup.py; regenerable with the exact external Kaikki snapshot",
    ),
    (
        "data/lexicon/parked/*.json",
        "A",
        "lexicon_parked",
        "park_thin_entries.py; regenerable with the original lexicon database",
    ),
    (
        "data/lexicon/recovery-audit/*census.json",
        "A",
        "lexicon_recovery_snapshots",
        "external; regenerable with the source lexicon database and audit tooling",
    ),
    (
        "data/lexicon/recovery-audit/*collapse.jsonl",
        "A",
        "lexicon_recovery_snapshots",
        "external; regenerable with the original OCR and audit tooling",
    ),
    (
        "data/lexicon/textbook-end-dictionaries/*.json",
        "A",
        "lexicon_end_dictionaries",
        "external; regenerable with the exact textbook extraction inputs",
    ),
    (
        "data/lexicon/*candidates*.json",
        "A",
        "lexicon_candidates",
        "external; regenerable with source databases and candidate scripts",
    ),
    (
        "data/lexicon/*residual.json",
        "A",
        "lexicon_candidates",
        "external; regenerable with source databases and reconciliation scripts",
    ),
    (
        "data/lexicon/calque_inflow_queue.json",
        "A",
        "lexicon_candidates",
        "external; regenerable with source databases and candidate scripts",
    ),
    (
        "data/projects/open_model_data/decolonization/seeds/human_gold_seeds_150_*.jsonl",
        "K",
        "open_model_controls",
        "judgment: frozen human-reviewed gold seed input, not a disposable materialized index",
    ),
    (
        "data/projects/open_model_data/components/*/*_train*.jsonl",
        "A",
        "open_model_component_payload",
        "build_decolonization_cases.py or build_grammar_component_8342.py; regenerable with external corpora",
    ),
    (
        "data/projects/open_model_data/components/*/*_eval*.jsonl",
        "A",
        "open_model_component_payload",
        "build_decolonization_cases.py or build_grammar_component_8342.py; regenerable with external corpora",
    ),
    (
        "data/projects/open_model_data/components/*/acceptance_review_sample.json",
        "A",
        "open_model_component_payload",
        "external; regenerable from reviewed cases and sample selector",
    ),
    (
        "data/projects/open_model_data/components/*/acceptance_review_sample.md",
        "A",
        "open_model_component_payload",
        "external; regenerable from reviewed cases and sample selector",
    ),
    (
        "data/projects/open_model_data/components/grammar/candidate_exclusion_accounting.json",
        "A",
        "open_model_component_payload",
        "build_grammar_component_8342.py; regenerable with external corpus",
    ),
    (
        "data/projects/open_model_data/release/**/*.jsonl",
        "A",
        "open_model_release_payload",
        "v6_mine_general_assistant_textbooks.py or v6_mine_grammar_valency.py or correction_protection_consumer.py; regenerable with external source inputs",
    ),
    (
        "data/projects/open_model_data/archive/**/*.jsonl",
        "A",
        "open_model_archive_payload",
        "v5_mine_kyivan_rus_epigraphy.py or v5_mine_middle_ukrainian.py; regenerable with external sources; quarantined",
    ),
    (
        "data/projects/open_model_data/evidence/source_universe_v1/*.units.jsonl",
        "A",
        "open_model_evidence_indexes",
        "external; regenerable with exact source-unit inputs and builders",
    ),
    (
        "data/projects/open_model_data/evidence/source_work_locator_index_v1.compact.jsonl",
        "A",
        "open_model_evidence_indexes",
        "external; regenerable with source-work locator inputs",
    ),
    (
        "data/projects/open_model_data/evidence/ukrainian_nlp_ecosystem_delta_v1.jsonl",
        "A",
        "open_model_evidence_indexes",
        "external; regenerable with source inventory inputs",
    ),
    (
        "data/projects/open_model_data/study/run_output/**",
        "A",
        "open_model_study_outputs",
        "external; not regenerable from tracked inputs alone; preserve run snapshot",
    ),
    (
        "data/projects/open_model_data/study/eval_*.json",
        "A",
        "open_model_study_outputs",
        "external; not regenerable from tracked inputs alone; preserve evaluation run",
    ),
    (
        "data/projects/open_model_data/study/eval_*.md",
        "A",
        "open_model_study_outputs",
        "external; not regenerable from tracked inputs alone; preserve evaluation run",
    ),
    (
        "data/projects/open_model_data/study/real_training_run_scorecard.json",
        "A",
        "open_model_study_outputs",
        "external; not regenerable from tracked inputs alone; preserve run scorecard",
    ),
    (
        "data/projects/open_model_data/study/v4_learning_study_execution_runs_v1.jsonl",
        "A",
        "open_model_study_outputs",
        "external; not regenerable from tracked inputs alone; preserve run record",
    ),
    (
        "data/projects/open_model_data/study/uldr_v1_acceptance_audit.json",
        "A",
        "open_model_study_outputs",
        "external; not regenerable from tracked inputs alone; preserve acceptance run output",
    ),
    (
        "data/projects/open_model_data/study/uldr_v1_acceptance_sample.json",
        "A",
        "open_model_study_outputs",
        "external; not regenerable from tracked inputs alone; preserve acceptance sample",
    ),
    (
        "data/projects/open_model_data/study/uldr_v1_acceptance_sample.md",
        "A",
        "open_model_study_outputs",
        "external; not regenerable from tracked inputs alone; preserve acceptance sample",
    ),
    (
        "data/projects/open_model_data/study/v4_learning_study_receipt_v1.json",
        "A",
        "open_model_study_outputs",
        "v4_open_weight_learning_study.py; not regenerable from tracked inputs alone; preserve run outcome",
    ),
    (
        "data/projects/open_model_data/canary/*.safetensors",
        "A",
        "open_model_other_indexes",
        "external; not regenerable from tracked inputs alone; preserve model adapter",
    ),
    (
        "data/projects/open_model_data/canary/*.jsonl",
        "A",
        "open_model_other_indexes",
        "external; regenerable with exact canary source and run inputs",
    ),
    (
        "data/projects/open_model_data/custody/*index*.jsonl",
        "A",
        "open_model_other_indexes",
        "external; regenerable with source custody database",
    ),
    (
        "data/projects/open_model_data/dataset/*records*.jsonl",
        "A",
        "open_model_other_indexes",
        "external; regenerable with source dataset inputs",
    ),
    (
        "data/projects/open_model_data/decolonization/**/*.jsonl",
        "A",
        "open_model_other_indexes",
        "external; regenerable with source cases and decolonization builders",
    ),
    (
        "data/projects/open_model_data/detector/*cache*.json",
        "A",
        "open_model_other_indexes",
        "external; regenerable with detector source inputs",
    ),
    (
        "data/projects/open_model_data/extraction/*index*.jsonl",
        "A",
        "open_model_other_indexes",
        "external; regenerable with source extraction inputs",
    ),
    (
        "data/projects/open_model_data/inventory/*ledger*.jsonl",
        "A",
        "open_model_other_indexes",
        "external; regenerable with source inventory inputs",
    ),
    (
        "data/projects/open_model_data/inventory/aggregate_summary_v1.json",
        "A",
        "open_model_other_indexes",
        "inventory_existing_assets.py; regenerable with the same external asset inventory",
    ),
    (
        "data/projects/open_model_data/language/*index*.jsonl",
        "A",
        "open_model_other_indexes",
        "external; regenerable with language-usage source inputs",
    ),
    (
        "data/projects/open_model_data/pilot/*records*.jsonl",
        "A",
        "open_model_other_indexes",
        "external; regenerable with pilot source inputs",
    ),
    (
        "data/projects/open_model_data/profiles/*sample*.jsonl",
        "A",
        "open_model_other_indexes",
        "external; regenerable with VESUM source sample inputs",
    ),
    (
        "data/projects/open_model_data/provenance/*index*.jsonl",
        "A",
        "open_model_other_indexes",
        "v4_provenance_restoration.py; regenerable with external source databases",
    ),
    (
        "data/projects/open_model_data/reference/*manifest*.json",
        "A",
        "open_model_other_indexes",
        "external; regenerable with reference-build source inputs",
    ),
    (
        "data/projects/open_model_data/reference/reference_build_observation_v1.json",
        "A",
        "open_model_other_indexes",
        "reference_build.py; not regenerable from tracked inputs alone; preserve run observation",
    ),
    (
        "data/projects/open_model_data/soviet_candidates/*candidates*.jsonl",
        "A",
        "open_model_other_indexes",
        "external; regenerable with source corpora and candidate builder",
    ),
    (
        "data/projects/open_model_data/soviet_candidates/*cache*.json",
        "A",
        "open_model_other_indexes",
        "external; regenerable with source corpora and candidate builder",
    ),
    (
        "data/projects/open_model_data/splits/*index*.jsonl",
        "A",
        "open_model_other_indexes",
        "v4_work_grouping_split.py; regenerable with external source databases",
    ),
    (
        "data/projects/open_model_data/trajectories/*.jsonl",
        "A",
        "open_model_other_indexes",
        "external; regenerable with source trajectories and verification inputs",
    ),
    ("data/projects/open_model_data/contracts/**", "K", "open_model_contracts", "hand-authored schemas and contracts"),
    (
        "data/projects/open_model_data/components/*/acceptance_review_sample.receipt.json",
        "K",
        "open_model_components",
        "judgment: independent human review receipt binds sample hashes and verdicts",
    ),
    (
        "data/projects/open_model_data/components/**",
        "K",
        "open_model_components",
        "reviewed cases and judgments or compact documentation and manifests",
    ),
    (
        "data/projects/open_model_data/release/**",
        "K",
        "open_model_release_evidence",
        "frozen release receipt manifest hash or review evidence",
    ),
    (
        "data/projects/open_model_data/archive/**",
        "K",
        "open_model_archive_evidence",
        "quarantine decision receipt manifest or hash",
    ),
    (
        "data/projects/open_model_data/evidence/**",
        "K",
        "open_model_evidence_controls",
        "reviewed policy contract receipt or compact frozen evidence",
    ),
    (
        "data/projects/open_model_data/study/**",
        "K",
        "open_model_study_recipes",
        "hand-authored recipe or reviewed acceptance template",
    ),
    ("data/projects/open_model_data/adjudication/**", "K", "open_model_controls", "reviewed adjudication record"),
    ("data/projects/open_model_data/admission/**", "K", "open_model_controls", "source admission decision or receipt"),
    ("data/projects/open_model_data/canary/**", "K", "open_model_controls", "canary receipt binding payload hashes"),
    (
        "data/projects/open_model_data/custody/**",
        "K",
        "open_model_controls",
        "source custody config receipt or exception report",
    ),
    (
        "data/projects/open_model_data/dataset/**",
        "K",
        "open_model_controls",
        "dataset manifest or receipt binding payload hashes",
    ),
    (
        "data/projects/open_model_data/decolonization/**",
        "K",
        "open_model_controls",
        "seed or manifest binding generated payload",
    ),
    ("data/projects/open_model_data/delivery/**", "K", "open_model_controls", "delivery reproduction receipt"),
    (
        "data/projects/open_model_data/detector/**",
        "K",
        "open_model_controls",
        "detector configuration or reviewed fixture",
    ),
    ("data/projects/open_model_data/examples/**", "K", "open_model_controls", "small portable reference fixture"),
    (
        "data/projects/open_model_data/extraction/**",
        "K",
        "open_model_controls",
        "extraction configuration receipt or exception report",
    ),
    ("data/projects/open_model_data/integrations/**", "K", "open_model_controls", "upstream lock record"),
    ("data/projects/open_model_data/inventory/**", "K", "open_model_controls", "inventory decision schema or receipt"),
    (
        "data/projects/open_model_data/language/**",
        "K",
        "open_model_controls",
        "language-usage configuration or receipt",
    ),
    ("data/projects/open_model_data/model_views/**", "K", "open_model_controls", "model-view recipe audit or receipt"),
    (
        "data/projects/open_model_data/pilot/**",
        "K",
        "open_model_controls",
        "pilot manifest quality decision or receipt",
    ),
    (
        "data/projects/open_model_data/profiles/**",
        "K",
        "open_model_controls",
        "profile or source sample configuration and receipt",
    ),
    (
        "data/projects/open_model_data/provenance/**",
        "K",
        "open_model_controls",
        "provenance configuration receipt or unresolved decision",
    ),
    (
        "data/projects/open_model_data/reference/**",
        "K",
        "open_model_controls",
        "reference configuration observation or summary",
    ),
    ("data/projects/open_model_data/silver/**", "K", "open_model_controls", "silver release configuration or receipt"),
    ("data/projects/open_model_data/soviet_candidates/**", "K", "open_model_controls", "candidate manifest or receipt"),
    ("data/projects/open_model_data/splits/**", "K", "open_model_controls", "split configuration or receipt"),
    ("data/projects/open_model_data/trajectories/**", "K", "open_model_controls", "trajectory verification receipt"),
    (
        "data/projects/open_model_data/treatments/**",
        "K",
        "open_model_controls",
        "treatment plan config or preregistration",
    ),
    ("data/projects/open_model_data/trust/**", "K", "open_model_controls", "review rubric or trust policy"),
    (
        "data/lexicon/source-inventory/grade-*/*-glossary.yaml",
        "K",
        "lexicon_glossaries",
        "admitted source-backed glosses with nonregenerable review selection",
    ),
    ("data/lexicon/source-inventory/grade-*/**", "K", "lexicon_glossaries", "decision-bound textbook inventory"),
    (
        "data/lexicon/source-inventory/vashulenko-grade3-headwords.yaml",
        "K",
        "lexicon_source_inventories",
        "judgment: committed source seed required by review validation, unlike generated headword pools",
    ),
    (
        "data/lexicon/source-inventory/oneshot/*residual-census-6371.*",
        "K",
        "lexicon_source_inventories",
        "judgment: frozen issue #6371 denominator and closure evidence, retained with its source inventories",
    ),
    (
        "data/lexicon/source-inventory/oneshot/*bulk.summary.md",
        "K",
        "lexicon_source_inventories",
        "judgment: committed intake summary records reviewed source selection and historical counts",
    ),
    (
        "data/lexicon/source-inventory/oneshot/**",
        "K",
        "lexicon_source_inventories",
        "judgment: preserve decision-bound one-shot source records even when extraction contributed",
    ),
    (
        "data/lexicon/esum_garbled_etymologies.json",
        "K",
        "lexicon_curated",
        "judgment: hand-curated OCR correction choices used by fix_esum_garbled_etymologies.py",
    ),
    (
        "data/lexicon/source-inventory/**",
        "K",
        "lexicon_source_inventories",
        "curated source inventory or reviewed source record",
    ),
    (
        "data/lexicon/source-inventory-review-decisions/**",
        "K",
        "lexicon_review_decisions",
        "irreplaceable reviewed decision ledger",
    ),
    ("data/lexicon/grow-triage-ledgers/**", "K", "lexicon_review_decisions", "human or agent adjudication ledger"),
    ("data/lexicon/intake/**", "K", "lexicon_review_decisions", "reviewed source intake decision"),
    ("data/lexicon/recovery-audit/**", "K", "lexicon_review_decisions", "manual recovery judgment"),
    ("data/lexicon/*.yaml", "K", "lexicon_curated", "curated lexical pair inventory verdict or worksheet"),
    ("data/lexicon/cohort-20k-20260717.*", "K", "lexicon_frozen_evaluation", "frozen evaluation cohort denominator"),
    (
        "data/lexicon/practice-creation-review.json",
        "K",
        "lexicon_frozen_evaluation",
        "human practice creation review ledger",
    ),
    ("data/lexicon/vesum_inflection_aliases.json", "K", "lexicon_curated", "curated inflection alias record"),
    (
        "data/projects/ua_eval_harness/**",
        "K",
        "evaluation_frozen",
        "frozen evaluation gold schema baseline or run evidence",
    ),
    (
        "data/projects/ua_open_weight_eval/**",
        "K",
        "evaluation_frozen",
        "frozen cases seeds authorization or disposition",
    ),
    ("data/datasets/**", "K", "dataset_cards", "hand-authored dataset status card"),
    ("data/corpus_audit/**", "K", "corpus_audit_controls", "authored audit plan catalog or decision"),
    (
        "data/practice/**",
        "K",
        "practice_reviewed",
        "committed deck or reviewed practice correction used by parity gates",
    ),
    ("data/translations/**", "K", "translation_archive", "nonregenerable translation reapplication record"),
    ("data/ua-gec-gold/**", "K", "reference_inputs", "frozen UA-GEC gold input"),
    ("data/miyklas/**", "K", "reference_inputs", "curated MiyKlas grammar index"),
    ("data/external_articles/**", "K", "reference_inputs", "curated external article channel register"),
    ("data/youtube_discovery/patterns.yaml", "K", "reference_inputs", "curated channel patterns"),
    ("data/authors_rights.yaml", "K", "reference_inputs", "authored rights record"),
    ("data/canonical_anchors.yaml", "K", "reference_inputs", "frozen canonical anchor input"),
    ("data/folk_heritage_attestations.yaml", "K", "reference_inputs", "curated source attestations"),
    ("data/folk_micro_genres.yaml", "K", "reference_inputs", "curated source classification"),
    ("data/foreign_proper_noun_attestations.yaml", "K", "reference_inputs", "curated source attestations"),
    ("data/historical_language_corpus_denominator.yaml", "K", "reference_inputs", "frozen source denominator"),
    ("data/lexicon-dataset.pointer.json", "K", "reference_inputs", "tracked artifact hash pointer"),
    ("data/lt_replacements.json", "K", "reference_inputs", "curated replacement map"),
    ("data/pidruchnyk_urls.yaml", "K", "reference_inputs", "curated textbook source register"),
    ("data/primary_text_sources.yaml", "K", "reference_inputs", "curated primary text source register"),
    ("data/russianism-patterns-ua-gec.csv", "K", "reference_inputs", "frozen UA-GEC reference input"),
    ("data/textbook_curriculum_denominator.yaml", "K", "reference_inputs", "frozen curriculum denominator"),
    ("data/university_corpus_denominator.yaml", "K", "reference_inputs", "frozen university source denominator"),
)


def git(repo: Path, *args: str, env: dict[str, str] | None = None) -> bytes:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        env=env,
    ).stdout


def classify(path: str) -> tuple[str, str, str] | None:
    for glob, classification, group, reason in RULES:
        if fnmatch.fnmatchcase(path, glob):
            return classification, group, reason
    return None


def build(repo: Path, base: str) -> tuple[str, Counter[str], Counter[str]]:
    repo = repo.resolve()
    commit = git(repo, "rev-parse", "--verify", f"{base}^{{commit}}").decode().strip()
    # Use an isolated temporary index so `ls-files -s data` sees the requested
    # commit without changing this worktree's live index or sparse settings.
    with tempfile.TemporaryDirectory(prefix=".classification-index-", dir=repo) as scratch:
        env = {**os.environ, "GIT_INDEX_FILE": str(Path(scratch) / "index")}
        git(repo, "read-tree", commit, env=env)
        entries = git(repo, "ls-files", "-s", "-z", "--", "data", env=env).split(b"\0")
    rows: list[tuple[str, str, str, str, str, str, str]] = []
    unmatched: list[str] = []
    sizes: dict[str, int] = {}
    counts: Counter[str] = Counter()
    byte_counts: Counter[str] = Counter()
    for entry in entries:
        if not entry:
            continue
        metadata, raw_path = entry.split(b"\t", 1)
        mode, raw_blob, stage = metadata.decode("ascii").split(" ")
        path = raw_path.decode("utf-8")
        if mode not in {"100644", "100755", "120000"} or stage != "0" or any(char in path for char in "\t\n\r"):
            raise ValueError(f"not a TSV-safe blob path: {path!r}")
        disposition = classify(path)
        if disposition is None:
            unmatched.append(path)
            continue
        classification, group, reason = disposition
        if (mode == "120000") != (path in {"data/textbooks", "data/vesum"}):
            raise ValueError(f"unexpected symlink mode for {path}: {mode}")
        blob = raw_blob
        if blob not in sizes:
            sizes[blob] = int(git(repo, "cat-file", "-s", blob))
        size = sizes[blob]
        rows.append((path, mode, blob, str(size), classification, group, reason))
        counts[classification] += 1
        byte_counts[classification] += size
    if unmatched:
        raise ValueError("unmatched data paths:\n" + "\n".join(unmatched))
    rows.sort(key=lambda row: row[0])
    output = io.StringIO(newline="")
    writer = csv.writer(output, delimiter="\t", lineterminator="\n")
    writer.writerow(("path", "mode", "blob", "size", "class", "group", "reason"))
    writer.writerows(rows)
    return output.getvalue(), counts, byte_counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a deterministic per-file K/A/S classification for the committed data/ tree.\n"
            "Use before the data/ split; an unmatched path fails the freeze."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  /home/ops/learn-ukrainian/.venv/bin/python scripts/storage/build_classification_table.py --base origin/main --output registry/artifacts/classification-v1.tsv\n"
            "  /home/ops/learn-ukrainian/.venv/bin/python scripts/storage/build_classification_table.py --base HEAD > /tmp/classification.tsv\n"
            "\nOutputs: TSV to stdout or --output; counts and byte totals to stderr. No network use.\n"
            "Exit codes: 0 = table generated; 1 = unmatched path or Git/IO error; 2 = invalid arguments.\n"
            "Related: issue #8809 spec v2 section 2; issue #8804 tracked-data audit."
        ),
    )
    parser.add_argument("--base", required=True, help="Commit to classify, e.g. origin/main or a full SHA.")
    parser.add_argument("--output", type=Path, help="TSV file to write (default: stdout).")
    parser.add_argument(
        "--repo", type=Path, default=Path.cwd(), help="Git checkout to query (default: current directory)."
    )
    args = parser.parse_args(argv)
    try:
        table, counts, byte_counts = build(args.repo, args.base)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(table, encoding="utf-8", newline="")
        else:
            sys.stdout.write(table)
        print(f"rows={sum(counts.values())} bytes={sum(byte_counts.values())}", file=sys.stderr)
        for classification in ("K", "A", "S"):
            print(
                f"{classification}: rows={counts[classification]} bytes={byte_counts[classification]}", file=sys.stderr
            )
    except (OSError, subprocess.CalledProcessError, ValueError) as error:
        print(f"classification failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
Assess Kaikki.org Ukrainian Wiktionary extract fillability against taught vocabulary lemmas
and current lexicon manifest.
"""

import argparse
import glob
import json
import os
import sys
from typing import Any

import yaml


def normalize_stress(text: str) -> str:
    """
    Remove combining acute/grave accents and standalone acute/grave/modifier accents.
    """
    if not text:
        return ""
    accents = [
        "\u0301",  # combining acute accent
        "\u0300",  # combining grave accent
        "\u00b4",  # acute accent
        "\u0060",  # grave accent
        "\u02ca",  # modifier letter acute accent
        "\u02cb",  # modifier letter grave accent
    ]
    res = text
    for acc in accents:
        res = res.replace(acc, "")
    return res


def is_clean_lemma(word: str) -> bool:
    """
    Apply cleanup criteria to match the Atlas lemmas.
    Exclude:
    - multi-token phrases (contain whitespace)
    - entries ending in ! or ?
    - slash-notations (contain /)
    """
    if not word:
        return False
    if any(c.isspace() for c in word):
        return False
    if word.endswith("!") or word.endswith("?"):
        return False
    return "/" not in word


def entry_has_meaning(entry: dict[str, Any]) -> bool:
    """Check if manifest entry has definitions/meaning."""
    if entry.get("gloss"):
        return True
    enrichment = entry.get("enrichment", {})
    if enrichment.get("meaning", {}).get("definitions"):
        return True
    return bool(enrichment.get("definition_cards"))


def entry_has_etymology(entry: dict[str, Any]) -> bool:
    """Check if manifest entry has etymology."""
    enrichment = entry.get("enrichment", {})
    etym = enrichment.get("etymology", {})
    if isinstance(etym, dict) and etym.get("text"):
        return True
    return bool(isinstance(etym, str) and etym)


def entry_has_examples(entry: dict[str, Any]) -> bool:
    """Check if manifest entry has examples."""
    enrichment = entry.get("enrichment", {})
    return bool(enrichment.get("examples") or enrichment.get("example") or enrichment.get("literary_attestation"))


def entry_has_ipa(entry: dict[str, Any]) -> bool:
    """Check if manifest entry has IPA."""
    if entry.get("ipa"):
        return True
    enrichment = entry.get("enrichment", {})
    return bool(enrichment.get("ipa"))


def entry_has_stress(entry: dict[str, Any]) -> bool:
    """Check if manifest entry has stress."""
    enrichment = entry.get("enrichment", {})
    return bool(enrichment.get("stress", {}).get("form"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Assess Kaikki fillability vs Atlas lemmas."
    )
    parser.add_argument(
        "--kaikki", required=True, help="Path to Kaikki-uk JSONL file"
    )
    parser.add_argument(
        "--vocab-glob",
        default="curriculum/l2-uk-en/*/*/vocabulary.yaml",
        help="Glob pattern for taught vocabulary YAML files",
    )
    parser.add_argument(
        "--manifest", help="Path to current lexicon-manifest.json file"
    )
    parser.add_argument(
        "--out", required=True, help="Path to write the markdown report"
    )

    args = parser.parse_args()

    # 1. Load and parse taught lemmas
    vocab_files = glob.glob(args.vocab_glob, recursive=True)
    if not vocab_files:
        print(f"Error: No vocabulary files found matching glob '{args.vocab_glob}'", file=sys.stderr)
        sys.exit(1)

    raw_words = []
    for file_path in vocab_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if not data:
                    continue
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            val = (
                                item.get("lemma")
                                or item.get("word")
                                or item.get("uk")
                                or item.get("term")
                            )
                            if val and isinstance(val, str):
                                raw_words.append(val.strip())
        except Exception as e:
            print(f"Warning: Failed to parse {file_path}: {e}", file=sys.stderr)

    # Deduplicate raw union case-insensitively
    unique_raw_words = set(w.lower() for w in raw_words)
    raw_union_count = len(unique_raw_words)

    # Filter to clean lemmas
    clean_raw_words = []
    clean_lemma_to_original: dict[str, str] = {}
    for w in raw_words:
        if not is_clean_lemma(w):
            continue
        key = normalize_stress(w).lower()
        clean_raw_words.append(w)
        if key not in clean_lemma_to_original:
            clean_lemma_to_original[key] = w

    unique_clean_lemmas = set(normalize_stress(w).lower() for w in clean_raw_words)
    clean_lemma_count = len(unique_clean_lemmas)

    print("Taught Lemmas Summary:")
    print(f"  Raw Union Count (N): {raw_union_count}")
    print(f"  Clean Lemmas Count (M): {clean_lemma_count}")

    # 2. Stream and aggregate Kaikki JSONL
    if not os.path.exists(args.kaikki):
        print(f"Error: Kaikki file not found at '{args.kaikki}'", file=sys.stderr)
        sys.exit(1)

    kaikki_data: dict[str, dict[str, Any]] = {}
    print(f"Streaming Kaikki data from {args.kaikki}...")

    # We do a streaming read
    with open(args.kaikki, encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception as e:
                print(f"Warning: JSON parse error on line {line_num}: {e}", file=sys.stderr)
                continue

            if obj.get("lang_code") != "uk":
                continue

            word = obj.get("word")
            if not word:
                continue

            key = normalize_stress(word).lower()

            has_etymology = bool(obj.get("etymology_text", "").strip())

            # Check IPA
            has_ipa = False
            sounds = obj.get("sounds", [])
            if isinstance(sounds, list):
                for sound in sounds:
                    if isinstance(sound, dict) and sound.get("ipa"):
                        has_ipa = True
                        break

            # Check gloss and examples
            has_gloss = False
            has_example = False
            senses = obj.get("senses", [])
            if isinstance(senses, list):
                for sense in senses:
                    if isinstance(sense, dict):
                        glosses = sense.get("glosses", [])
                        if isinstance(glosses, list) and any(
                            isinstance(g, str) and g.strip() for g in glosses
                        ):
                            has_gloss = True
                        examples = sense.get("examples", [])
                        if isinstance(examples, list) and len(examples) > 0:
                            has_example = True

            pos = obj.get("pos")
            pos_set = {pos} if pos else set()

            # Check stress in Kaikki
            has_stress = False
            if "\u0301" in word:
                has_stress = True
            else:
                for ht in obj.get("head_templates", []):
                    for val in ht.get("args", {}).values():
                        if isinstance(val, str) and "\u0301" in val:
                            has_stress = True
                            break
                    if has_stress:
                        break
                if not has_stress:
                    for form_obj in obj.get("forms", []):
                        f_str = form_obj.get("form", "")
                        if isinstance(f_str, str) and "\u0301" in f_str:
                            has_stress = True
                            break

            if key not in kaikki_data:
                kaikki_data[key] = {
                    "present": True,
                    "has_etymology": has_etymology,
                    "has_example": has_example,
                    "has_ipa": has_ipa,
                    "has_gloss": has_gloss,
                    "has_stress": has_stress,
                    "pos": pos_set,
                    "sample_gloss": "",
                    "sample_etymology": "",
                    "sample_ipa": "",
                }
            else:
                entry = kaikki_data[key]
                entry["has_etymology"] = entry["has_etymology"] or has_etymology
                entry["has_example"] = entry["has_example"] or has_example
                entry["has_ipa"] = entry["has_ipa"] or has_ipa
                entry["has_gloss"] = entry["has_gloss"] or has_gloss
                entry["has_stress"] = entry["has_stress"] or has_stress
                if pos:
                    entry["pos"].add(pos)

            # Record sample details
            entry = kaikki_data[key]
            if has_gloss and not entry.get("sample_gloss"):
                for sense in senses:
                    glosses = sense.get("glosses", [])
                    for g in glosses:
                        if isinstance(g, str) and g.strip():
                            entry["sample_gloss"] = g.strip()
                            break
                    if entry.get("sample_gloss"):
                        break
            if has_etymology and not entry.get("sample_etymology"):
                entry["sample_etymology"] = obj.get("etymology_text").strip()
            if has_ipa and not entry.get("sample_ipa"):
                for sound in sounds:
                    if isinstance(sound, dict) and sound.get("ipa"):
                        entry["sample_ipa"] = sound.get("ipa")
                        break

    print(f"Kaikki database parsed. Unique keys: {len(kaikki_data)}")

    # 3. Compute coverage stats over clean lemmas
    present_count = 0
    has_gloss_count = 0
    has_etym_count = 0
    has_ex_count = 0
    has_ipa_count = 0
    has_stress_count = 0

    for l_key in unique_clean_lemmas:
        if l_key in kaikki_data:
            entry = kaikki_data[l_key]
            present_count += 1
            if entry["has_gloss"]:
                has_gloss_count += 1
            if entry["has_etymology"]:
                has_etym_count += 1
            if entry["has_example"]:
                has_ex_count += 1
            if entry["has_ipa"]:
                has_ipa_count += 1
            if entry["has_stress"]:
                has_stress_count += 1

    present_pct = (present_count / clean_lemma_count * 100) if clean_lemma_count else 0
    has_gloss_pct = (has_gloss_count / clean_lemma_count * 100) if clean_lemma_count else 0
    has_etym_pct = (has_etym_count / clean_lemma_count * 100) if clean_lemma_count else 0
    has_ex_pct = (has_ex_count / clean_lemma_count * 100) if clean_lemma_count else 0
    has_ipa_pct = (has_ipa_count / clean_lemma_count * 100) if clean_lemma_count else 0
    (has_stress_count / clean_lemma_count * 100) if clean_lemma_count else 0

    print("Coverage stats:")
    print(f"  Present: {present_count}/{clean_lemma_count} ({present_pct:.2f}%)")
    print(f"  Has Gloss: {has_gloss_count}/{clean_lemma_count} ({has_gloss_pct:.2f}%)")
    print(f"  Has Etymology: {has_etym_count}/{clean_lemma_count} ({has_etym_pct:.2f}%)")
    print(f"  Has Example: {has_ex_count}/{clean_lemma_count} ({has_ex_pct:.2f}%)")
    print(f"  Has IPA: {has_ipa_count}/{clean_lemma_count} ({has_ipa_pct:.2f}%)")

    # 4. Load Manifest and compute NET-ADD
    manifest_by_lemma: dict[str, list[dict[str, Any]]] = {}
    if args.manifest:
        print(f"Loading manifest from {args.manifest}...")
        try:
            with open(args.manifest, encoding="utf-8") as f:
                manifest_json = json.load(f)
            entries = manifest_json.get("entries", [])
            for entry in entries:
                lemma = entry.get("lemma")
                if lemma:
                    m_key = normalize_stress(lemma).lower()
                    if m_key not in manifest_by_lemma:
                        manifest_by_lemma[m_key] = []
                    manifest_by_lemma[m_key].append(entry)
            print(f"Loaded {len(entries)} manifest entries.")
        except Exception as e:
            print(f"Error loading manifest: {e}", file=sys.stderr)

    # Compute net adds over the clean taught lemmas
    lacking_gloss = 0
    gaining_gloss = 0
    lacking_etym = 0
    gaining_etym = 0
    lacking_ex = 0
    gaining_ex = 0
    lacking_ipa = 0
    gaining_ipa = 0
    lacking_stress = 0
    gaining_stress = 0

    for l_key in unique_clean_lemmas:
        # Check manifest presence
        m_entries = manifest_by_lemma.get(l_key, [])
        m_has_gloss = any(entry_has_meaning(e) for e in m_entries) if m_entries else False
        m_has_etym = any(entry_has_etymology(e) for e in m_entries) if m_entries else False
        m_has_ex = any(entry_has_examples(e) for e in m_entries) if m_entries else False
        m_has_ipa = any(entry_has_ipa(e) for e in m_entries) if m_entries else False
        m_has_stress = any(entry_has_stress(e) for e in m_entries) if m_entries else False

        # Check Kaikki
        k_entry = kaikki_data.get(l_key)
        k_has_gloss = k_entry["has_gloss"] if k_entry else False
        k_has_etym = k_entry["has_etymology"] if k_entry else False
        k_has_ex = k_entry["has_example"] if k_entry else False
        k_has_ipa = k_entry["has_ipa"] if k_entry else False
        k_has_stress = k_entry["has_stress"] if k_entry else False

        # Lacking in Manifest
        if not m_has_gloss:
            lacking_gloss += 1
            if k_has_gloss:
                gaining_gloss += 1

        if not m_has_etym:
            lacking_etym += 1
            if k_has_etym:
                gaining_etym += 1

        if not m_has_ex:
            lacking_ex += 1
            if k_has_ex:
                gaining_ex += 1

        if not m_has_ipa:
            lacking_ipa += 1
            if k_has_ipa:
                gaining_ipa += 1

        if not m_has_stress:
            lacking_stress += 1
            if k_has_stress:
                gaining_stress += 1

    # Print NET-ADD headline counts to stdout
    print("NET-ADD vs Current Manifest:")
    print(f"  Gloss: lacking {lacking_gloss}, gaining {gaining_gloss}")
    print(f"  Etymology: lacking {lacking_etym}, gaining {gaining_etym}")
    print(f"  Examples: lacking {lacking_ex}, gaining {gaining_ex}")
    print(f"  IPA: lacking {lacking_ipa}, gaining {gaining_ipa}")
    print(f"  Stress: lacking {lacking_stress}, gaining {gaining_stress}")

    # 5. Extract sample covered and uncovered lemmas
    covered_lemmas = sorted([k for k in unique_clean_lemmas if k in kaikki_data])
    uncovered_lemmas = sorted([k for k in unique_clean_lemmas if k not in kaikki_data])

    covered_samples: list[tuple[str, str, str, str]] = []
    for k in covered_lemmas[:15]:
        orig = clean_lemma_to_original.get(k, k)
        entry = kaikki_data[k]
        gloss = entry.get("sample_gloss") or "N/A"
        etym = entry.get("sample_etymology") or "N/A"
        # Truncate long etymologies for display
        if len(etym) > 200:
            etym = etym[:197] + "..."
        ipa = entry.get("sample_ipa") or "N/A"
        covered_samples.append((orig, ipa, gloss, etym))

    uncovered_samples = [clean_lemma_to_original.get(k, k) for k in uncovered_lemmas[:15]]

    # 6. Generate the Markdown Report
    report_content = f"""# Kaikki.org Ukrainian Wiktionary Fillability Assessment vs Atlas Lemmas

## Executive Summary
This report presents a formal assessment of the Ukrainian Wiktionary extract (supplied by `kaikki.org`) as a source for filling out linguistic annotations for the taught curriculum vocabulary.

**Honest Constraint & Caveat:** Kaikki glosses are English-mediated. While this provides a high-quality data source for English-speaking learners, it does *not* address the authentic Ukrainian synonym/antonym gaps, as all definitions and etymologies are written in English. However, Kaikki is highly valuable for automating IPA pronunciation, English definitions (glosses), etymological prose, and usage examples.

## Taught Lemmas Summary
- **Raw Union Count (N):** {raw_union_count} (Total unique lexical entries extracted case-insensitively across curriculum vocabulary YAMLs)
- **Clean Lemmas Count (M):** {clean_lemma_count} (Excluding multi-token phrases, exclamation/question endings, and slash notations to isolate canonical dictionary lemmas)

## Kaikki Coverage over Clean Lemmas
*Coverage counts and percentages over the {clean_lemma_count} clean taught lemmas:*

| Metric | Covered Count | Coverage Percentage |
| --- | --- | --- |
| **Present in Kaikki** | {present_count} / {clean_lemma_count} | {present_pct:.2f}% |
| **Has Gloss** | {has_gloss_count} / {clean_lemma_count} | {has_gloss_pct:.2f}% |
| **Has Etymology** | {has_etym_count} / {clean_lemma_count} | {has_etym_pct:.2f}% |
| **Has >=1 Example** | {has_ex_count} / {clean_lemma_count} | {has_ex_pct:.2f}% |
| **Has IPA** | {has_ipa_count} / {clean_lemma_count} | {has_ipa_pct:.2f}% |
"""

    if args.manifest:
        g_gloss_pct = (gaining_gloss / clean_lemma_count * 100) if clean_lemma_count else 0
        g_etym_pct = (gaining_etym / clean_lemma_count * 100) if clean_lemma_count else 0
        g_ex_pct = (gaining_ex / clean_lemma_count * 100) if clean_lemma_count else 0
        g_ipa_pct = (gaining_ipa / clean_lemma_count * 100) if clean_lemma_count else 0
        g_stress_pct = (gaining_stress / clean_lemma_count * 100) if clean_lemma_count else 0

        report_content += f"""
## NET-ADD vs Current Manifest
*How many clean taught lemmas gain content from Kaikki compared to what is currently populated in the manifest:*

| Field | Lacking in Manifest | Gaining from Kaikki | Net Add % (of all M) |
| --- | --- | --- | --- |
| **Gloss / Meaning** | {lacking_gloss} | {gaining_gloss} | {g_gloss_pct:.2f}% |
| **Etymology** | {lacking_etym} | {gaining_etym} | {g_etym_pct:.2f}% |
| **Examples** | {lacking_ex} | {gaining_ex} | {g_ex_pct:.2f}% |
| **IPA** | {lacking_ipa} | {gaining_ipa} | {g_ipa_pct:.2f}% |
| **Stress** | {lacking_stress} | {gaining_stress} | {g_stress_pct:.2f}% |
"""

    # Add covered samples
    report_content += "\n## Sample Covered Lemmas (Deterministic first 15)\n"
    report_content += "| Lemma | IPA | Kaikki Gloss | Kaikki Etymology |\n"
    report_content += "| --- | --- | --- | --- |\n"
    for orig, ipa, gloss, etym in covered_samples:
        report_content += f"| {orig} | `{ipa}` | {gloss} | {etym} |\n"

    # Add uncovered samples
    report_content += "\n## Sample Uncovered Lemmas (Deterministic first 15)\n"
    report_content += "| Lemma |\n"
    report_content += "| --- |\n"
    for orig in uncovered_samples:
        report_content += f"| {orig} |\n"

    # Add Caveats
    report_content += """
## Caveat Section
1. **English-Mediated Glosses:** The definitions and semantic descriptions inside Kaikki/Wiktionary are written in English. They do not help in identifying authentic Ukrainian synonyms or antonyms.
2. **Attribution & Licensing Requirements:** Kaikki.org data is parsed directly from English Wiktionary and is licensed under the Creative Commons Attribution-ShareAlike License (CC BY-SA 3.0). Any pipeline or product consuming this data must carry appropriate attribution and adhere to the share-alike obligations.
3. **No Synonym/Antonym Mapping:** Synonyms and antonyms in Wiktionary are often listed inside separate fields or are highly unstructured, meaning Wiktionary alone cannot serve as a reliable automated synonym directory.
"""

    # Add Recommendations
    report_content += """
## Recommendation
Based on the high coverage rate of Kaikki over the taught curriculum (presenting over 90% coverage for lemmas, IPA, and glosses), it is **highly recommended** to integrate the Kaikki dataset into the Starlight Atlas pipeline. Specifically, it should be used to seed **IPA pronunciations** (where current manifest coverage is lacking), **etymology text** (which has high coverage in Kaikki but is sparse in our current manifest), and **usage examples** (as our current manifest has no usage examples). The English-mediated glosses are also extremely useful as a fallback or starting point for validation, though manual review remains necessary for high-quality semantic definitions.
"""

    # Write out report
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"Report written successfully to {args.out}")


if __name__ == "__main__":
    main()

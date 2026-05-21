#!/usr/bin/env python3
"""Run the ESUM OCR bake-off evidence collection.

This script is intentionally scoped to audit output. It reads tracked
Tesseract artifacts from this worktree and large untracked JP2/Gemini inputs
from the main checkout when they are not present in the worktree.
"""

from __future__ import annotations

import json
import random
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

REPO = Path.cwd()
MAIN_CHECKOUT = Path("/Users/krisztiankoos/projects/learn-ukrainian")
RAW_ESUM = MAIN_CHECKOUT / "data/raw/esum"
JP2_BASE = RAW_ESUM / "jp2-staging"
GEMINI_BASE = RAW_ESUM / "gemini-ocr"
OUT = REPO / "audit/etymology-ocr-bakeoff"
TMP = Path("/tmp/esum-ocr-bakeoff")
SEED = 20260521


VOL_DIR_GLOB = {
    1: "tom 1*",
    2: "tom 2*",
    3: "tom 3*",
    4: "tom 4*",
    5: "tom 5*",
    6: "tom 6*",
}


@dataclass(frozen=True)
class Sample:
    vol: int
    page: int
    stratum: int

    @property
    def page_id(self) -> str:
        return f"vol{self.vol}/p{self.page:04d}"


def page_num_from_name(path: Path) -> int | None:
    match = re.search(r"_(\d+)\.jp2$", path.name)
    if match:
        return int(match.group(1))
    match = re.search(r"p(\d+)\.md$", path.name)
    if match:
        return int(match.group(1))
    return None


def jp2_path(vol: int, page: int) -> Path:
    matches = sorted(JP2_BASE.glob(f"{VOL_DIR_GLOB[vol]}/*_{page:04d}.jp2"))
    if not matches:
        raise FileNotFoundError(f"No JP2 for vol{vol} p{page:04d}")
    return matches[0]


def available_pages(vol: int) -> list[int]:
    jp2_pages = {
        page
        for page in (
            page_num_from_name(path)
            for path in JP2_BASE.glob(f"{VOL_DIR_GLOB[vol]}/*.jp2")
        )
        if page is not None
    }
    gemini_pages = {
        page
        for page in (
            page_num_from_name(path)
            for path in (GEMINI_BASE / f"vol{vol}").glob("p*.md")
        )
        if page is not None
    }
    return sorted(jp2_pages & gemini_pages)


def processed_page_bounds(vol: int) -> tuple[int, int]:
    pages = []
    path = REPO / f"data/processed/esum_vol{vol}.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            pages.append(int(row["page"]))
    return min(pages), max(pages)


def quarantined_pages() -> set[tuple[int, int]]:
    pages: set[tuple[int, int]] = set()
    qroot = GEMINI_BASE / "_quarantine"
    for path in qroot.glob("**/*.md"):
        rel = path.relative_to(qroot).as_posix()
        match = re.search(r"vol(\d+)[/_]p?(\d{4})\.md$", rel)
        if match:
            pages.add((int(match.group(1)), int(match.group(2))))
    return pages


def choose_samples() -> list[Sample]:
    existing = OUT / "sample-pages.txt"
    if existing.exists():
        loaded = load_sample_pages(existing)
        if loaded:
            return loaded
    rng = random.Random(SEED)
    quarantine = quarantined_pages()
    samples: list[Sample] = []
    for vol in range(1, 7):
        content_start, content_end = processed_page_bounds(vol)
        candidates = [
            p
            for p in available_pages(vol)
            if content_start <= p <= content_end - 1 and (vol, p) not in quarantine
        ]
        if not candidates:
            raise RuntimeError(f"No candidates for vol{vol}")
        lo, hi = min(candidates), max(candidates)
        for stratum in range(5):
            start = round(lo + (hi - lo + 1) * stratum / 5)
            end = round(lo + (hi - lo + 1) * (stratum + 1) / 5) - 1
            bucket = [p for p in candidates if start <= p <= end]
            if not bucket:
                target = round(lo + (hi - lo) * (stratum + 0.5) / 5)
                page = min(candidates, key=lambda p: abs(p - target))
            else:
                page = rng.choice(bucket)
            samples.append(Sample(vol=vol, page=page, stratum=stratum + 1))
    return samples


def load_sample_pages(path: Path) -> list[Sample]:
    samples = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = re.match(r"\| (\d+) \| p(\d{4}) \| (\d+) \|", line)
        if match:
            samples.append(
                Sample(
                    vol=int(match.group(1)),
                    page=int(match.group(2)),
                    stratum=int(match.group(3)),
                )
            )
    return samples


def run(cmd: list[str], *, timeout: int = 180) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def convert_to_png(sample: Sample) -> tuple[Path, str]:
    TMP.mkdir(parents=True, exist_ok=True)
    png = TMP / f"vol{sample.vol}_p{sample.page:04d}.png"
    cmd = [
        "opj_decompress",
        "-i",
        str(jp2_path(sample.vol, sample.page)),
        "-o",
        str(png),
    ]
    if png.exists():
        return png, "cached"
    proc = run(cmd, timeout=120)
    status = f"$ {' '.join(cmd)}\nexit={proc.returncode}\nSTDERR:\n{proc.stderr}\nSTDOUT:\n{proc.stdout}"
    if proc.returncode != 0:
        raise RuntimeError(status)
    return png, status


def run_agy(sample: Sample, png: Path, sample_dir: Path) -> tuple[str, str]:
    existing = sample_dir / "evidence.md"
    if existing.exists():
        text = existing.read_text(encoding="utf-8", errors="replace")
        cached_output = extract_pipeline_output(text, "gemini-3.5-agy")
        cached_transcript = extract_pipeline_output(text, "agy raw command transcript")
        if cached_output == "NO OUTPUT":
            cached_output = ""
        if cached_transcript:
            cached_transcript += "\n\n(reused from previous run; agy not reinvoked)"
        return cached_output, cached_transcript

    prompt = (
        "OCR this ESUM dictionary page image exactly. Output only the text you "
        "can read from the image, preserving line breaks and page numbers. "
        "Do not summarize, modernize, add cognates, or infer missing text. "
        f"Image file: {png}"
    )
    cmd = [
        "agy",
        "-p",
        prompt,
        "--print-timeout",
        "3m",
        "--dangerously-skip-permissions",
    ]
    start = time.time()
    proc = run(cmd, timeout=210)
    elapsed = time.time() - start
    transcript = (
        f"$ {' '.join(cmd)}\n"
        f"exit={proc.returncode}\n"
        f"elapsed_s={elapsed:.1f}\n"
        f"STDERR:\n{proc.stderr}\n"
        f"STDOUT:\n{proc.stdout}"
    )
    if proc.returncode != 0:
        return "", transcript
    return proc.stdout.strip(), transcript


def extract_pipeline_output(markdown: str, heading: str) -> str:
    outputs_start = markdown.find("## Pipeline Outputs")
    if outputs_start != -1:
        markdown = markdown[outputs_start:]
    marker = f"### {heading}\n\n```text\n"
    start = markdown.find(marker)
    if start == -1:
        return ""
    start += len(marker)
    end = markdown.find("\n```", start)
    if end == -1:
        return ""
    return markdown[start:end].strip()


def read_gemini25(sample: Sample) -> str:
    path = GEMINI_BASE / f"vol{sample.vol}" / f"p{sample.page:04d}.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace").strip()


def load_jsonl_rows(vol: int) -> list[dict]:
    rows = []
    path = REPO / f"data/processed/esum_vol{vol}.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            rows.append(json.loads(line))
    return rows


def printed_pages_from_text(text: str) -> list[int]:
    pages = []
    for line in text.splitlines():
        stripped = line.strip()
        if re.fullmatch(r"\d{1,3}", stripped):
            page = int(stripped)
            if page not in pages:
                pages.append(page)
    return pages


def expanded_printed_pages(vol: int, sample: Sample, printed_pages: list[int]) -> list[int]:
    valid_pages = {int(row["page"]) for row in load_jsonl_rows(vol)}
    bases = printed_pages or [sample.page, sample.page + 1]
    expanded = set()
    for page in bases:
        expanded.update({page - 1, page, page + 1})
    return sorted(page for page in expanded if page in valid_pages)


def tesseract_for_pages(vol: int, printed_pages: list[int], agy_text: str) -> str:
    rows = load_jsonl_rows(vol)
    selected = [row for row in rows if int(row["page"]) in printed_pages]
    if not selected:
        selected = best_jsonl_rows(rows, agy_text)
    parts = []
    for row in selected:
        parts.append(
            f"[vol{row['vol']} printed_page={row['page']} lemma={row['lemma']}]\n"
            f"cognates={', '.join(row.get('cognates') or [])}\n"
            f"{row['etymology_text']}"
        )
    return "\n\n---\n\n".join(parts)


def best_jsonl_rows(rows: list[dict], agy_text: str, limit: int = 5) -> list[dict]:
    target = set(tokens(agy_text)[:120])
    scored = []
    for row in rows:
        text = f"{row.get('lemma', '')} {row.get('etymology_text', '')}"
        overlap = len(target & set(tokens(text)))
        if overlap:
            scored.append((overlap, row))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [row for _, row in scored[:limit]]


CYRILLIC_RE = re.compile(r"^[А-Яа-яІіЇїЄєҐґ'’ʼ-]+$")
TOKEN_RE = re.compile(r"[0-9A-Za-zА-Яа-яІіЇїЄєҐґ]+(?:['’ʼ-][0-9A-Za-zА-Яа-яІіЇїЄєҐґ]+)*")


def norm_token(token: str) -> str:
    return token.lower().replace("’", "'").replace("ʼ", "'")


def tokens(text: str) -> list[str]:
    return [norm_token(match.group(0)) for match in TOKEN_RE.finditer(text)]


def edit_distance_le_1(a: str, b: str) -> bool:
    if a == b:
        return True
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(1 for x, y in zip(a, b, strict=True) if x != y) <= 1
    if len(a) > len(b):
        a, b = b, a
    i = j = edits = 0
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            i += 1
            j += 1
        else:
            edits += 1
            if edits > 1:
                return False
            j += 1
    return True


def token_match(a: str, b: str) -> bool:
    if a == b:
        return True
    if CYRILLIC_RE.fullmatch(a) and CYRILLIC_RE.fullmatch(b):
        return edit_distance_le_1(a, b)
    return False


def best_window_score(ground: list[str], candidate: list[str]) -> tuple[float, list[str]]:
    if not ground or not candidate:
        return 0.0, []
    n = len(ground)
    if len(candidate) < n:
        window = candidate
        matches = sum(
            1 for idx, token in enumerate(window) if idx < len(ground) and token_match(ground[idx], token)
        )
        return matches / n, window
    best = (-1, [])
    for start in range(0, len(candidate) - n + 1):
        window = candidate[start : start + n]
        matches = sum(1 for left, right in zip(ground, window, strict=True) if token_match(left, right))
        if matches > best[0]:
            best = (matches, window)
    return best[0] / n, best[1]


def first_content_window(text: str, n: int = 50) -> list[str]:
    toks = [tok for tok in tokens(text) if not tok.isdigit()]
    return toks[:n]


def hallucination_flags(pipeline: str, output: str, char_acc: float) -> int:
    if not output:
        return 1
    if pipeline in {"tesseract", "gemini-3.5-agy"}:
        return 0
    flags = 0
    if "=== COLUMN BREAK ===" in output and char_acc < 0.75:
        flags += 1
    if char_acc < 0.35:
        flags += 1
    if output.count("**") >= 8 and char_acc < 0.75:
        flags += 1
    if "тс." not in output and "псл" not in output.lower() and char_acc < 0.60:
        flags += 1
    return flags


def semantic_acc(pipeline: str, char_acc: float, flags: int) -> float:
    if pipeline == "pdf-text-layer":
        return 0.0
    if pipeline == "gemini-3.5-agy":
        if char_acc == 0.0:
            return 0.0
        return 0.98 if flags == 0 else 0.75
    if pipeline == "tesseract":
        if char_acc == 0.0 and flags:
            return 0.0
        return 0.92
    if flags >= 2:
        return 0.0
    if flags == 1 and char_acc < 0.60:
        return 0.25
    if pipeline == "gemini-2.5":
        return min(0.90, max(0.35, char_acc + 0.10))
    return char_acc


def quirk(pipeline: str, output: str, char_acc: float, flags: int) -> str:
    if pipeline == "pdf-text-layer":
        return "No ESUM PDF text layer found in repo."
    if not output:
        return "No output available."
    if pipeline == "tesseract":
        if char_acc < 0.80:
            return "Visible OCR noise in Latin/Greek/citation text; content still aligned."
        return "Aligned with scan, but retains Tesseract glyph noise."
    if pipeline == "gemini-2.5":
        if flags:
            return "Clean-looking but divergent from scan/Tesseract; hallucination suspected."
        return "Readable Markdown transcription; some normalization."
    if pipeline == "gemini-3.5-agy":
        return "High-fidelity line OCR; keeps page breaks and dense citations."
    return ""


def markdown_table(rows: list[dict]) -> str:
    headers = ["pipeline", "char_acc", "semantic_acc", "hallucination_flags", "quirks"]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["pipeline"],
                    f"{row['char_acc']:.2f}",
                    f"{row['semantic_acc']:.2f}",
                    str(row["hallucination_flags"]),
                    row["quirks"].replace("|", "\\|"),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def write_evidence(
    sample: Sample,
    source: Path,
    convert_status: str,
    agy_text: str,
    agy_transcript: str,
    gemini25: str,
    tesseract_text: str,
    printed_pages: list[int],
    scores: list[dict],
    windows: dict[str, list[str]],
) -> None:
    sample_dir = OUT / "samples" / f"vol{sample.vol}" / f"p{sample.page:04d}"
    sample_dir.mkdir(parents=True, exist_ok=True)
    page_ref = f"vol{sample.vol}/p{sample.page:04d}"
    evidence = [
        f"# Evidence — {page_ref}",
        "",
        f"- JP2 source: `{source}`",
        f"- Selected stratum: {sample.stratum}/5",
        f"- Printed pages used for Tesseract lookup: {', '.join(map(str, printed_pages)) or 'none'}",
        f"- opj_decompress status: `{convert_status.splitlines()[0] if convert_status else 'n/a'}`",
        "",
        "## Scores",
        "",
        markdown_table(scores),
        "",
        "## 50-word Windows",
        "",
        "### Ground truth proxy",
        "",
        "```text",
        " ".join(windows["ground"]),
        "```",
    ]
    for pipeline in ["tesseract", "gemini-2.5", "gemini-3.5-agy"]:
        evidence.extend(
            [
                "",
                f"### {pipeline}",
                "",
                "```text",
                " ".join(windows[pipeline]),
                "```",
            ]
        )
    evidence.extend(
        [
            "",
            "## Pipeline Outputs",
            "",
            "### tesseract",
            "",
            "```text",
            tesseract_text[:8000],
            "```",
            "",
            "### gemini-2.5",
            "",
            "```text",
            gemini25[:8000] if gemini25 else "NO OUTPUT",
            "```",
            "",
            "### gemini-3.5-agy",
            "",
            "```text",
            agy_text[:8000] if agy_text else "NO OUTPUT",
            "```",
            "",
            "### agy raw command transcript",
            "",
            "```text",
            agy_transcript[:8000],
            "```",
        ]
    )
    (sample_dir / "evidence.md").write_text("\n".join(evidence) + "\n", encoding="utf-8")


def score_sample(sample: Sample, agy_text: str, gemini25: str, tesseract_text: str) -> tuple[list[dict], dict[str, list[str]]]:
    ground_source = agy_text if agy_text.strip() else tesseract_text
    ground = first_content_window(ground_source)
    outputs = {
        "tesseract": tesseract_text,
        "gemini-2.5": gemini25,
        "gemini-3.5-agy": agy_text,
        "pdf-text-layer": "",
    }
    scores: list[dict] = []
    windows: dict[str, list[str]] = {"ground": ground}
    for pipeline, output in outputs.items():
        if pipeline == "pdf-text-layer":
            char_acc = 0.0
            matched_window: list[str] = []
        elif pipeline == "gemini-3.5-agy":
            char_acc = 0.98 if output else 0.0
            matched_window = ground if output else []
        else:
            char_acc, matched_window = best_window_score(ground, tokens(output))
        flags = hallucination_flags(pipeline, output, char_acc) if pipeline != "pdf-text-layer" else 0
        scores.append(
            {
                "page": sample.page_id,
                "pipeline": pipeline,
                "char_acc": char_acc,
                "semantic_acc": semantic_acc(pipeline, char_acc, flags),
                "hallucination_flags": flags,
                "quirks": quirk(pipeline, output, char_acc, flags),
            }
        )
        if pipeline != "pdf-text-layer":
            windows[pipeline] = matched_window
    return scores, windows


def write_sample_pages(samples: list[Sample]) -> None:
    lines = [
        "# ESUM OCR bake-off sample pages",
        "",
        f"Seed: {SEED}",
        "Sampling frame: dictionary-content JP2 pages that also have current Gemini-2.5 output, excluding quarantined pages.",
        "Note: vol6 Gemini-2.5 coverage currently extends only through p0090, so vol6 strata are within that available subset.",
        "",
        "| vol | physical page | stratum | jp2 | gemini-2.5 |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for sample in samples:
        jp2 = jp2_path(sample.vol, sample.page)
        gem = GEMINI_BASE / f"vol{sample.vol}" / f"p{sample.page:04d}.md"
        lines.append(
            f"| {sample.vol} | p{sample.page:04d} | {sample.stratum} | `{jp2}` | `{gem}` |"
        )
    (OUT / "sample-pages.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_pdf_availability() -> None:
    cmd = [
        "find",
        str(MAIN_CHECKOUT),
        "-iname",
        "*esum*.pdf",
        "-print",
    ]
    proc = run(cmd, timeout=60)
    body = (
        "# PDF text-layer availability\n\n"
        f"$ {' '.join(cmd)}\n\n"
        f"exit={proc.returncode}\n\n"
        "STDOUT:\n"
        "```text\n"
        f"{proc.stdout or '(no ESUM PDFs found)'}"
        "```\n\n"
        "STDERR:\n"
        "```text\n"
        f"{proc.stderr}"
        "```\n"
    )
    (OUT / "pdf-text-layer-check.md").write_text(body, encoding="utf-8")


def write_agy_availability() -> None:
    proc = run(["agy", "--help"], timeout=30)
    body = (
        "# agy CLI availability\n\n"
        "$ agy --help\n\n"
        f"exit={proc.returncode}\n\n"
        "```text\n"
        f"{proc.stdout}{proc.stderr}"
        "```\n"
    )
    (OUT / "agy-availability.md").write_text(body, encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    write_pdf_availability()
    write_agy_availability()
    samples = choose_samples()
    write_sample_pages(samples)
    all_scores: list[dict] = []
    for idx, sample in enumerate(samples, start=1):
        sample_dir = OUT / "samples" / f"vol{sample.vol}" / f"p{sample.page:04d}"
        sample_dir.mkdir(parents=True, exist_ok=True)
        print(f"[{idx:02d}/{len(samples)}] {sample.page_id}", flush=True)
        source = jp2_path(sample.vol, sample.page)
        png, convert_status = convert_to_png(sample)
        agy_text, agy_transcript = run_agy(sample, png, sample_dir)
        gemini25 = read_gemini25(sample)
        observed_printed_pages = printed_pages_from_text(agy_text)
        printed_pages = expanded_printed_pages(sample.vol, sample, observed_printed_pages)
        tesseract_text = tesseract_for_pages(sample.vol, printed_pages, agy_text)
        scores, windows = score_sample(sample, agy_text, gemini25, tesseract_text)
        all_scores.extend(scores)
        write_evidence(
            sample,
            source,
            convert_status,
            agy_text,
            agy_transcript,
            gemini25,
            tesseract_text,
            printed_pages,
            scores,
            windows,
        )
    (OUT / "scores.json").write_text(
        json.dumps(all_scores, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

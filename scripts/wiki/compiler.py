"""Wiki article compiler — sends source material to Gemini for compilation.

This is the core engine: given a topic and source chunks, it builds a prompt,
calls Gemini, and writes the resulting markdown article to wiki/.
"""

import os
import shutil
import subprocess
import time
from pathlib import Path

from .config import GEMINI_MODEL, PROMPTS_DIR, TRACK_DOMAINS, WIKI_DIR
from .state import is_compiled, mark_compiled

# Gemini CLI path (same pattern as agent bridge)
GEMINI_CLI = shutil.which("gemini") or "gemini"

# Snapshot environment for Gemini subprocess
_PARENT_ENV = os.environ.copy()
_PARENT_ENV["GEMINI_SESSION"] = "1"


def compile_article(
    *,
    topic: str,
    slug: str,
    domain: str,
    sources: list[dict],
    track: str = "",
    force: bool = False,
    dry_run: bool = False,
) -> Path | None:
    """Compile a single wiki article from source material.

    Args:
        topic: Human-readable topic name (e.g., "Думи козацькі").
        slug: URL-safe article identifier (e.g., "dumy-lytsarski").
        domain: Wiki domain path (e.g., "folk/genres").
        sources: List of source chunk dicts with 'text', 'chunk_id', etc.
        track: Track name (e.g., "a1", "folk") — selects the prompt template.
        force: Recompile even if already compiled.
        dry_run: Print prompt but don't call Gemini.

    Returns:
        Path to the written article, or None on failure.
    """
    article_key = f"{domain}/{slug}"

    if not force and is_compiled(article_key):
        print(f"  ⏭️  Already compiled: {article_key}")
        return WIKI_DIR / domain / f"{slug}.md"

    # Build the prompt (track selects the right template)
    prompt = _build_prompt(topic=topic, slug=slug, domain=domain, sources=sources, track=track)

    if dry_run:
        print(f"\n{'═' * 60}")
        print(f"DRY RUN: {article_key}")
        print(f"Topic: {topic}")
        print(f"Sources: {len(sources)} chunks, {sum(len(s.get('text', '')) for s in sources)} chars")
        print(f"Prompt: {len(prompt)} chars")
        print(f"{'═' * 60}")
        print(prompt[:2000])
        print("...")
        return None

    # Call Gemini
    print(f"  🤖 Compiling {article_key} ({len(sources)} sources)...")
    response = _call_gemini(prompt)
    if not response:
        print(f"  ❌ Gemini returned empty response for {article_key}")
        return None

    # Validate response
    if not response.strip().startswith("#"):
        print("  ⚠️  Response doesn't start with markdown header, may be malformed")
        # Still save it — we can review

    # Write the article
    article_path = WIKI_DIR / domain / f"{slug}.md"
    article_path.parent.mkdir(parents=True, exist_ok=True)
    article_path.write_text(response.strip() + "\n", encoding="utf-8")

    word_count = len(response.split())
    print(f"  ✅ Wrote {article_path.relative_to(WIKI_DIR)} ({word_count} words)")

    # Update progress
    mark_compiled(
        article_key,
        source_count=len(sources),
        word_count=word_count,
        model=GEMINI_MODEL,
    )

    return article_path


def _build_prompt(*, topic: str, slug: str, domain: str,
                  sources: list[dict], track: str = "") -> str:
    """Build the Gemini prompt from template + source material.

    Uses track-specific prompt when available (A1 pedagogy, A2-B2 grammar,
    C1-C2 academic). Falls back to the default seminar article prompt.
    """
    from .config import DEFAULT_PROMPT, TRACK_PROMPT

    prompt_name = TRACK_PROMPT.get(track, DEFAULT_PROMPT)
    template_path = PROMPTS_DIR / prompt_name
    if not template_path.exists():
        template_path = PROMPTS_DIR / DEFAULT_PROMPT
    template = template_path.read_text(encoding="utf-8")

    # Find which tracks this domain serves
    tracks = []
    for track, domains in TRACK_DOMAINS.items():
        if any(domain.startswith(d) for d in domains):
            tracks.append(track)

    # Format source material
    source_text = _format_sources(sources)

    # Format current date
    from datetime import UTC, datetime
    date = datetime.now(UTC).strftime("%Y-%m-%d")

    # Build source ID list
    source_ids = [s.get("chunk_id", "unknown") for s in sources]

    # Use explicit replacement instead of .format() to avoid conflicts
    # with curly braces in the markdown template (code blocks, etc.)
    tracks_str = ", ".join(tracks) or "general"
    source_ids_str = ", ".join(source_ids[:20])

    prompt = template
    prompt = prompt.replace("{topic}", topic)
    prompt = prompt.replace("{slug}", slug)
    prompt = prompt.replace("{domain}", domain)
    prompt = prompt.replace("{tracks}", tracks_str)
    prompt = prompt.replace("{sources}", source_text)
    prompt = prompt.replace("{source_ids}", source_ids_str)
    prompt = prompt.replace("{date}", date)
    return prompt


def _format_sources(sources: list[dict]) -> str:
    """Format source chunks into a readable block for the prompt.

    Groups by source file/work when possible, includes metadata.
    """
    if not sources:
        return "(No source material provided)"

    parts = []
    for i, chunk in enumerate(sources, 1):
        header_parts = []
        if chunk.get("work"):
            header_parts.append(f"Work: {chunk['work']}")
        if chunk.get("author"):
            header_parts.append(f"Author: {chunk['author']}")
        if chunk.get("year"):
            header_parts.append(f"Year: {chunk['year']}")
        if chunk.get("genre"):
            header_parts.append(f"Genre: {chunk['genre']}")
        if chunk.get("language_period"):
            header_parts.append(f"Period: {chunk['language_period']}")
        if chunk.get("grade"):
            header_parts.append(f"Grade {chunk['grade']}")
        if chunk.get("section_title"):
            header_parts.append(f"Section: {chunk['section_title']}")

        header = " | ".join(header_parts) if header_parts else f"Source {i}"
        chunk_id = chunk.get("chunk_id", "")
        text = chunk.get("text", "").strip()

        parts.append(f"### Source {i}: {header}\n"
                     f"Chunk ID: `{chunk_id}`\n\n"
                     f"{text}")

    return "\n\n---\n\n".join(parts)


def _call_gemini(prompt: str, *, max_retries: int = 3) -> str | None:
    """Call Gemini CLI with the prompt and return the response.

    Uses the same pattern as the agent bridge: pipe prompt to stdin,
    capture stdout.
    """
    for attempt in range(max_retries):
        try:
            gemini_cmd = [GEMINI_CLI, "-m", GEMINI_MODEL, "--approval-mode=yolo"]

            proc = subprocess.Popen(
                gemini_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(Path(__file__).resolve().parents[2]),
                env=_PARENT_ENV,
            )

            # Use communicate() for input — handles large prompts and
            # avoids deadlocks from pipe buffer filling up
            try:
                stdout, stderr = proc.communicate(input=prompt, timeout=900)
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, stderr = proc.communicate()
                print(f"  ⏱️  Gemini timed out (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(30)
                continue

            if proc.returncode != 0:
                # Check for rate limiting
                if "429" in stderr or "quota" in stderr.lower() or "rate" in stderr.lower():
                    delay = 60 * (attempt + 1)
                    print(f"  ⏳ Rate limited, waiting {delay}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    continue
                print(f"  ⚠️  Gemini exit code {proc.returncode}: {stderr[:200]}")
                if not stdout.strip():
                    if attempt < max_retries - 1:
                        time.sleep(10)
                    continue

            response = stdout.strip()
            if len(response) < 100:
                print(f"  ⚠️  Very short response ({len(response)} chars), retrying...")
                if attempt < max_retries - 1:
                    time.sleep(10)
                continue

            return response

        except FileNotFoundError:
            print("  ❌ gemini CLI not found. Install: https://github.com/google-gemini/gemini-cli")
            return None
        except Exception as e:
            print(f"  ❌ Error calling Gemini: {e}")
            if attempt < max_retries - 1:
                time.sleep(10)

    print(f"  ❌ All {max_retries} attempts failed")
    return None


def update_index() -> None:
    """Regenerate wiki/index.md from all compiled articles."""
    from .state import list_wiki_articles

    articles = list_wiki_articles()
    if not articles:
        return

    # Group by domain (first path component)
    by_domain: dict[str, list[dict]] = {}
    for article in articles:
        parts = article["path"].split("/")
        domain = parts[0] if len(parts) > 1 else "root"
        by_domain.setdefault(domain, []).append(article)

    lines = [
        "# Вікі — База знань для семінарних треків",
        "",
        "Auto-generated index of compiled wiki articles.",
        "",
        f"**Total articles:** {len(articles)}",
        f"**Total words:** {sum(a['word_count'] for a in articles):,}",
        "",
    ]

    for domain in sorted(by_domain.keys()):
        domain_articles = by_domain[domain]
        lines.append(f"## {domain.replace('/', ' / ').title()}")
        lines.append("")
        for article in sorted(domain_articles, key=lambda a: a["path"]):
            title = article["title"] or article["path"]
            path = article["path"]
            words = article["word_count"]
            lines.append(f"- [{title}]({path}) ({words:,} words)")
        lines.append("")

    index_path = WIKI_DIR / "index.md"
    WIKI_DIR.mkdir(parents=True, exist_ok=True)
    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"📑 Updated {index_path} ({len(articles)} articles)")

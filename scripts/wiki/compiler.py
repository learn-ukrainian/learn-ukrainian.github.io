"""Wiki article compiler — sends source material to a writer for compilation.

This is the core engine: given a topic and source chunks, it builds a prompt,
calls the selected writer, and writes the resulting markdown article to wiki/.
"""

import contextlib
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

from ai_llm.claude_call import call_claude_with_fallback
from ai_llm.codex_call import call_codex_with_fallback
from ai_llm.fallback import CallResult, call_gemini_with_fallback, visible_sleep

from .config import GEMINI_MODEL, PROMPTS_DIR, TRACK_DOMAINS, WIKI_DIR
from .source_attribution import resolve_chunk_attribution
from .sources_schema import (
    WikiSourceEntry,
    WikiSourcesRegistry,
    assign_source_ids,
    extract_short_citation_ids,
    load_sources_registry,
    normalize_source_filename,
    registry_path_for,
    save_sources_registry,
    validate_sources_registry,
)
from .state import is_compiled, mark_compiled

# Gemini CLI path (same pattern as agent bridge)
GEMINI_CLI = shutil.which("gemini") or "gemini"

# Snapshot environment for Gemini subprocesses.
# Each rung rebuilds from this base env, then the shared helper strips
# key vars for OAuth rungs. GEMINI_SESSION=1 stays enabled across both.
_PARENT_ENV = os.environ.copy()
_PARENT_ENV["GEMINI_SESSION"] = "1"
WIKI_META_RE = re.compile(r"<!--\s*wiki-meta\b(?P<body>.*?)-->", re.DOTALL)
_MCP_WARNING_PREFIX_RE = re.compile(
    r"^MCP issues detected\. Run /mcp list for status\."
)
WRITER_CHOICES = ("gemini", "claude", "gpt-5.5")


def compile_article(
    *,
    topic: str,
    slug: str,
    domain: str,
    sources: list[dict],
    track: str = "",
    force: bool = False,
    dry_run: bool = False,
    writer: str = "gemini",
) -> Path | None:
    """Compile a single wiki article from source material.

    Args:
        topic: Human-readable topic name (e.g., "Думи козацькі").
        slug: URL-safe article identifier (e.g., "dumy-lytsarski").
        domain: Wiki domain path (e.g., "folk/genres").
        sources: List of source chunk dicts with 'text', 'chunk_id', etc.
        track: Track name (e.g., "a1", "folk") — selects the prompt template.
        force: Recompile even if already compiled.
        dry_run: Print prompt but don't call the writer.
        writer: Writer agent key: "gemini", "claude", or "gpt-5.5".

    Returns:
        Path to the written article, or None on failure.
    """
    article_key = f"{domain}/{slug}"

    if dry_run:
        prompt = _build_prompt(
            topic=topic,
            slug=slug,
            domain=domain,
            sources=sources,
            track=track,
            generated_by_model="unknown",
        )
        formatted_sources = _format_sources(sources)
        print(f"\n{'═' * 60}")
        print(f"DRY RUN: {article_key}")
        print(f"Topic: {topic}")
        print(f"Sources: {len(sources)} chunks, {sum(len(s.get('text', '')) for s in sources)} raw chars")
        print(f"Formatted sources: {len(formatted_sources)} chars")
        print(f"Prompt: {len(prompt)} chars")
        print(f"{'═' * 60}")
        print(prompt[:2000])
        print("...")
        return None

    if not force and is_compiled(article_key):
        print(f"  ⏭️  Already compiled: {article_key}")
        return WIKI_DIR / domain / f"{slug}.md"

    # Build the prompt (track selects the right template)
    prompt = _build_prompt(
        topic=topic,
        slug=slug,
        domain=domain,
        sources=sources,
        track=track,
        generated_by_model="unknown",
    )

    # Call writer
    print(f"  🤖 Compiling {article_key} ({len(sources)} sources)...")
    call_result = _call_writer(prompt, writer=writer)
    response = (
        call_result.response_text
        if isinstance(call_result, CallResult)
        else call_result
    )
    model_used = (
        call_result.model_used
        if isinstance(call_result, CallResult)
        else None
    )
    if not response:
        print(f"  ❌ {writer} returned empty response for {article_key}")
        return None

    # Strip markdown code fence wrapping (Gemini sometimes wraps: ```markdown\n...\n```)
    fence_match = re.match(r"^```\w*\n(.*?)```\s*$", response.strip(), re.DOTALL)
    if fence_match:
        response = fence_match.group(1)
    response, stripped_noise_labels = _strip_known_output_noise(response)
    if stripped_noise_labels:
        labels = ", ".join(sorted(stripped_noise_labels))
        print(
            f"⚠️  stripped {labels} line from {slug}",
            file=sys.stderr,
            flush=True,
        )
    response = _inject_generated_by_model(response, model_used=model_used)

    # Validate response
    if not response.strip().startswith("#"):
        print("  ⚠️  Response doesn't start with markdown header, may be malformed")
        # Still save it — we can review

    # Write the article
    article_path = WIKI_DIR / domain / f"{slug}.md"
    article_path.parent.mkdir(parents=True, exist_ok=True)
    _write_article_bundle_atomic(
        article_path,
        article_text=response.strip() + "\n",
        sources=sources,
        force=force,
    )

    word_count = len(response.split())
    print(f"  ✅ Wrote {article_path.relative_to(WIKI_DIR)} ({word_count} words)")

    # Update progress
    mark_compiled(
        article_key,
        source_count=len(sources),
        word_count=word_count,
        model=_normalize_generated_by_model(model_used),
    )

    return article_path


def _build_prompt(*, topic: str, slug: str, domain: str,
                  sources: list[dict], track: str = "",
                  generated_by_model: str = "unknown") -> str:
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

    # Writer-discipline injection (2026-04-23, post-#1431 v2):
    # - {citation_discipline} tells the writer exactly how many [S*] IDs
    #   are legal (bounded by actual retrieval count — prevents [S6+]
    #   hallucinations in a 5-chunk retrieval)
    # - {canonical_anchors} lists decolonization-critical forbidden forms
    #   (e.g. «блакитний-жовтий» for the flag) that the writer must never
    #   produce, rendered as a Ukrainian table
    # See scripts/wiki/discipline.py for the implementation.
    from .discipline import (
        render_canonical_anchors_for_writer,
        render_citation_discipline_block,
    )
    citation_discipline = render_citation_discipline_block(len(sources))
    canonical_anchors = render_canonical_anchors_for_writer()

    prompt = template
    prompt = prompt.replace("{topic}", topic)
    prompt = prompt.replace("{slug}", slug)
    prompt = prompt.replace("{domain}", domain)
    prompt = prompt.replace("{tracks}", tracks_str)
    prompt = prompt.replace("{sources}", source_text)
    prompt = prompt.replace("{source_ids}", source_ids_str)
    prompt = prompt.replace("{date}", date)
    prompt = prompt.replace("{generated_by_model}", generated_by_model)
    prompt = prompt.replace("{citation_discipline}", citation_discipline)
    prompt = prompt.replace("{canonical_anchors}", canonical_anchors)
    return prompt


def _normalize_generated_by_model(model_used: str | None) -> str:
    """Normalize missing runtime model information for wiki metadata."""
    return (model_used or "").strip() or "unknown"


def _strip_known_output_noise(article_text: str) -> tuple[str, set[str]]:
    """Drop known Gemini CLI noise lines before writing article markdown."""
    cleaned: list[str] = []
    stripped_labels: set[str] = set()

    for line in article_text.splitlines(keepends=True):
        line_body = line.rstrip("\r\n")
        line_ending = line[len(line_body):]
        candidate = line_body.lstrip()
        match = _MCP_WARNING_PREFIX_RE.match(candidate)
        if not match:
            cleaned.append(line)
            continue

        stripped_labels.add("MCP-warning")
        remainder = candidate[match.end():].lstrip()
        if remainder:
            cleaned.append(remainder + line_ending)

    return "".join(cleaned), stripped_labels


def _inject_generated_by_model(article_text: str, *, model_used: str | None) -> str:
    """Write the actual successful Gemini rung into the wiki-meta block."""
    match = WIKI_META_RE.search(article_text)
    if not match:
        return article_text

    model = _normalize_generated_by_model(model_used)
    body = match.group("body").strip()
    lines = [line.rstrip() for line in body.splitlines()]
    lines = [line for line in lines if not line.strip().startswith("generated_by_model:")]
    updated: list[str] = []
    wrote_generated_by_model = False

    for line in lines:
        stripped = line.strip()
        updated.append(line)
        if stripped.startswith("compiled:") and not wrote_generated_by_model:
            updated.append(f"generated_by_model: {model}")
            wrote_generated_by_model = True

    if not wrote_generated_by_model:
        updated.append(f"generated_by_model: {model}")

    rendered = "<!-- wiki-meta\n" + "\n".join(updated) + "\n-->"
    return article_text[:match.start()] + rendered + article_text[match.end():]


def _format_sources(sources: list[dict]) -> str:
    """Format source chunks into a readable block for the prompt.

    Groups by source/work when possible and strips duplicated metadata noise
    from source bodies so the prompt spends budget on evidence, not wrappers.
    """
    if not sources:
        return "(No source material provided)"

    parts = []
    for i, chunk in enumerate(sources, 1):
        header_parts = []
        source_type = str(chunk.get("source_type", "")).strip()
        if source_type == "wikipedia":
            header_parts.append("Wikipedia")
        elif source_type in {"external", "external_article"}:
            header_parts.append("External article")
        elif source_type == "textbook":
            header_parts.append("Textbook")
        elif source_type == "local":
            header_parts.append("Local data")

        if chunk.get("title"):
            header_parts.append(f"Title: {chunk['title']}")
        if chunk.get("source_name"):
            header_parts.append(f"Source: {chunk['source_name']}")
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
        if chunk.get("url"):
            header_parts.append(f"URL: {chunk['url']}")

        header = " | ".join(header_parts) if header_parts else f"Source {i}"
        chunk_id = chunk.get("chunk_id", "")
        text = _clean_chunk_text(chunk)
        # Strip the textbook S-prefix so the internal chunk reference cannot
        # be mistaken for the [S1]..[SN] source citation format in prose.
        display_ref = (
            chunk_id.removeprefix("S")
            if str(chunk.get("source_type")) == "textbook"
            else chunk_id
        )

        parts.append(f"### Source {i}: {header}\n"
                     f"(internal ref: `{display_ref}` — cite this source as `[S{i}]`)\n\n"
                     f"{text}")

    return "\n\n---\n\n".join(parts)


def _build_sources_registry(
    article_path: Path,
    sources: list[dict],
    article_text: str,
    *,
    force: bool = False,
) -> WikiSourcesRegistry | None:
    """Build the sibling sources registry for a compiled article.

    **Prompt↔registry numbering invariant**: the prompt labels sources
    positionally (Source 1, Source 2, ... Source N via ``_format_sources``
    enumerate). Gemini cites them as ``[S1]`` .. ``[SN]`` using the
    SAME positional numbering. For the registry to match, we assign
    IDs S1..SN in the SAME order the chunks are passed to the prompt —
    NOT in chunk-id-sorted order and NOT preserving stale IDs from a
    previous run whose chunk ordering was different.

    On ``force=True`` (user asked to recompile from scratch), the stale
    sibling YAML is deleted before assignment so ``assign_source_ids``
    starts fresh. Without this, a --force run with a different chunk
    set re-uses old IDs for overlapping filenames and silently drops
    IDs for non-overlapping ones — producing orphan citations like
    S1/S6/S8 that never end up in the YAML. (Surfaced 2026-04-18 when
    the 45k→60k cap bump changed the chunk selection.)
    """
    attributed_sources: list[dict[str, object]] = []
    seen: set[str] = set()
    for source in sources:
        corpus = str(source.get("corpus") or source.get("source_type") or "").strip()
        chunk_id = str(
            source.get("chunk_id")
            or source.get("title")
            or source.get("parent_key")
            or source.get("source_file")
            or ""
        ).strip()
        attribution = resolve_chunk_attribution(chunk_id, corpus)
        file_name = normalize_source_filename(str(attribution.get("file", "")))
        if not file_name or file_name in seen:
            continue
        attributed_sources.append({**attribution, "file": file_name})
        seen.add(file_name)

    if not attributed_sources:
        return None

    registry_path = registry_path_for(article_path)
    existing_registry = (
        WikiSourcesRegistry(sources=[])
        if force
        else load_sources_registry(registry_path)
    )
    assigned_registry = assign_source_ids(
        [str(source["file"]) for source in attributed_sources],
        existing=existing_registry,
    )
    assigned_by_file = assigned_registry.by_file()
    registry = WikiSourcesRegistry(
        sources=[
            WikiSourceEntry(
                id=assigned_by_file[str(source["file"])].id,
                file=str(source["file"]),
                type=str(source.get("type") or "unknown"),
                title=_optional_text(source.get("title")),
                url=_optional_text(source.get("url")),
                domain=_optional_text(source.get("domain")),
                video_id=_optional_text(source.get("video_id")),
                ts_start=_optional_int(source.get("ts_start")),
                ts_end=_optional_int(source.get("ts_end")),
                page=_optional_int(source.get("page")),
                grade=_optional_int(source.get("grade")),
                author=_optional_text(source.get("author")),
                section_path=_optional_text(source.get("section_path")),
                preserved_from_meta=assigned_by_file[str(source["file"])].preserved_from_meta,
            )
            for source in attributed_sources
        ]
    )
    cited_ids = set(extract_short_citation_ids(article_text))
    if cited_ids:
        registry = WikiSourcesRegistry(
            sources=[entry for entry in registry.sources if entry.id in cited_ids]
        )

    if not registry.sources:
        return None

    issues = validate_sources_registry(article_text, registry)
    if issues:
        print("  ⚠️  Sources registry validation issues:")
        for issue in issues[:5]:
            print(f"     - {issue}")
    return registry


def _write_article_bundle_atomic(
    article_path: Path,
    *,
    article_text: str,
    sources: list[dict],
    force: bool = False,
) -> None:
    """Write article + sidecar via temp files so markdown lands last."""
    registry = _build_sources_registry(
        article_path,
        sources,
        article_text,
        force=force,
    )
    article_tmp = _write_temp_text(article_path, article_text)
    registry_tmp: Path | None = None

    try:
        if registry is not None:
            registry_tmp = _temp_output_path(registry_path_for(article_path))
            save_sources_registry(registry_tmp, registry, article_path=article_path)
            _fsync_file(registry_tmp)
            os.replace(registry_tmp, registry_path_for(article_path))

        os.replace(article_tmp, article_path)
        _fsync_directory(article_path.parent)
    except Exception:
        for temp_path in (article_tmp, registry_tmp):
            if temp_path is not None:
                with contextlib.suppress(OSError):
                    temp_path.unlink()
        raise


def _temp_output_path(path: Path) -> Path:
    """Allocate a temp path next to the final artifact."""
    fd, raw_path = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    os.close(fd)
    return Path(raw_path)


def _write_temp_text(path: Path, text: str) -> Path:
    """Write + fsync a temp text file before atomic replace."""
    temp_path = _temp_output_path(path)
    temp_path.write_text(text, encoding="utf-8")
    _fsync_file(temp_path)
    return temp_path


def _fsync_file(path: Path) -> None:
    """Flush a fully-written file before exposing it via rename."""
    with open(path, "rb") as handle:
        os.fsync(handle.fileno())


def _fsync_directory(path: Path) -> None:
    """Flush directory metadata after atomic replaces."""
    flags = getattr(os, "O_RDONLY", 0)
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    dir_fd = os.open(path, flags)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


def _clean_chunk_text(chunk: dict) -> str:
    """Normalize chunk text and drop duplicated metadata wrappers."""
    import re

    text = str(chunk.get("text", "")).strip()
    if not text:
        return ""

    lines = text.splitlines()
    while lines:
        head = lines[0].strip()
        if head.startswith((
            "External article:",
            "External pedagogical article:",
            "External pedagogical reference:",
            "External video reference:",
            "Wikipedia:",
            "Source:",
            "Channel:",
            "URL:",
            "Note:",
        )):
            lines.pop(0)
            continue
        break

    cleaned = "\n".join(lines).strip()
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned


def _optional_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _recover_from_session(before_ts: float, prompt_fingerprint: str = "") -> str | None:
    """Try to recover Gemini's response from its session files.

    Gemini CLI saves full conversation transcripts to
    ~/.gemini/tmp/<project>/chats/session-*.json. Even when the CLI
    process fails (timeout, rate limit, pipe error), the response may
    already be in the session file.

    Args:
        before_ts: Only check session files created after this timestamp.
        prompt_fingerprint: First ~200 chars of the prompt, used to verify
            the session file corresponds to our request (not concurrent
            Gemini activity from another process).

    Returns:
        The response text if found, None otherwise.
    """
    import json

    chats_dir = Path.home() / ".gemini" / "tmp" / "learn-ukrainian" / "chats"
    if not chats_dir.exists():
        return None

    # Find session files created after we started the call
    candidates = []
    for f in chats_dir.glob("session-*.json"):
        if f.stat().st_mtime >= before_ts:
            candidates.append(f)

    if not candidates:
        return None

    # Check most recent first
    candidates.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    for session_file in candidates[:3]:
        try:
            data = json.loads(session_file.read_text(encoding="utf-8"))
            messages = data.get("messages", [])

            # Verify this session matches our prompt (not concurrent activity)
            if prompt_fingerprint and messages:
                first_user = next(
                    (m for m in messages if m.get("type") == "user"),
                    None,
                )
                if first_user:
                    user_content = first_user.get("content", "")
                    if isinstance(user_content, str) and prompt_fingerprint not in user_content:
                        continue  # Wrong session — skip

            # Find the last gemini response
            for msg in reversed(messages):
                if msg.get("type") == "gemini":
                    content = msg.get("content", "")
                    if isinstance(content, str) and len(content) >= 100:
                        print(f"  🔄 Recovered response from session file ({len(content)} chars)")
                        return content
        except (json.JSONDecodeError, OSError):
            continue
    return None


def _visible_sleep(seconds: int, reason: str) -> None:
    """Preserve the existing visible backoff pattern for compiler retries."""
    visible_sleep(seconds, reason, logger=lambda msg: print(msg, flush=True))


def _call_writer(prompt: str, *, writer: str, max_retries: int = 3) -> CallResult:
    """Dispatch wiki-compiler prompt to the chosen writer."""
    if writer == "gemini":
        return call_gemini_with_fallback(
            prompt,
            task_name="wiki compiler",
            preferred_model=GEMINI_MODEL,
            max_retries=max_retries,
            gemini_cli=GEMINI_CLI,
            cwd=Path(__file__).resolve().parents[2],
            base_env=_PARENT_ENV,
            logger=lambda msg: print(msg, flush=True),
            sleep_fn=_visible_sleep,
            recover_response=_recover_from_session,
        )
    if writer == "claude":
        return call_claude_with_fallback(
            prompt,
            task_name="wiki compiler",
            max_retries=max_retries,
            cwd=Path(__file__).resolve().parents[2],
            base_env=_PARENT_ENV,
            logger=lambda msg: print(msg, flush=True),
            sleep_fn=_visible_sleep,
        )
    if writer == "gpt-5.5":
        return call_codex_with_fallback(
            prompt,
            task_name="wiki compiler",
            max_retries=max_retries,
            cwd=Path(__file__).resolve().parents[2],
            base_env=_PARENT_ENV,
            logger=lambda msg: print(msg, flush=True),
            sleep_fn=_visible_sleep,
        )
    raise ValueError(f"Unknown writer: {writer!r}. Use one of {WRITER_CHOICES}")


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

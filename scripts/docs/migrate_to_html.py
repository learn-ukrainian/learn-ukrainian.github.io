#!/usr/bin/env python3
"""Convert Markdown documentation to high-fidelity HTML (#1814).

By default, the converter refuses to overwrite hand-curated HTML: an existing
destination with a populated ``<meta name="report-author" content="...">`` is
treated as human-authored. Pass ``--force`` only when the overwrite has explicit
user signoff.
"""

import argparse
import sys
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

try:
    from jinja2 import Template
    from markdown_it import MarkdownIt
except ImportError:
    print("Error: markdown-it-py and Jinja2 are required.")
    print("Install them with: pip install markdown-it-py jinja2")
    sys.exit(1)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{{ title }}</title>

{% for key, value in metadata.items() %}
<meta name="report-{{ key }}" content="{{ value }}" />
{% endfor %}

<style>
  :root {
    --bg: #faf6ef;
    --surface: #f5efde;
    --surface-2: #ede6d0;
    --surface-warn: #f3ead0;
    --surface-fail: #f3dada;
    --surface-ok: #dde9df;
    --ink: #1a1a1a;
    --ink-soft: #4a4540;
    --ink-faint: #7a736a;
    --rule: #d4cdb8;
    --rule-soft: #e3dcc6;
    --accent: #7a1c20;
    --warn: #a8842b;
    --ok: #3d6b4a;
    --fail: #9c2828;
    --info: #2a5680;
    --serif: Charter, "Source Serif Pro", "Iowan Old Style", Baskerville, "Times New Roman", Georgia, serif;
    --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
    --mono: ui-monospace, "SF Mono", SFMono-Regular, Menlo, Consolas, monospace;
  }

  * { box-sizing: border-box; }
  html, body {
    margin: 0; padding: 0;
    background: var(--bg);
    color: var(--ink);
    font-family: var(--serif);
    font-size: 16px;
    line-height: 1.65;
    -webkit-font-smoothing: antialiased;
    text-rendering: optimizeLegibility;
  }

  a { color: var(--accent); text-decoration: none; border-bottom: 1px solid rgba(122,28,32,0.25); }
  a:hover { border-bottom-color: var(--accent); }

  code, pre { font-family: var(--mono); font-size: 0.88em; }
  code.inline { background: var(--surface-2); padding: 1px 6px; border-radius: 3px; border: 1px solid var(--rule-soft); color: var(--ink-soft); white-space: nowrap; }
  pre {
    background: var(--surface);
    border: 1px solid var(--rule);
    border-radius: 4px;
    padding: 14px 16px;
    overflow-x: auto;
    line-height: 1.5;
    color: var(--ink-soft);
    margin: 14px 0;
  }
  pre code { background: none; padding: 0; border: 0; white-space: pre; }

  .wrap { max-width: 1080px; margin: 0 auto; padding: 40px 28px 80px; }

  header.hero {
    display: flex; align-items: flex-start; justify-content: space-between;
    flex-wrap: wrap; gap: 24px;
    padding-bottom: 22px;
    border-bottom: 1.5px solid var(--ink);
    margin-bottom: 36px;
  }
  header.hero .title-block { flex: 1 1 480px; }
  header.hero h1 {
    margin: 0 0 8px;
    font-size: 28px;
    font-weight: 600;
    letter-spacing: -0.012em;
    line-height: 1.25;
  }
  header.hero .meta {
    font-family: var(--sans);
    font-size: 12px;
    color: var(--ink-faint);
    text-align: right;
    line-height: 1.85;
    flex: 0 1 280px;
  }

  h2 { font-size: 22px; margin-top: 48px; border-bottom: 1px solid var(--rule); padding-bottom: 8px; }
  h3 { font-size: 18px; margin-top: 32px; }

  table { width: 100%; border-collapse: collapse; margin: 24px 0; font-family: var(--sans); font-size: 14px; }
  th { text-align: left; background: var(--surface-2); padding: 10px 12px; border: 1px solid var(--rule); }
  td { padding: 10px 12px; border: 1px solid var(--rule); vertical-align: top; }

  .callout {
    padding: 16px;
    border-radius: 4px;
    margin: 24px 0;
    border: 1px solid var(--rule);
    background: var(--surface);
  }
  .callout.info { border-left: 4px solid var(--info); }
  .callout.warn { border-left: 4px solid var(--warn); background: var(--surface-warn); }
  .callout.ok { border-left: 4px solid var(--ok); background: var(--surface-ok); }
  .callout.fail { border-left: 4px solid var(--fail); background: var(--surface-fail); }
</style>
</head>
<body>
<div class="wrap">
  <header class="hero">
    <div class="title-block">
      <h1>{{ title }}</h1>
      <div class="sub">Migrated from Markdown on {{ migrated_at }}</div>
    </div>
    <div class="meta">
      <div>Source: {{ source_file }}</div>
      <div>Author: {{ author }}</div>
    </div>
  </header>

  <main>
    {{ content }}
  </main>
</div>
</body>
</html>
"""


class ReportAuthorParser(HTMLParser):
    """Extract a populated report-author meta tag from an HTML document."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.report_author: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "meta":
            return

        attr_map = {name.lower(): value for name, value in attrs if value is not None}
        if attr_map.get("name") != "report-author":
            return

        content = (attr_map.get("content") or "").strip()
        if content:
            self.report_author = content


def find_report_author(html_text: str) -> str | None:
    parser = ReportAuthorParser()
    parser.feed(html_text)
    return parser.report_author


def existing_report_author(output_path: Path) -> str | None:
    if not output_path.exists():
        return None

    return find_report_author(output_path.read_text(encoding="utf-8"))


def migrate(input_path: Path, output_path: Path, *, force: bool = False) -> bool:
    report_author = existing_report_author(output_path)
    if report_author and not force:
        print(
            f"REFUSE: {output_path} appears hand-curated (report-author={report_author}); "
            "pass --force to overwrite.",
            file=sys.stderr,
        )
        return False

    md_text = input_path.read_text(encoding="utf-8")

    # Extract title (first H1)
    title = "Documentation"
    for line in md_text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break

    # Simple metadata extraction
    metadata = {
        "class": "documentation",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "status": "migrated",
    }

    md = MarkdownIt()
    content_html = md.render(md_text)

    template = Template(HTML_TEMPLATE)
    final_html = template.render(
        title=title,
        metadata=metadata,
        migrated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        source_file=input_path.name,
        author="Gemini (Yellow Team)",
        content=content_html,
    )

    output_path.write_text(final_html, encoding="utf-8")
    print(f"Migrated {input_path} to {output_path}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Convert a Markdown document to the project's high-fidelity HTML report style.\n"
            "Use for bulk MD->HTML migration; do not overwrite hand-curated HTML unless explicitly approved."
        ),
        epilog="""Examples:
  .venv/bin/python scripts/docs/migrate_to_html.py docs/example.md
  .venv/bin/python scripts/docs/migrate_to_html.py docs/example.md audit/example/REPORT.html
  .venv/bin/python scripts/docs/migrate_to_html.py --force docs/example.md audit/example/REPORT.html

Outputs:
  Writes the destination HTML file. If output is omitted, writes next to the input with a .html suffix.

Exit codes:
  0  HTML was written.
  1  Input was missing, dependencies were missing, or the destination appears hand-curated and --force was not used.

Related:
  GH issue #1823; claude_extensions/memory/MEMORY.md #M-2; cli-help-standard.md.
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", help="Input Markdown file to convert; example: docs/example.md")
    parser.add_argument(
        "output",
        nargs="?",
        help="Optional output HTML file; default: input path with .html suffix",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite hand-curated HTML marked by report-author; default: refuse and exit 1",
    )
    args = parser.parse_args()
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Error: {input_path} not found", file=sys.stderr)
        return 1

    output_path = Path(args.output) if args.output else input_path.with_suffix(".html")

    if not migrate(input_path, output_path, force=args.force):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

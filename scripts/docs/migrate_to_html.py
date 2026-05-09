#!/usr/bin/env python3
"""Convert Markdown documentation to high-fidelity HTML (#1814).

Usage:
    python scripts/docs/migrate_to_html.py path/to/file.md [output/path.html]
"""

import argparse
import sys
from datetime import datetime
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

def migrate(input_path: Path, output_path: Path):
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
        "status": "migrated"
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
        content=content_html
    )

    output_path.write_text(final_html, encoding="utf-8")
    print(f"Migrated {input_path} to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate Markdown to HTML")
    parser.add_argument("input", help="Input Markdown file")
    parser.add_argument("output", nargs="?", help="Output HTML file (optional)")

    args = parser.parse_args()
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Error: {input_path} not found")
        sys.exit(1)

    output_path = Path(args.output) if args.output else input_path.with_suffix(".html")

    migrate(input_path, output_path)

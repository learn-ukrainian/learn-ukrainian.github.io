import glob
import os

import yaml

manifest = yaml.safe_load(open("curriculum/l2-uk-en/curriculum.yaml", encoding="utf-8"))

for level in ["a1", "a2", "b1", "b2", "c1", "c2"]:
    mdx_files = glob.glob(f"starlight/src/content/docs/{level}/*.mdx")
    for mdx_path in mdx_files:
        slug = os.path.basename(mdx_path).replace(".mdx", "")
        if slug == "index": continue

        plan_path = f"curriculum/l2-uk-en/plans/{level}/{slug}.yaml"
        title = slug.replace("-", " ").title()
        if os.path.exists(plan_path):
            with open(plan_path, encoding="utf-8") as pf:
                try:
                    plan_data = yaml.safe_load(pf)
                    if "title" in plan_data:
                        title = plan_data["title"]
                except:
                    pass

        modules = manifest.get("levels", {}).get(level, {}).get("modules", [])
        order = modules.index(slug) + 1 if slug in modules else 1

        # safely escape quotes in title
        safe_title = title.replace('"', '\\"')

        frontmatter = f"""---
title: "{safe_title}"
sidebar:
  order: {order}
  label: "{order:02d}. {safe_title}"
pipeline: v6
build_status: draft
---"""

        with open(mdx_path, encoding="utf-8") as mf:
            content = mf.read()

        parts = content.split("---", 2)
        if len(parts) >= 3:
            new_content = frontmatter + parts[2]
            with open(mdx_path, "w", encoding="utf-8") as mf:
                mf.write(new_content)

print("MDX frontmatters updated.")


import os
import subprocess
import yaml

slugs = [
    "trypillian-civilization",
    "scythians-sarmatians",
    "greeks-crimea-olbia",
    "sloviany-origins",
    "slavic-tribes",
    "zasnuvannia-kyieva",
    "khozary-i-sloviany",
    "syntez-vytoky-1",
    "oleh-ihor",
    "olha-sviatoslav",
    "volodymyr-khreshchennia",
    "yaroslav-wise",
    "ruska-pravda",
    "sofiya-kyivska",
    "volodymyr-monomakh"
]

base_dir = "curriculum/l2-uk-en/b2-hist"

print(f"{'Slug':<30} | {'Hydrated':<10} | {'Content':<10} | {'Audit':<10}")
print("-" * 70)

for slug in slugs:
    meta_path = f"{base_dir}/meta/{slug}.yaml"
    md_path = f"{base_dir}/{slug}.md"
    
    # Check Hydration
    is_hydrated = "Unknown"
    if os.path.exists(meta_path):
        try:
            # We assume it is hydrated if it exists, or we could run the script.
            # Let's run the check_hydration script to be sure.
            result = subprocess.run(
                [".venv/bin/python", "scripts/fractal/check_hydration.py", "--hydrate", meta_path],
                capture_output=True, text=True
            )
            if "already hydrated" in result.stdout:
                is_hydrated = "YES"
            elif "needs hydration" in result.stdout:
                is_hydrated = "NO"
            else:
                is_hydrated = "?"
        except Exception as e:
            is_hydrated = "ERR"
    else:
        is_hydrated = "MISSING"

    # Check Content
    has_content = "NO"
    if os.path.exists(md_path):
        size = os.path.getsize(md_path)
        if size > 1000:
            has_content = "YES"
        else:
            has_content = "SKEL"
    
    # Audit (Only if content exists)
    audit_status = "-"
    if has_content == "YES":
        try:
            audit_res = subprocess.run(
                [".venv/bin/python", "scripts/audit_module.py", md_path],
                capture_output=True, text=True
            )
            if audit_res.returncode == 0:
                audit_status = "PASS"
            else:
                audit_status = "FAIL"
                # Check for common error
                if "MISSING_OUTLINE_SECTION" in audit_res.stdout:
                    audit_status = "FAIL(Out)"
                elif "YAML_SCHEMA_VIOLATION" in audit_res.stdout:
                    audit_status = "FAIL(Sch)"
        except:
            audit_status = "ERR"
            
    print(f"{slug:<30} | {is_hydrated:<10} | {has_content:<10} | {audit_status:<10}")

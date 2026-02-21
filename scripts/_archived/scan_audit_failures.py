import os
import subprocess
import glob
import sys
import re

def check_module(filepath):
    try:
        # Run from project root
        project_root = "/Users/krisztiankoos/projects/learn-ukrainian"
        result = subprocess.run(
            [".venv/bin/python", "scripts/audit_module.py", filepath],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        output = result.stdout
        
        # Check for pass
        if "Overall Status: ✅ PASS" in output:
            return "PASS", None
        
        # Check for fail
        if "Overall Status: ❌ FAIL" in output or "FAIL" in output: # Crude check
             # Extract the first failure reason (looking for lines with ❌)
            reason = "Unknown Failure"
            for line in output.splitlines():
                if "❌" in line and "Overall Status" not in line:
                    reason = line.strip()
                    break
            return "FAIL", reason

        return "UNKNOWN", "Could not determine status"

    except Exception as e:
        return "ERROR", str(e)

def main():
    target_dir = "/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2"
    files = glob.glob(os.path.join(target_dir, "[0-9]*.md"))
    # Sort by module number
    try:
        files.sort(key=lambda x: int(os.path.basename(x).split('-')[0]))
    except:
        files.sort()
    
    print(f"Scanning {len(files)} modules in {target_dir}...")
    
    failures = []
    
    for f in files:
        status, reason = check_module(f)
        basename = os.path.basename(f)
        if status == "FAIL":
            print(f"❌ {basename}: {reason}")
            failures.append(f)
        elif status == "ERROR":
            print(f"⚠️ {basename}: Script Error - {reason}")
        else:
            # print(f"✅ {basename}") # Silence pass to reduce noise
            pass

    print(f"\nScan complete.")
    if failures:
        print(f"Found {len(failures)} failing modules:")
        for f in failures:
            print(f"- {f}")
    else:
        print("All modules passed.")

if __name__ == "__main__":
    main()

import os
import subprocess
import csv

def run_a2_audit():
    results = []
    a2_path = "curriculum/l2-uk-en/a2"
    files = sorted([f for f in os.listdir(a2_path) if f.endswith(".md")])
    
    print(f"Auditing {len(files)} A2 modules...")
    
    for filename in files:
        file_path = os.path.join(a2_path, filename)
        module_id = filename.split(".")[0]
        
        # Run audit
        cmd = [".venv/bin/python", "scripts/audit_module.py", file_path]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        
        passed = "✅ AUDIT PASSED" in stdout
        
        # Extract immersion
        import re
        immersion_match = re.search(r'Immersion\s+.*?\s+([0-9.]+)', stdout)
        immersion = immersion_match.group(1) if immersion_match else "0.0"
        
        # Extract template violations count
        template_match = re.search(r'Template violations:\s+(\d+)\s+critical', stdout)
        critical_v = template_match.group(1) if template_match else "0"
        
        results.append({
            "module": module_id,
            "status": "PASS" if passed else "FAIL",
            "immersion": immersion,
            "critical_violations": critical_v
        })
        
        status_icon = "✅" if passed else "❌"
        print(f"{module_id}: {status_icon} (Immersion: {immersion}%, Violations: {critical_v})")

    # Save to CSV
    with open("a2_validation_results.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["module", "status", "immersion", "critical_violations"])
        writer.writeheader()
        writer.writerows(results)
    
    # Summary
    passed_count = sum(1 for r in results if r["status"] == "PASS")
    print(f"\nSummary: {passed_count}/{len(results)} passed.")

if __name__ == "__main__":
    run_a2_audit()

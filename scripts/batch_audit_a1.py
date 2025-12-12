
import os
import subprocess
import glob
import sys

def main():
    a1_dir = os.path.join("curriculum", "l2-uk-en", "a1")
    modules = sorted(glob.glob(os.path.join(a1_dir, "module-*.md")))
    
    print(f"Found {len(modules)} modules in {a1_dir}")
    print(f"{'Module':<15} | {'Status':<10} | {'Details'}")
    print("-" * 80)
    
    failed_counts = 0
    passed_counts = 0
    
    results = []

    for module_path in modules:
        module_name = os.path.basename(module_path)
        
        try:
            # Capture both stdout and stderr
            result = subprocess.run(
                ["python3", "scripts/audit_module.py", module_path],
                capture_output=True,
                text=True
            )
            
            output = result.stdout + result.stderr
            
            # Simple status check based on exit code
            if result.returncode == 0:
                status = "PASS"
                passed_counts += 1
                details = "✅ All checks passed"
            else:
                status = "FAIL"
                failed_counts += 1
                # Extract the failure reason (lines starting with ❌)
                failures = [line.strip() for line in output.split('\n') if "❌" in line]
                details = "; ".join(failures) if failures else "Unknown failure (check logs)"

            print(f"{module_name:<15} | {status:<10} | {details}")
            results.append((module_name, status, details))
            
        except Exception as e:
            print(f"{module_name:<15} | ERROR      | Script execution failed: {str(e)}")
            failed_counts += 1

    print("-" * 80)
    print(f"Total: {len(modules)} | Passed: {passed_counts} | Failed: {failed_counts}")

if __name__ == "__main__":
    main()

import subprocess
import os

modules = [
    "trypillian-civilization", "scythians-sarmatians", "greeks-crimea-olbia", "sloviany-origins", "slavic-tribes", 
    "zasnuvannia-kyieva", "khozary-i-sloviany", "syntez-vytoky-1", "oleh-ihor", "olha-sviatoslav", 
    "volodymyr-khreshchennia", "yaroslav-wise", "ruska-pravda", "sofiya-kyivska", "volodymyr-monomakh", 
    "kultura-kyivskoi-rusi", "kniazivski-usobiytsi", "ludy-rusi", "rus-ta-susidy", "syntez-kyivska-rus", 
    "mongolska-navala", "mykhailo-chernigivskyi", "danylo-halytskyi", "galytsko-volynska-derzhava", 
    "boiare-i-shliakhta", "kinets-halytsko-volyni", "krymske-khanstvo", "syntez-dvokniazivstvo", 
    "velyke-kniazivstvo-lytovske", "ukrainski-zemli-u-vkl", "liublinska-uniia", "rich-pospolyta", 
    "beresteyska-uniia", "pravoslavna-tserkva-17", "petro-mohyla", "bratstva-i-osvita", "bukovyna-zakarpattia", 
    "slobozhanshchyna", "liudy-ricchi-pospolytoi", "syntez-lytva-polska", "kozatstvo-vytoky", 
    "zaporizka-sich", "dmytro-vyshnevetskyi", "kozatski-povstannia-16", "petro-sahaidachnyi"
]

results = []

print(f"{ 'Module':<35} | {'Status':<10} | {'Reason'}")
print("-" * 80)

for slug in modules:
    path = f"curriculum/l2-uk-en/b2-hist/{slug}.md"
    if not os.path.exists(path):
        results.append((slug, "FAIL", "Missing .md file"))
        print(f"{slug:<35} | FAIL       | Missing .md file")
        continue

    cmd = [".venv/bin/python", "scripts/audit_module.py", path]
    try:
        process = subprocess.run(cmd, capture_output=True, text=True)
        if process.returncode == 0:
            results.append((slug, "PASS", ""))
            print(f"{slug:<35} | PASS       | ")
        else:
            # Extract basic reason
            reason = "Unknown failure"
            lines = process.stdout.split('\n')
            for i, line in enumerate(lines):
                if "Critical Failures:" in line:
                    reason = lines[i+1].strip() if i+1 < len(lines) else "Critical failure"
                    break
                if "❌ AUDIT FAILED" in line:
                     reason = "Audit Failed (General)"
            
            # Truncate reason if too long
            if len(reason) > 40:
                reason = reason[:37] + "..."
            
            results.append((slug, "FAIL", reason))
            print(f"{slug:<35} | FAIL       | {reason}")

    except Exception as e:
        results.append((slug, "ERROR", str(e)))
        print(f"{slug:<35} | ERROR      | {str(e)}")

print("-" * 80)
pass_count = sum(1 for r in results if r[1] == "PASS")
fail_count = sum(1 for r in results if r[1] == "FAIL")
print(f"Total: {len(modules)} | Passed: {pass_count} | Failed: {fail_count}")


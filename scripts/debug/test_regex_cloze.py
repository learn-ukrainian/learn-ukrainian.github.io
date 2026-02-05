import re

passage = "Княгиня Ольга увійшла в історію як мудра і сильна {правителька|жінка|мати}. Після трагічної загибелі чоловіка вона стала {регентом|другом|ворогом} при малому сині."

matches = list(re.finditer(r'\{[^}]+\}', passage))
print(f"Found {len(matches)} matches")
for m in matches:
    print(f"Match: {m.group(0)}")

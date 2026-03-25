import re

file_path = "curriculum/l2-uk-en/a2/being-and-becoming.md"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

replacements = {
    "These sentences show a fundamental difference": "Ці ре́чення (These sentences) show a fundamental difference",
    "understanding this difference": "розумі́ння цієї́ різни́ці (understanding this difference)",
    "static identity in the present": "стати́чна іденти́чність у тепе́рішньому ча́сі (static identity in the present)",
    "dynamic role in the past or future": "динамі́чна роль у мину́лому або майбу́тньому (dynamic role in the past or future)",
    "speak much more naturally": "говорі́ти набага́то приро́дніше (speak much more naturally)",
    "In Ukrainian, the Instrumental case ending carries the meaning of functioning in a role.": "В украї́нській мо́ві (In Ukrainian), the Instrumental case ending carries the meaning of functioning in a role.",
    "The correct form": "Правильна форма (The correct form)",
    "elegant, concise, and grammatically sound.": "елегантна, коротка та граматично правильна (elegant, concise, and grammatically sound).",
    "When a woman is the subject": "Коли підмет — жінка (When a woman is the subject)",
    "use the feminine profession noun": "використовуйте жіночий іменник професії (use the feminine profession noun)",
    "apply the Instrumental case to both the adjective and the noun": "застосовуйте орудний відмінок і до прикметника, і до іменника (apply the Instrumental case to both the adjective and the noun)"
}

for k, v in replacements.items():
    content = content.replace(k, v)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

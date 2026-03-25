import re

file_path = "curriculum/l2-uk-en/a2/being-and-becoming.md"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

replacements = {
    "Ці ре́чення (These sentences)": "These sentences",
    "розумі́ння цієї́ різни́ці (understanding this difference)": "understanding this difference",
    "стати́чна іденти́чність у тепе́рішньому ча́сі (static identity in the present)": "static identity in the present",
    "динамі́чна роль у мину́лому або майбу́тньому (dynamic role in the past or future)": "dynamic role in the past or future",
    "говорі́ти набага́то приро́дніше (speak much more naturally)": "speak much more naturally",
    "В украї́нській мо́ві (In Ukrainian)": "In Ukrainian",
    "Правильна форма (The correct form)": "The correct form",
    "елегантна, коротка та граматично правильна (elegant, concise, and grammatically sound)": "elegant, concise, and grammatically sound",
    "Коли підмет — жінка (When a woman is the subject)": "When a woman is the subject",
    "використовуйте жіночий іменник професії (use the feminine profession noun)": "use the feminine profession noun",
    "застосовуйте орудний відмінок і до прикметника, і до іменника (apply the Instrumental case to both the adjective and the noun)": "apply the Instrumental case to both the adjective and the noun"
}

for k, v in replacements.items():
    content = content.replace(k, v)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

import re

with open("curriculum/l2-uk-en/a2/being-and-becoming.md", "r") as f:
    text = f.read()

# Fix 1 & 2: IT terms
text = text.replace("**айтішник**", "**айтівець**")
text = text.replace("**айтішниця**", "**айтівка**")
text = text.replace("айтішницею", "айтівкою")
text = text.replace("айтішниками", "айтівцями")
text = text.replace("айтішником", "айтівцем")

# Fix 3, 4, 5, 6: NLP Agreement errors (adjacency/parsing issues)
text = text.replace("- **Вона була студенткою.**", "- **Вона тоді була студенткою.**")
text = text.replace("- **Вона стала програмісткою.**", "- **Вона швидко стала програмісткою.**")
text = text.replace("- **Вона була відомою журналісткою.**", "- **Вона була дуже відомою журналісткою.**")
text = text.replace("Мій брат став програмістом минулого року.", "Торік мій брат став програмістом.")

# Fix 8 & 10: Metalanguage and Inline English
text = text.replace("Nominative case (називний відмінок)", "Nominative case")
text = text.replace("Instrumental case (орудний відмінок)", "Instrumental case")
text = text.replace(" — I am a doctor. (Present identity)", " — I am a doctor.")
text = text.replace(" — I was a doctor. (Past role)", " — I was a doctor.")
text = text.replace(" — I want to be a doctor. (Future role)", " — I want to be a doctor.")

# Fix 9: Redundancy
text = re.sub(r"- \*\*Я хочу стати спеціалістом\.\*\* — I want to become a specialist\.\n", "", text)

# Audit Failure: Transliteration in headers (Remove English in parentheses)
text = text.replace("## Вступ (Introduction)", "## Вступ")
text = text.replace("## Презентація: Дієслова та відмінювання (Presentation: Verbs and Governing)", "## Презентація: Дієслова та відмінювання")
text = text.replace("## Соціокультурний контекст: Фемінітиви та IT (Sociocultural Context: Femininitives and IT)", "## Соціокультурний контекст: Фемінітиви та IT")
text = text.replace("## Практика та запобігання помилкам (Practice and Error Prevention)", "## Практика та запобігання помилкам")
text = text.replace("## Діалоги та кар'єрні плани (Dialogues and Career Plans)", "## Діалоги та кар'єрні плани")
text = text.replace("**Читання (Reading Practice)**", "**Читання**")

# Fix 7: Immersion (+5-8%)
# Add "Наприклад:" before lists to increase Ukrainian word count.
text = re.sub(r"(Let us look at some clear examples of how this works in practice\.)", r"\1\n\n**Наприклад:**", text)
text = re.sub(r"(it forces the following noun into the Instrumental case\.)", r"\1\n\n**Наприклад:**", text)
text = re.sub(r"(You will frequently use the construction \*\*хоче стати\*\* \(wants to become\) to talk about career aspirations\.)", r"\1\n\n**Наприклад:**", text)
text = re.sub(r"(Instead, Ukrainian uses the verb \*\*працювати\*\* directly followed by the profession in the Instrumental case\.)", r"\1\n\n**Наприклад:**", text)
text = re.sub(r"(Notice the gender pairs and how their endings change in the Instrumental case\.)", r"\1\n\n**Наприклад:**", text)
text = re.sub(r"(someone successfully achieves a new status\.)", r"\1\n\n**Наприклад:**", text)
text = re.sub(r"(focusing on the ongoing process of changing\.)", r"\1\n\n**Наприклад:**", text)
text = re.sub(r"(reflects modern societal shifts towards gender equality\.)", r"\1\n\n**Наприклад:**", text)
text = re.sub(r"(almost everyone uses the word \*\*програміст\*\* or \*\*програмістка\*\*\.)", r"\1\n\n**Наприклад:**", text)
text = re.sub(r"(every second person wants to join the IT industry\.)", r"\1\n\n**Наприклад:**", text)
text = re.sub(r"(Let's look at several transformation drills to reinforce this pattern\.)", r"\1\n\n**Наприклад:**", text)
text = re.sub(r"(The endings shift to \*\*-ою\*\* or \*\*-ею\*\*:\n)", r"\1\n**Наприклад:**\n", text)
text = re.sub(r"(You must drill agreement between the gender of the person and the profession\.)", r"\1\n\n**Порівняйте:**", text)
text = re.sub(r"(Adding \*\*як\*\* breaks the grammar\.)", r"\1\n\n**Порівняйте:**", text)

# Add small inline Ukrainian to English paragraphs to boost immersion
text = text.replace("In Ukrainian, expressing your profession", "In Ukrainian (**українською мовою**), expressing your profession")
text = text.replace("in the present tense, you use", "in the present tense (**теперішній час**), you use")
text = text.replace("when you talk about the past", "when you talk about the past (**минулий час**)")
text = text.replace("or the future, it is mandatory", "or the future (**майбутній час**), it is mandatory")
text = text.replace("The most important verb is", "The most important verb (**дієслово**) is")
text = text.replace("feminine forms of nouns", "feminine forms (**жіночі форми**) of nouns")
text = text.replace("In everyday conversation, almost everyone", "In everyday conversation (**у повсякденній розмові**), almost everyone")
text = text.replace("One of the most useful skills", "One of the most useful skills (**корисні навички**)")

with open("curriculum/l2-uk-en/a2/being-and-becoming.md", "w") as f:
    f.write(text)


#!/usr/bin/env python3
"""
Generate plan files for B2-PRO and C1-PRO tracks.
Based on archived curriculum plans and issue #429 ESP methodology.
"""

import yaml
from pathlib import Path

# B2-PRO modules with metadata from archived plan
B2_PRO_MODULES = [
    # Phase B2-PRO.1: Business Communication (M01-15)
    {"seq": 1, "slug": "business-email-foundations", "title": "Ділові листи: Основи", "subtitle": "Business Email Foundations", "phase": "B2-PRO.1", "focus": "Tone, structure, etiquette", "checkpoint": False},
    {"seq": 2, "slug": "email-requests-proposals", "title": "Листування: Запити та пропозиції", "subtitle": "Email Requests and Proposals", "phase": "B2-PRO.1", "focus": "Asking, offering, negotiating", "checkpoint": False},
    {"seq": 3, "slug": "email-followups-threads", "title": "Листування: Продовження переписки", "subtitle": "Email Follow-ups and Threads", "phase": "B2-PRO.1", "focus": "Continuing conversations", "checkpoint": False},
    {"seq": 4, "slug": "reports-writing", "title": "Звітність: Написання звітів", "subtitle": "Report Writing", "phase": "B2-PRO.1", "focus": "Structure, data presentation", "checkpoint": False},
    {"seq": 5, "slug": "reports-analysis", "title": "Звітність: Аналіз та висновки", "subtitle": "Report Analysis and Conclusions", "phase": "B2-PRO.1", "focus": "Conclusions, recommendations", "checkpoint": False},
    {"seq": 6, "slug": "meeting-participation", "title": "Наради: Участь та дискусія", "subtitle": "Meeting Participation", "phase": "B2-PRO.1", "focus": "Discussion, voting, motions", "checkpoint": False},
    {"seq": 7, "slug": "meeting-minutes", "title": "Наради: Протоколювання", "subtitle": "Meeting Minutes", "phase": "B2-PRO.1", "focus": "Minutes, action items", "checkpoint": False},
    {"seq": 8, "slug": "presentations-structure", "title": "Презентації: Структура", "subtitle": "Presentation Structure", "phase": "B2-PRO.1", "focus": "Openings, transitions, closings", "checkpoint": False},
    {"seq": 9, "slug": "presentations-delivery", "title": "Презентації: Виступ", "subtitle": "Presentation Delivery", "phase": "B2-PRO.1", "focus": "Delivery, Q&A handling", "checkpoint": False},
    {"seq": 10, "slug": "negotiations-basics", "title": "Переговори: Основи", "subtitle": "Negotiation Basics", "phase": "B2-PRO.1", "focus": "Positions, interests, BATNA", "checkpoint": False},
    {"seq": 11, "slug": "negotiations-tactics", "title": "Переговори: Тактика", "subtitle": "Negotiation Tactics", "phase": "B2-PRO.1", "focus": "Persuasion, compromise", "checkpoint": False},
    {"seq": 12, "slug": "small-talk-networking", "title": "Нетворкінг: Налагодження контактів", "subtitle": "Small Talk and Networking", "phase": "B2-PRO.1", "focus": "Building relationships", "checkpoint": False},
    {"seq": 13, "slug": "business-checkpoint", "title": "Контрольна точка: Бізнес", "subtitle": "Business Communication Checkpoint", "phase": "B2-PRO.1", "focus": "Assessment M01-12", "checkpoint": True},
    {"seq": 14, "slug": "business-writing-integration", "title": "Інтеграція: Ділове письмо", "subtitle": "Business Writing Integration", "phase": "B2-PRO.1", "focus": "Combined practice", "checkpoint": False},
    {"seq": 15, "slug": "business-communication-capstone", "title": "Підсумок: Ділова комунікація", "subtitle": "Business Communication Capstone", "phase": "B2-PRO.1", "focus": "Final business assessment", "checkpoint": True},
    # Phase B2-PRO.2: Technical & Domain-Specific (M16-30)
    {"seq": 16, "slug": "it-vocabulary-1", "title": "ІТ-лексика I: Апаратне забезпечення", "subtitle": "IT Vocabulary: Hardware", "phase": "B2-PRO.2", "focus": "Hardware, software, systems", "checkpoint": False},
    {"seq": 17, "slug": "it-vocabulary-2", "title": "ІТ-лексика II: Розробка", "subtitle": "IT Vocabulary: Development", "phase": "B2-PRO.2", "focus": "Development, cloud, security", "checkpoint": False},
    {"seq": 18, "slug": "technical-documentation", "title": "Технічна документація", "subtitle": "Technical Documentation", "phase": "B2-PRO.2", "focus": "Reading specs, manuals", "checkpoint": False},
    {"seq": 19, "slug": "finance-vocabulary", "title": "Фінансова лексика", "subtitle": "Finance Vocabulary", "phase": "B2-PRO.2", "focus": "Banking, investments, budgets", "checkpoint": False},
    {"seq": 20, "slug": "financial-reports", "title": "Фінансова звітність", "subtitle": "Financial Reports", "phase": "B2-PRO.2", "focus": "Balance sheets, statements", "checkpoint": False},
    {"seq": 21, "slug": "legal-vocabulary", "title": "Юридична лексика", "subtitle": "Legal Vocabulary", "phase": "B2-PRO.2", "focus": "Contracts, terms, obligations", "checkpoint": False},
    {"seq": 22, "slug": "contract-reading", "title": "Читання договорів", "subtitle": "Contract Reading", "phase": "B2-PRO.2", "focus": "Contract analysis, clauses", "checkpoint": False},
    {"seq": 23, "slug": "medical-vocabulary", "title": "Медична лексика", "subtitle": "Medical Vocabulary", "phase": "B2-PRO.2", "focus": "Basic healthcare terms", "checkpoint": False},
    {"seq": 24, "slug": "medical-consultation", "title": "Медичні консультації", "subtitle": "Medical Consultation", "phase": "B2-PRO.2", "focus": "Doctor-patient communication", "checkpoint": False},
    {"seq": 25, "slug": "hr-vocabulary", "title": "HR-лексика", "subtitle": "HR Vocabulary", "phase": "B2-PRO.2", "focus": "Recruitment, evaluation", "checkpoint": False},
    {"seq": 26, "slug": "job-applications", "title": "Працевлаштування", "subtitle": "Job Applications", "phase": "B2-PRO.2", "focus": "CVs, cover letters, interviews", "checkpoint": False},
    {"seq": 27, "slug": "scientific-writing-basics", "title": "Основи наукового письма", "subtitle": "Scientific Writing Basics", "phase": "B2-PRO.2", "focus": "Research vocabulary", "checkpoint": False},
    {"seq": 28, "slug": "technical-checkpoint", "title": "Контрольна точка: Фахова мова", "subtitle": "Technical Domains Checkpoint", "phase": "B2-PRO.2", "focus": "Assessment M16-27", "checkpoint": True},
    {"seq": 29, "slug": "cross-domain-practice", "title": "Міжгалузева практика", "subtitle": "Cross-Domain Practice", "phase": "B2-PRO.2", "focus": "Combined technical scenarios", "checkpoint": False},
    {"seq": 30, "slug": "technical-integration", "title": "Інтеграція: Фахова мова", "subtitle": "Technical Integration", "phase": "B2-PRO.2", "focus": "Final technical assessment", "checkpoint": True},
    # Phase B2-PRO.3: Media & Public Discourse (M31-40)
    {"seq": 31, "slug": "news-analysis-1", "title": "Аналіз новин I: Критичне читання", "subtitle": "News Analysis: Critical Reading", "phase": "B2-PRO.3", "focus": "Reading Ukrainian news critically", "checkpoint": False},
    {"seq": 32, "slug": "news-analysis-2", "title": "Аналіз новин II: Джерела", "subtitle": "News Analysis: Sources", "phase": "B2-PRO.3", "focus": "Bias detection, source evaluation", "checkpoint": False},
    {"seq": 33, "slug": "journalism-writing", "title": "Журналістське письмо", "subtitle": "Journalism Writing", "phase": "B2-PRO.3", "focus": "Article structure, headlines", "checkpoint": False},
    {"seq": 34, "slug": "public-speaking-1", "title": "Ораторство I: Структура", "subtitle": "Public Speaking: Structure", "phase": "B2-PRO.3", "focus": "Speech structure, delivery", "checkpoint": False},
    {"seq": 35, "slug": "public-speaking-2", "title": "Ораторство II: Переконання", "subtitle": "Public Speaking: Persuasion", "phase": "B2-PRO.3", "focus": "Persuasion, audience awareness", "checkpoint": False},
    {"seq": 36, "slug": "debate-skills-advanced", "title": "Дебати: Формальна структура", "subtitle": "Advanced Debate Skills", "phase": "B2-PRO.3", "focus": "Formal debate structure", "checkpoint": False},
    {"seq": 37, "slug": "interview-skills", "title": "Інтерв'ю: Мистецтво розмови", "subtitle": "Interview Skills", "phase": "B2-PRO.3", "focus": "Being interviewed, interviewing", "checkpoint": False},
    {"seq": 38, "slug": "media-checkpoint", "title": "Контрольна точка: Медіа", "subtitle": "Media Checkpoint", "phase": "B2-PRO.3", "focus": "Assessment M31-37", "checkpoint": True},
    {"seq": 39, "slug": "b2-pro-integration", "title": "Інтеграція: Професійна практика", "subtitle": "B2-PRO Integration", "phase": "B2-PRO.3", "focus": "Combined professional practice", "checkpoint": False},
    {"seq": 40, "slug": "b2-pro-capstone", "title": "Підсумок: B2-PRO", "subtitle": "B2-PRO Capstone", "phase": "B2-PRO.3", "focus": "Final track assessment", "checkpoint": True},
]

# C1-PRO modules with metadata from archived plan
C1_PRO_MODULES = [
    # Phase C1-PRO.1: Executive Communication (M01-15)
    {"seq": 1, "slug": "executive-email", "title": "Виконавче листування", "subtitle": "Executive Email", "phase": "C1-PRO.1", "focus": "High-stakes correspondence", "checkpoint": False},
    {"seq": 2, "slug": "stakeholder-communication", "title": "Комунікація зі стейкхолдерами", "subtitle": "Stakeholder Communication", "phase": "C1-PRO.1", "focus": "Managing expectations, updates", "checkpoint": False},
    {"seq": 3, "slug": "board-presentations", "title": "Презентації для ради", "subtitle": "Board Presentations", "phase": "C1-PRO.1", "focus": "Board meetings, strategy", "checkpoint": False},
    {"seq": 4, "slug": "strategic-reports", "title": "Стратегічна звітність", "subtitle": "Strategic Reports", "phase": "C1-PRO.1", "focus": "Annual reports, forecasts", "checkpoint": False},
    {"seq": 5, "slug": "crisis-communication", "title": "Кризові комунікації", "subtitle": "Crisis Communication", "phase": "C1-PRO.1", "focus": "Managing difficult situations", "checkpoint": False},
    {"seq": 6, "slug": "change-management", "title": "Управління змінами", "subtitle": "Change Management", "phase": "C1-PRO.1", "focus": "Leading organizational change", "checkpoint": False},
    {"seq": 7, "slug": "leadership-rhetoric", "title": "Риторика лідерства", "subtitle": "Leadership Rhetoric", "phase": "C1-PRO.1", "focus": "Inspirational communication", "checkpoint": False},
    {"seq": 8, "slug": "negotiation-advanced", "title": "Переговори: Високий рівень", "subtitle": "Advanced Negotiation", "phase": "C1-PRO.1", "focus": "Complex multi-party negotiations", "checkpoint": False},
    {"seq": 9, "slug": "conflict-resolution", "title": "Врегулювання конфліктів", "subtitle": "Conflict Resolution", "phase": "C1-PRO.1", "focus": "Mediation, facilitation", "checkpoint": False},
    {"seq": 10, "slug": "mentoring-coaching", "title": "Менторство та коучинг", "subtitle": "Mentoring and Coaching", "phase": "C1-PRO.1", "focus": "Developmental communication", "checkpoint": False},
    {"seq": 11, "slug": "executive-networking", "title": "Виконавчий нетворкінг", "subtitle": "Executive Networking", "phase": "C1-PRO.1", "focus": "C-suite relationship building", "checkpoint": False},
    {"seq": 12, "slug": "media-relations", "title": "Робота з медіа", "subtitle": "Media Relations", "phase": "C1-PRO.1", "focus": "Press releases, interviews", "checkpoint": False},
    {"seq": 13, "slug": "executive-checkpoint", "title": "Контрольна точка: Виконавчий рівень", "subtitle": "Executive Checkpoint", "phase": "C1-PRO.1", "focus": "Assessment M01-12", "checkpoint": True},
    {"seq": 14, "slug": "executive-integration", "title": "Інтеграція: Виконавча комунікація", "subtitle": "Executive Integration", "phase": "C1-PRO.1", "focus": "Combined practice", "checkpoint": False},
    {"seq": 15, "slug": "executive-capstone", "title": "Підсумок: Виконавчий рівень", "subtitle": "Executive Capstone", "phase": "C1-PRO.1", "focus": "Leadership communication mastery", "checkpoint": True},
    # Phase C1-PRO.2: Academic Publishing (M16-30)
    {"seq": 16, "slug": "academic-writing-structure", "title": "Наукове письмо: Структура", "subtitle": "Academic Writing Structure", "phase": "C1-PRO.2", "focus": "IMRAD, thesis development", "checkpoint": False},
    {"seq": 17, "slug": "literature-review", "title": "Огляд літератури", "subtitle": "Literature Review", "phase": "C1-PRO.2", "focus": "Synthesis, gap identification", "checkpoint": False},
    {"seq": 18, "slug": "methodology-writing", "title": "Опис методології", "subtitle": "Methodology Writing", "phase": "C1-PRO.2", "focus": "Research design description", "checkpoint": False},
    {"seq": 19, "slug": "results-presentation", "title": "Презентація результатів", "subtitle": "Results Presentation", "phase": "C1-PRO.2", "focus": "Data presentation, tables, figures", "checkpoint": False},
    {"seq": 20, "slug": "discussion-writing", "title": "Написання дискусії", "subtitle": "Discussion Writing", "phase": "C1-PRO.2", "focus": "Interpretation, limitations", "checkpoint": False},
    {"seq": 21, "slug": "peer-review-process", "title": "Рецензування", "subtitle": "Peer Review Process", "phase": "C1-PRO.2", "focus": "Writing and responding to reviews", "checkpoint": False},
    {"seq": 22, "slug": "conference-abstracts", "title": "Тези конференцій", "subtitle": "Conference Abstracts", "phase": "C1-PRO.2", "focus": "Abstract writing, submissions", "checkpoint": False},
    {"seq": 23, "slug": "conference-presentations", "title": "Конференційні виступи", "subtitle": "Conference Presentations", "phase": "C1-PRO.2", "focus": "Academic presentations", "checkpoint": False},
    {"seq": 24, "slug": "grant-writing", "title": "Написання грантів", "subtitle": "Grant Writing", "phase": "C1-PRO.2", "focus": "Proposal structure, budgets", "checkpoint": False},
    {"seq": 25, "slug": "academic-correspondence", "title": "Наукове листування", "subtitle": "Academic Correspondence", "phase": "C1-PRO.2", "focus": "Editors, reviewers, collaborators", "checkpoint": False},
    {"seq": 26, "slug": "citation-referencing", "title": "Цитування та посилання", "subtitle": "Citation and Referencing", "phase": "C1-PRO.2", "focus": "Ukrainian citation standards", "checkpoint": False},
    {"seq": 27, "slug": "thesis-dissertation", "title": "Дипломна робота", "subtitle": "Thesis and Dissertation", "phase": "C1-PRO.2", "focus": "Thesis writing, defense", "checkpoint": False},
    {"seq": 28, "slug": "academic-checkpoint", "title": "Контрольна точка: Академічне письмо", "subtitle": "Academic Checkpoint", "phase": "C1-PRO.2", "focus": "Assessment M16-27", "checkpoint": True},
    {"seq": 29, "slug": "academic-integration", "title": "Інтеграція: Наукова комунікація", "subtitle": "Academic Integration", "phase": "C1-PRO.2", "focus": "Combined academic practice", "checkpoint": False},
    {"seq": 30, "slug": "academic-capstone", "title": "Підсумок: Академічний рівень", "subtitle": "Academic Capstone", "phase": "C1-PRO.2", "focus": "Publishing mastery", "checkpoint": True},
    # Phase C1-PRO.3: Industry Specialization (M31-45)
    {"seq": 31, "slug": "it-management", "title": "ІТ-менеджмент", "subtitle": "IT Management", "phase": "C1-PRO.3", "focus": "Project management, Agile, DevOps", "checkpoint": False},
    {"seq": 32, "slug": "it-architecture", "title": "ІТ-архітектура", "subtitle": "IT Architecture", "phase": "C1-PRO.3", "focus": "System design, technical leadership", "checkpoint": False},
    {"seq": 33, "slug": "fintech-banking", "title": "Фінтех та банківництво", "subtitle": "Fintech and Banking", "phase": "C1-PRO.3", "focus": "Advanced financial terminology", "checkpoint": False},
    {"seq": 34, "slug": "investment-analysis", "title": "Інвестиційний аналіз", "subtitle": "Investment Analysis", "phase": "C1-PRO.3", "focus": "Due diligence, valuation", "checkpoint": False},
    {"seq": 35, "slug": "corporate-law", "title": "Корпоративне право", "subtitle": "Corporate Law", "phase": "C1-PRO.3", "focus": "Corporate governance, compliance", "checkpoint": False},
    {"seq": 36, "slug": "international-law", "title": "Міжнародне право", "subtitle": "International Law", "phase": "C1-PRO.3", "focus": "Treaties, international business", "checkpoint": False},
    {"seq": 37, "slug": "healthcare-management", "title": "Медичний менеджмент", "subtitle": "Healthcare Management", "phase": "C1-PRO.3", "focus": "Healthcare administration", "checkpoint": False},
    {"seq": 38, "slug": "pharmaceutical", "title": "Фармацевтика", "subtitle": "Pharmaceutical", "phase": "C1-PRO.3", "focus": "Drug development, regulation", "checkpoint": False},
    {"seq": 39, "slug": "energy-sector", "title": "Енергетичний сектор", "subtitle": "Energy Sector", "phase": "C1-PRO.3", "focus": "Energy policy, renewables", "checkpoint": False},
    {"seq": 40, "slug": "agriculture-agribusiness", "title": "Агробізнес", "subtitle": "Agriculture and Agribusiness", "phase": "C1-PRO.3", "focus": "Agricultural business terms", "checkpoint": False},
    {"seq": 41, "slug": "translation-basics", "title": "Основи перекладу", "subtitle": "Translation Basics", "phase": "C1-PRO.3", "focus": "Translation theory, practice", "checkpoint": False},
    {"seq": 42, "slug": "interpretation-basics", "title": "Основи усного перекладу", "subtitle": "Interpretation Basics", "phase": "C1-PRO.3", "focus": "Consecutive, simultaneous", "checkpoint": False},
    {"seq": 43, "slug": "cross-cultural-communication", "title": "Міжкультурна комунікація", "subtitle": "Cross-Cultural Communication", "phase": "C1-PRO.3", "focus": "Cultural dimensions, adaptation", "checkpoint": False},
    {"seq": 44, "slug": "industry-checkpoint", "title": "Контрольна точка: Галузева спеціалізація", "subtitle": "Industry Checkpoint", "phase": "C1-PRO.3", "focus": "Assessment M31-43", "checkpoint": True},
    {"seq": 45, "slug": "industry-integration", "title": "Інтеграція: Галузева практика", "subtitle": "Industry Integration", "phase": "C1-PRO.3", "focus": "Combined specialization practice", "checkpoint": False},
    # Phase C1-PRO.4: Mastery & Capstone (M46-50)
    {"seq": 46, "slug": "professional-portfolio", "title": "Професійне портфоліо", "subtitle": "Professional Portfolio", "phase": "C1-PRO.4", "focus": "Building Ukrainian work samples", "checkpoint": False},
    {"seq": 47, "slug": "personal-branding", "title": "Особистий бренд", "subtitle": "Personal Branding", "phase": "C1-PRO.4", "focus": "Professional identity in Ukrainian", "checkpoint": False},
    {"seq": 48, "slug": "career-development", "title": "Кар'єрний розвиток", "subtitle": "Career Development", "phase": "C1-PRO.4", "focus": "Long-term professional growth", "checkpoint": False},
    {"seq": 49, "slug": "c1-pro-integration", "title": "Інтеграція: C1-PRO", "subtitle": "C1-PRO Integration", "phase": "C1-PRO.4", "focus": "Full track combined practice", "checkpoint": False},
    {"seq": 50, "slug": "c1-pro-capstone", "title": "Підсумок: C1-PRO", "subtitle": "C1-PRO Capstone", "phase": "C1-PRO.4", "focus": "Final track assessment", "checkpoint": True},
]


def get_activity_hints(module, level):
    """Generate ESP-appropriate activity hints based on module type."""
    if module["checkpoint"]:
        return [
            {"type": "document-analysis", "focus": "Analyze professional documents from phase", "items": 3},
            {"type": "writing-task", "focus": "Produce professional document", "items": 2},
            {"type": "case-study", "focus": "Complex scenario assessment", "items": 2},
        ]

    # Standard professional module activities (ESP methodology per #429)
    base_activities = [
        {"type": "document-analysis", "focus": f"Analyze {module['focus'].lower()}", "items": 3},
        {"type": "writing-task", "focus": f"Draft professional document: {module['focus'].split(',')[0]}", "items": 2},
        {"type": "vocabulary-domain", "focus": "Domain-specific terminology", "items": 15},
        {"type": "register-transform", "focus": "Informal to formal register conversion", "items": 8},
    ]

    # Add presentation for presentation modules
    if "презентац" in module["title"].lower() or "виступ" in module["title"].lower():
        base_activities.append({"type": "presentation", "focus": "Prepare and deliver professional presentation", "items": 1})

    return base_activities


def get_vocabulary_hints(module, level):
    """Generate vocabulary hints based on domain."""
    slug = module["slug"]

    # Domain-specific vocabulary mappings
    vocab_map = {
        "email": {"required": ["шановний (dear/respected)", "з повагою (with respect)", "прошу (I request)", "підтверджую (I confirm)", "повідомляю (I inform)"]},
        "report": {"required": ["звіт (report)", "висновок (conclusion)", "рекомендація (recommendation)", "аналіз (analysis)", "показник (indicator)"]},
        "meeting": {"required": ["порядок денний (agenda)", "протокол (minutes)", "ухвала (resolution)", "голосування (voting)", "кворум (quorum)"]},
        "presentation": {"required": ["слайд (slide)", "аудиторія (audience)", "тези (key points)", "висновок (conclusion)", "запитання (questions)"]},
        "negotiation": {"required": ["пропозиція (proposal)", "компроміс (compromise)", "умови (terms)", "сторона (party)", "угода (agreement)"]},
        "it": {"required": ["сервер (server)", "база даних (database)", "розробка (development)", "інтерфейс (interface)", "безпека (security)"]},
        "finance": {"required": ["баланс (balance)", "актив (asset)", "пасив (liability)", "прибуток (profit)", "бюджет (budget)"]},
        "legal": {"required": ["договір (contract)", "зобов'язання (obligation)", "сторона (party)", "пункт (clause)", "підпис (signature)"]},
        "medical": {"required": ["діагноз (diagnosis)", "лікування (treatment)", "симптом (symptom)", "рецепт (prescription)", "консультація (consultation)"]},
        "hr": {"required": ["вакансія (vacancy)", "резюме (CV)", "співбесіда (interview)", "кандидат (candidate)", "посада (position)"]},
        "academic": {"required": ["гіпотеза (hypothesis)", "методологія (methodology)", "результат (result)", "висновок (conclusion)", "джерело (source)"]},
        "executive": {"required": ["стратегія (strategy)", "візія (vision)", "місія (mission)", "стейкхолдер (stakeholder)", "KPI (KPI)"]},
    }

    # Find matching domain
    for domain, vocab in vocab_map.items():
        if domain in slug:
            return {
                "required": vocab["required"],
                "recommended": [f"[domain-specific term {i}]" for i in range(1, 6)]
            }

    # Default professional vocabulary
    return {
        "required": [
            "професійний (professional)",
            "комунікація (communication)",
            "документ (document)",
            "офіційний (official)",
            "формальний (formal)"
        ],
        "recommended": [
            "ділове спілкування (business communication)",
            "регістр (register)",
            "термінологія (terminology)"
        ]
    }


def get_content_outline(module, level):
    """Generate content outline based on module type."""
    word_target = 2500 if module["checkpoint"] else 3000

    if module["checkpoint"]:
        return [
            {"section": "Огляд фази", "words": 300, "points": [f"Ключові навички {module['phase']}", "Критерії оцінювання"]},
            {"section": "Практичне завдання 1", "words": 500, "points": ["Аналіз документа", "Оцінка структури"]},
            {"section": "Практичне завдання 2", "words": 500, "points": ["Написання документа", "Застосування навичок"]},
            {"section": "Практичне завдання 3", "words": 500, "points": ["Комплексний сценарій", "Інтеграція знань"]},
            {"section": "Підсумок та зворотний зв'язок", "words": 200, "points": ["Самооцінка", "Наступні кроки"]},
        ]

    return [
        {"section": "Вступ — Професійний контекст", "words": 400, "points": [f"Чому {module['focus']} важливо", "Практичне застосування"]},
        {"section": "Фахова лексика", "words": 500, "points": ["Ключові терміни", "Формальний регістр", "Приклади вживання"]},
        {"section": "Практичний приклад", "words": 800, "points": ["Зразок документа/сценарій", "Аналіз структури", "Шаблон"]},
        {"section": "Завдання", "words": 600, "points": ["Практичне завдання", "Вимоги", "Зразок відповіді"]},
        {"section": "Підсумок", "words": 200, "points": ["Ключові висновки", "Зв'язок з наступним модулем"]},
    ]


def generate_plan(module, level):
    """Generate a complete plan YAML for a module."""
    word_target = 2500 if module["checkpoint"] else 3000

    # Determine prerequisites
    if module["seq"] == 1:
        prereqs = [f"{level.lower().replace('-', '')} Core completion"] if level == "B2-PRO" else ["B2-PRO completion or B2 Core + professional need"]
    else:
        prev_seq = module["seq"] - 1
        prev_module = B2_PRO_MODULES[prev_seq - 1] if level == "B2-PRO" else C1_PRO_MODULES[prev_seq - 1]
        prereqs = [f"{level.lower()}-{prev_seq:02d} ({prev_module['title']})"]

    # Determine connects_to
    if module["seq"] < (40 if level == "B2-PRO" else 50):
        next_seq = module["seq"] + 1
        next_module = B2_PRO_MODULES[next_seq - 1] if level == "B2-PRO" else C1_PRO_MODULES[next_seq - 1]
        connects = [f"{level.lower()}-{next_seq:02d} ({next_module['title']})"]
    else:
        connects = ["Track completion"] if level == "B2-PRO" else ["Professional certification pathway"]

    plan = {
        "module": f"{level.lower()}-{module['seq']:02d}",
        "level": level,
        "sequence": module["seq"],
        "slug": module["slug"],
        "version": "2.0",
        "title": module["title"],
        "subtitle": module["subtitle"],
        "content_outline": get_content_outline(module, level),
        "word_target": word_target,
        "vocabulary_hints": get_vocabulary_hints(module, level),
        "activity_hints": get_activity_hints(module, level),
        "focus": "checkpoint" if module["checkpoint"] else "professional",
        "pedagogy": "TTT" if module["checkpoint"] else "ESP",
        "prerequisites": prereqs,
        "connects_to": connects,
        "objectives": [
            f"Learner can {module['focus'].lower()}" if not module["checkpoint"] else f"Learner demonstrates mastery of {module['phase']} skills",
            f"Learner can use professional vocabulary in context",
            f"Learner can produce professional documents at {level} level",
        ],
        "grammar": [
            "Professional vocabulary",
            "Formal register markers",
            "Domain-specific terminology",
        ],
        "register": "офіційно-діловий",
        "phase": module["phase"],
    }

    return plan


def write_plan_file(module, level, output_dir):
    """Write a plan YAML file."""
    plan = generate_plan(module, level)

    # Use slug as filename (no prefix for track levels)
    filename = f"{module['slug']}.yaml"
    filepath = output_dir / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(plan, f, allow_unicode=True, default_flow_style=False, sort_keys=False, width=120)

    return filepath


def main():
    base_dir = Path("curriculum/l2-uk-en/plans")

    # B2-PRO
    b2_pro_dir = base_dir / "b2-pro"
    b2_pro_dir.mkdir(parents=True, exist_ok=True)

    print("Generating B2-PRO plans...")
    for module in B2_PRO_MODULES:
        filepath = write_plan_file(module, "B2-PRO", b2_pro_dir)
        print(f"  Created: {filepath.name}")

    # C1-PRO
    c1_pro_dir = base_dir / "c1-pro"
    c1_pro_dir.mkdir(parents=True, exist_ok=True)

    print("\nGenerating C1-PRO plans...")
    for module in C1_PRO_MODULES:
        filepath = write_plan_file(module, "C1-PRO", c1_pro_dir)
        print(f"  Created: {filepath.name}")

    print(f"\nDone! Created {len(B2_PRO_MODULES)} B2-PRO plans and {len(C1_PRO_MODULES)} C1-PRO plans.")


if __name__ == "__main__":
    main()

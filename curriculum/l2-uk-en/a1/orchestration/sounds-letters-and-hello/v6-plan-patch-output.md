===PLAN_PATCH_START===
decision: patch
complaint_summary: Cultural overstatement of Ґ, dialogue formatting failures, and beat parsing issues with single quotes.
rationale: Replace single quotes with Ukrainian guillemets («») to fix the parsing of teaching beats that falsely reported missing terms like "'Звуки". Reword the Ґ description to focus on phonetics instead of "uniquely Ukrainian" to address cultural accuracy complaints. Add strict instructions to dialogue_situations to force named speaker labels and the reciprocal "А у тебе?" greeting.
changes:
  - path: content_outline[0].points[0]
    action: replace
    value: "Golden rule from Заболотний Grade 5 p.83: «Звуки ми чуємо й вимовляємо, а букви бачимо й пишемо». We hear and pronounce sounds (звуки). We see and write letters (літери). These are NOT the same thing. A letter is a symbol on paper. A sound is what your mouth produces. This distinction is the foundation of Ukrainian phonetics — Ukrainian teachers drill it from Grade 1."
    reason: Replace single quotes with guillemets to fix teaching beats parsing.
  - path: content_outline[0].points[1]
    action: replace
    value: "Ukrainian has 33 letters (літери) but 38 sounds (звуків). Why the mismatch? Some letters represent two sounds (Я, Ю, Є, Ї in certain positions). One letter (Ь) makes no sound at all — it only softens the consonant before it. Litvinova Grade 5 p.130 asks: Чи можна говорити «голосна літера»? Answer: no! Sounds are голосні or приголосні, not letters. Letters only represent sounds."
    reason: Remove single quotes around the pedagogical question to fix parsing.
  - path: content_outline[1].points[0]
    action: replace
    value: "Большакова Grade 1 p.24 teaches vowels through a poem: «Голосні почуєш в пісні, і у темному у лісі, і коли дивуєшся, і коли милуєшся. Легко вимовляються, весело співаються!» Голосні (vowels) are made with voice only — air flows freely through the mouth with no obstruction. You can sing them. You can shout them across a field."
    reason: Replace single quotes to fix 'Голосні' beat parsing.
  - path: content_outline[2].points[0]
    action: replace
    value: "Большакова Grade 1 p.24: «Приголосні деренчать і тихенько шелестять, голосно свистять і шиплять». Приголосні (consonants) are made with voice + noise or noise only. Your lips, teeth, or tongue create an obstruction. You cannot sing a pure consonant — try singing [к] or [п]."
    reason: Replace single quotes to fix 'Приголосні' beat parsing.
  - path: content_outline[2].points[2]
    action: replace
    value: "Consonant letters to meet through Anna Ohoiko videos: М, Н, С, К, Л, Р, Б, В, Д, П, Т, Г, Ґ, З, Ж, Ш, Х, Й, Ч, Щ, Ц, Ф. Each video shows the letter, demonstrates the sound, and gives example words. Special: the letter Ґ represents the hard [g] sound, whereas Г is the pharyngeal [h]. Щ always = two sounds [шч]. Ь (м'який знак) makes no sound — it softens the consonant before it."
    reason: Remove "uniquely Ukrainian" claim for Ґ to address cultural accuracy complaint.
  - path: content_outline[4].points[0]
    action: replace
    value: "Self-check questions: How many letters in the Ukrainian alphabet? (33) How many sounds? (38) Why are they different? What are голосні? What are приголосні? Can you say «голосна літера»? (No — sounds are голосні, not letters!) What does Привіт mean? How do you answer Як справи?"
    reason: Replace single quotes to fix beat parsing.
  - path: dialogue_situations[1].setting
    action: replace
    value: "Two new classmates meet in the hallway before their first Ukrainian lesson and introduce themselves. MUST use named speaker labels (Марко: ..., Софія: ...), exchange names, and use the reciprocal «А у тебе?»."
    reason: Force writer to use named speakers instead of em dashes and include the required greeting.
  - path: dialogue_situations[1].motivation
    action: replace
    value: "Привіт! Як тебе звати? Мене звати... А у тебе? — first social use of sounds learned"
    reason: Update motivation to explicitly include the reciprocal greeting pattern.
===PLAN_PATCH_END===

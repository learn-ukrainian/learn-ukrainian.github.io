import re

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/pronoun-declension.md', 'r') as f:
    text = f.read()

# Fix the last instrumental
text = text.replace('### Завжди з прийменником', '### Завжди плюс прийменник')
text = text.replace('з прийменником', '+ прийменник')

# Accusative section fluff
text = text.replace(
    '''Every complete sentence requires an actor and an action. The person, animal, or thing that directly receives that action is known as the direct object. In English, personal pronouns change their form when they step into the role of a direct object. For example, you say "I see him", not "I see he". The pronoun "he" must transform into "him" to properly show its grammatical role in the sentence structure. 

This exact grammatical process happens systematically in Ukrainian. The grammatical category responsible for marking direct objects is called the Accusative case. When a pronoun becomes the direct target of a verb, it must abandon its dictionary form and take its Accusative form. Recognizing this role is the absolute first step to mastering conversational fluency. 

You already know many common verbs that require a direct object to complete their meaning. These include foundational verbs like to see, to know, to hear, to love, and to understand. Whenever you use these verbs, the pronoun that follows them must change accordingly.''',
    '''In Ukrainian, the Accusative case marks direct objects. When a pronoun is the direct target of a verb (like see, know, hear), it takes its Accusative form.'''
)

text = text.replace(
    '''The first and second person pronouns change significantly when they enter the Accusative case. The basic pronoun «я» transforms completely into «ме́не». The pronoun «ти» changes into «те́бе». In the plural forms, the transformation is slightly more predictable but still vital: «ми» becomes «нас», and «ви» becomes «вас».

These specific forms are used constantly in everyday speech. You will hear them everywhere when people talk about their personal relationships, daily interactions, and feelings. Let us look at how they work in full, contextual sentences. Notice carefully how the action of the verb directly affects the form of the pronoun.''',
    '''The first and second person pronouns change in the Accusative case: «я» becomes «ме́не», and «ти» becomes «те́бе». In plural: «ми» becomes «нас», and «ви» becomes «вас».'''
)

text = text.replace(
    '''The third person pronouns also undergo a transformation when they become direct objects. The masculine pronoun «він» and the neuter pronoun «воно́» share the exact same Accusative form, which is «його́». The feminine pronoun «вона́» changes into «її́». The plural pronoun «вони́», which covers all genders, becomes «їх».

These pronouns are absolutely essential for talking about people or things that are not currently participating in the conversation. You use them constantly to refer to friends, colleagues, missing items, or objects you have already mentioned previously in your story.''',
    '''The third person pronouns also change. «він» and «воно́» become «його́». «вона́» becomes «її́». «вони́» becomes «їх».'''
)

text = text.replace(
    '''Prepositions are small, connecting words that indicate relationships between other words in a sentence. Some common prepositions, such as the words for "for", "without", or "about", structurally require the Accusative case to follow them. When third person pronouns follow a preposition, a very special phonetic rule activates in Ukrainian.

A harmonious sound rule dictates that third person pronouns must receive the prefix «н-». Therefore, the form «його́» smoothly becomes «ньо́го». The pronoun «її́» becomes «неї́». The plural form «їх» becomes «них». This structural rule makes the language flow much more smoothly and effectively avoids awkward clusters of vowel sounds.

Crucially, this prefix rule applies exclusively to the third person pronouns. First and second person pronouns never change their form after prepositions.''',
    '''Some prepositions ("for", "without", "about") require the Accusative case. When third person pronouns follow a preposition, they receive the prefix «н-». «його́» becomes «ньо́го», «її́» becomes «неї́», and «їх» becomes «них». First and second person pronouns never change.'''
)

# Locative section fluff
text = text.replace(
    '''The Locative case possesses a distinctive, defining grammatical feature that sets it apart. It is one of the few cases in Ukrainian that never appears entirely alone in a sentence. It must always be securely anchored by a preposition. You simply cannot use a Locative pronoun nakedly in a sentence structure.

The most common prepositions used with the Locative case primarily indicate physical location, position, or the subject of an abstract thought. These include small words corresponding to "in", "at", "on", and "about". Understanding this absolute requirement makes mastering the Locative case much easier and more intuitive.

If you ever see a pronoun form that looks identical to a Locative form but completely lacks a preposition, it is actually functioning in the Dative case. The preposition is the mandatory trigger for the Locative.''',
    '''The Locative case never appears alone; it is always anchored by a preposition ("in", "at", "on", "about"). If there is no preposition, it is not Locative.'''
)

text = text.replace(
    '''The specific forms for the first and second person in the Locative case are «мені́» and «тобі́». For plural pronouns, the forms are completely identical to the Accusative case forms you just learned. They remain «нас» and «вас».

Because these specific pronouns must always be paired with prepositions, you will always encounter them in tight, connected pairs. You will use them extensively to describe where you currently are, what someone is wearing on themselves, or what you hold inside.''',
    '''The forms for first and second person are «мені́» and «тoбі́». For plural, they match the Accusative: «нас» and «вaм». They must be paired with prepositions.'''
)

text = text.replace(
    '''Because the Locative case structurally always requires a preposition, the rule for third person pronouns is incredibly simple and consistent. Third person pronouns in the Locative case will always, without exception, take the «н-» prefix. 

The resulting forms are «ньо́му» for both masculine and neuter subjects, «ній» for feminine subjects, and «них» for plural subjects. These forms are incredibly common when describing locations involving other people, buildings, or physical objects in your environment.

You also frequently use the Locative case with the preposition meaning "about" (про) to clearly express the topic of your deep thoughts, discussions, or speech.''',
    '''Third person pronouns in Locative always take the «н-» prefix: «ньо́му» (masculine/neuter), «ній» (feminine), and «них» (plural).'''
)

# Dative section fluff
text = text.replace(
    '''You have actually already encountered the Dative case without consciously realizing its grammatical name. When you previously learned how to say that you like something or someone, you used a very special structural construction. The phrase «мені подобається» translates literally to "to me it is pleasing".

In this specific emotional construction, the person experiencing the feeling is not the active grammatical subject of the sentence. Instead, the person is the passive, indirect receiver of the feeling. Therefore, the personal pronoun must take the Dative form. This is an extremely common way to express feelings, physical states, and preferences in Ukrainian.

You can flexibly use this exact structure to express that you are physically cold, hot, emotionally sad, or happy. The Dative pronoun sets the personal stage for the emotional or physical condition.''',
    '''The phrase «мені подобається» translates literally to "to me it is pleasing". The person is the indirect receiver, so the pronoun takes the Dative form.'''
)

text = text.replace(
    '''The Dative case forms primarily indicate the indirect recipient or beneficiary of an action. The correct form for «я» is «мені́». The form for «ти» is «тoбі́». You should notice that these are visually identical to the Locative forms, but they are critically used without prepositions.

For the third person, the masculine and neuter form changes to «йoму́». The feminine form becomes «їй». For the plural pronouns, «ми» becomes «нaм», «ви» becomes «вaм», and «вони́» becomes «їм».

These forms are consistently used to answer the fundamental questions "to whom?" or "for whom?" the action is being performed.''',
    '''The Dative case indicates the indirect recipient of an action. Forms: «я» is «мені́», «ти» is «тoбі́». Third person: «йoму́», «їй». Plural: «нaм», «вaм», «їм».'''
)

text = text.replace(
    '''Certain active verbs naturally and logically require the Dative case. These are verbs that inherently involve transferring a physical object, communicating specific information, or providing necessary assistance to someone. When you use these verbs, the person receiving the item, the message, or the help must be placed in the Dative case.

Core verbs in this essential category include the verbs to give, to speak or tell, to write, to answer, and to help. Memorizing these specific verbs alongside the Dative pronoun forms is an excellent and efficient learning strategy.''',
    '''Verbs like "to give", "to tell", "to write", and "to help" require the Dative case for the recipient.'''
)

# Genitive section fluff
text = text.replace(
    '''The Genitive case is perhaps the most frequently used oblique grammatical case in the entire Ukrainian language. One of its primary, foundational functions is to express possession, ownership, or basic existence. Unlike English, which heavily relies on the active verb "to have", Ukrainian strongly prefers a prepositional phrase coupled with the Genitive case.

The common construction translates quite literally to "at me there is". This reflects a distinct linguistic mindset that focuses more on the physical or abstract location of an object near a person, rather than strict, legal ownership. To form this vital construction, you use the preposition «у» or «в» (meaning "at"), followed by a personal pronoun securely in the Genitive case, and then the word «є» (meaning "is").

This specific structure is the absolute standard way to say that you have a family, a stable job, an idea, or a physical item in possession.''',
    '''The Genitive case is used to express possession or existence. Ukrainian prefers the structure "at me there is" using «у»/«в» + Genitive pronoun + «є».'''
)

text = text.replace(
    '''The Genitive case is equally essential for expressing total absence, lack, or negation. When something simply does not exist, or when someone is physically not present in a location, you use the specific word indicating absence followed immediately by the Genitive case.

This grammatical rule is absolute and strict. The negative word «нема́є» always, without exception, requires the Genitive case. It entirely does not matter what kind of object or person is missing. If they are not there, their pronoun must take the Genitive form.''',
    '''The Genitive case is also used for absence. The word «нема́є» always requires the Genitive case.'''
)

text = text.replace(
    '''As you study these paradigms, you might have noticed something comfortably familiar about the Genitive pronoun forms. For almost all personal pronouns, the Genitive forms are absolutely, letter-for-letter identical to the Accusative forms. The nominative pronoun «я» becomes «ме́не» in both cases. The pronoun «ми» becomes «нас» in both cases.

This extensive overlap significantly simplifies your learning process. You do not need to memorize an entirely new set of vocabulary words. Instead, you merely need to understand the surrounding context. If the pronoun follows the word for absence or the preposition "at", it is functioning as Genitive. If it is the direct target of a physical action, it is functioning as Accusative.

The third person pronouns also generously share their fundamental forms between the Genitive and Accusative cases. The forms «його́», «її́», and «їх» successfully serve double duty.''',
    '''Most Genitive pronoun forms are identical to their Accusative forms («ме́не», «те́бе», «нас», «вас», «його́», «її́», «їх»). Only the context distinguishes them.'''
)

text = text.replace(
    '''Exactly like in the Accusative case, third person pronouns in the Genitive case strictly require the «н-» prefix whenever they immediately follow a preposition. Many incredibly common prepositions structurally require the Genitive case, such as words meaning "near", "for", "from", and "without".

When you use these specific prepositions with third person pronouns, you must smoothly add the prefix. Therefore, you correctly say «бі́ля ньо́го», and you never say «бі́ля його́». This maintains the essential phonetic harmony of the spoken sentence.

However, you must clearly and carefully distinguish this grammatical situation from simple possession. When you say a phrase like "his brother", there is no preposition involved at all. In this case, the pronoun merely acts as a possessive adjective and definitely does not take the prefix.''',
    '''Third person pronouns in the Genitive case take the «н-» prefix after prepositions ("near", "for", "without").'''
)

with open('/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/pronoun-declension.md', 'w') as f:
    f.write(text)

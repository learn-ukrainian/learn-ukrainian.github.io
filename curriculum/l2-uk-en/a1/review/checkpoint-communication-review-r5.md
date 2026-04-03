## Linguistic Scan
No linguistic errors found.

## Exercise Check
- `<!-- INJECT_ACTIVITY: activity-1 -->` (Vocative + imperative fill-in) is present and correctly placed after the grammar table for imperatives.
- `<!-- INJECT_ACTIVITY: activity-2 -->` (Conjunction quiz) is present and correctly placed after the coordinating/subordinating conjunctions rules.
- `<!-- INJECT_ACTIVITY: activity-3 -->` (Complex sentences fill-in) is present and correctly placed after the subordinating conjunctions (що, де, коли) rules.
- `<!-- INJECT_ACTIVITY: activity-4 -->` (Holiday match) is present and correctly placed after the holiday greetings explanation.
All 4 activity markers are present, evenly distributed, and match the plan's `activity_hints`.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | All outline sections and vocabulary words (плакат, квиток, напій, кутя, колядки) are included. The dialogue scenarios from the plan are utilized effectively. |
| 2. Linguistic accuracy | 10/10 | Text is free of Russianisms, Surzhyk, and calques. Gender, case, and complex sentence structures are correct. |
| 3. Pedagogical quality | 8/10 | Provides clear grammar tables and translations, but incorrectly teaches that the vocative of "друг" is formed just by changing a hard consonant to "-е", ignoring the required consonant mutation. |
| 4. Vocabulary coverage | 10/10 | All required vocabulary is used naturally in the reading and dialogue sections. |
| 5. Exercise quality | 10/10 | Activity markers are perfectly placed immediately after the relevant grammar instructions. |
| 6. Engagement & tone | 6/10 | Contains excessive meta-commentary ("Notice how all five A1.7 communication tools appear naturally together..."). Treats the dialogue like a grammar-hunting exercise, which breaks immersion. |
| 7. Structural integrity | 10/10 | All required H2 headings are present, ordered correctly, and formatted cleanly. |
| 8. Cultural accuracy | 10/10 | Correctly uses "З Різдвом!" and references authentic holiday items like "кутя" and "колядки". |
| 9. Dialogue & conversation quality | 9/10 | Dialogues are clear and realistic, effectively demonstrating the grammar points in context. |

## Findings

[Pedagogical quality] [Critical]
Location: `| **друг** | **друже!** | Friend! (hard consonant → -е) |`
Issue: The rule provided for the vocative of "друг" is factually incorrect. It claims the hard consonant simply changes to "-е", which would incorrectly produce "друге". The actual change involves a consonant mutation (г → ж) before the ending "-е".
Fix: Update the rule explanation to explicitly state the consonant mutation.

[Engagement & tone] [Major]
Location: `Read the text below. Notice how all five A1.7 communication tools appear naturally together in one single realistic situation.`
Issue: Excessive meta-commentary that breaks immersion. Calling out "all five A1.7 communication tools" reads like a teacher's syllabus rather than engaging learner content.
Fix: Simplify the sentence to remove the meta-commentary.

[Engagement & tone] [Major]
Location: `Read through the dialogue again and circle every vocative case, imperative verb, conjunction, and subordinating clause you see. You should find at least two vocatives, three imperatives, three coordinating conjunctions, and five subordinating clauses. This is how natural Ukrainian looks in action.`
Issue: Highly robotic and textbook-like instruction. Treating the dialogue as a grammar-hunting exercise with a specific count breaks immersion and tells rather than shows.
Fix: Replace with a more natural instruction focused on comprehension and observation.

[Engagement & tone] [Minor]
Location: `These five skills work together. In the reading passage below, you will see Olena use all of them in one short phone call — she addresses Taras by name, asks him to bring something, explains why, links her thoughts into longer sentences, and wishes him a happy holiday. This is how these skills work in real conversations.`
Issue: Telling instead of showing. The concluding sentence "This is how these skills work in real conversations" is a generic cliché.
Fix: Streamline the text to be more engaging and less meta.

## Verdict: REVISE
The module covers all the necessary checkpoints and grammar rules effectively, but it contains a critical pedagogical error regarding the vocative mutation of "друг" and suffers from excessive meta-commentary that breaks learner immersion. Applying the fixes will resolve these issues.

<fixes>
- find: "| **друг** | **друже!** | Friend! (hard consonant → -е) |"
  replace: "| **друг** | **друже!** | Friend! (г → ж + е) |"
- find: "These five skills work together. In the reading passage below, you will see Olena use all of them in one short phone call — she addresses Taras by name, asks him to bring something, explains why, links her thoughts into longer sentences, and wishes him a happy holiday. This is how these skills work in real conversations."
  replace: "These five skills work together seamlessly. Read how Olena uses them naturally when calling her friend."
- find: "Read the text below. Notice how all five A1.7 communication tools appear naturally together in one single realistic situation."
  replace: "Read the text below. Notice how these communication tools appear together naturally."
- find: "Read through the dialogue again and circle every vocative case, imperative verb, conjunction, and subordinating clause you see. You should find at least two vocatives, three imperatives, three coordinating conjunctions, and five subordinating clauses. This is how natural Ukrainian looks in action."
  replace: "Read through the dialogue again. Notice how the organizer and volunteers use the vocative to address each other, and the imperative to give clear instructions."
</fixes>

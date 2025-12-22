/**
 * Quiz activity parser
 *
 * Parses multiple choice questions with checkbox syntax:
 *
 * ## quiz: Quiz Title
 * > Instructions here
 *
 * 1. Question text?
 *    - [x] Correct option
 *    - [ ] Wrong option
 *    - [ ] Wrong option
 *    > [!explanation] Why this is correct
 *
 * 2. Another question?
 *    - [ ] Option A
 *    - [x] Option B
 */

import { ActivityParser } from './base';
import { QuizContent, QuizQuestion, ParseContext } from '../../types';

/**
 *
 */
export class QuizParser extends ActivityParser<QuizContent> {
  readonly type = 'quiz' as const;

  /**
   *
   */
  protected parseContent(content: string, ctx: ParseContext): QuizContent {
    const questions: QuizQuestion[] = [];
    const body = this.getContentBody(content);

    // Split by numbered questions
    const qMatches = body.matchAll(/(\d+)\.\s+(.+?)\n([\s\S]*?)(?=\n\d+\.|$)/g);

    for (const match of qMatches) {
      const questionText = match[2].trim();
      const optionsBlock = match[3];

      const options: string[] = [];
      let correctIndex = 0;

      // Parse checkbox options: - [x] or - [ ]
      const optMatches = optionsBlock.matchAll(/-\s+\[([x ])\]\s+(.+)/gi);
      let idx = 0;
      for (const optMatch of optMatches) {
        options.push(optMatch[2].trim());
        if (optMatch[1].toLowerCase() === 'x') {
          correctIndex = idx;
        }
        idx++;
      }

      // If no checkbox options found, try to parse from > [!options] block
      let structuredOptionsFound = false;
      if (options.length === 0) {
        const { options: calloutOptions } = this.parseAnswerBlock(optionsBlock);
        if (calloutOptions && calloutOptions.length > 0) {
          options.push(...calloutOptions);
          structuredOptionsFound = true;
        }
      }

      // Parse explanation from callout
      let explanation = '';
      const { explanation: calloutExp } = this.parseAnswerBlock(optionsBlock);
      if (calloutExp) {
        explanation = calloutExp;
      } else if (!structuredOptionsFound) {
        // Legacy format: > explanation
        // Only attempt if we didn't find structured options, to avoid matching the option values themselves
        const expMatch = optionsBlock.match(/>\s+([^[\n].+)$/m);
        if (expMatch) explanation = expMatch[1].trim();
      }

      // Get image from context if available
      const imageUrl = ctx.imageMap?.get(questionText.toLowerCase());

      const question: QuizQuestion = {
        question: questionText,
        options,
        correctIndex,
        explanation,
      };

      if (imageUrl) {
        question.imageUrl = imageUrl;
      }

      questions.push(question);
    }

    return {
      type: 'quiz',
      questions,
      shuffleQuestions: true,
      shuffleOptions: true,
      showCorrectAnswers: true,
    };
  }
}

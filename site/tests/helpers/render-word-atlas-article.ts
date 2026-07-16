import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import WordAtlasArticle, {
  type WordAtlasArticleProps,
} from "@site/src/lexicon/WordAtlasArticle";

/** SSR-render the React WordAtlasArticle (no hydration / no Astro container). */
export function renderWordAtlasArticle(props: WordAtlasArticleProps): string {
  return renderToStaticMarkup(createElement(WordAtlasArticle, props));
}

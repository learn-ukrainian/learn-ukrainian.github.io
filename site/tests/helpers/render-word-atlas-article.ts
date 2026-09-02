import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import WordAtlasArticle, {
  type WordAtlasArticleProps,
} from "@site/src/lexicon/WordAtlasArticle";
import { atlasLinkCatalog } from "@site/src/lib/lexicon/atlas-link-catalog";

/** SSR-render the React WordAtlasArticle (no hydration / no Astro container). */
export function renderWordAtlasArticle(props: WordAtlasArticleProps): string {
  return renderToStaticMarkup(
    createElement(WordAtlasArticle, {
      ...props,
      atlasLinkCatalog: props.atlasLinkCatalog ?? atlasLinkCatalog,
    }),
  );
}

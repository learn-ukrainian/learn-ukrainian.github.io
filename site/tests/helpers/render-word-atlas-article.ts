import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import searchAliases from "@site/src/data/lexicon-search-aliases.json";
import searchArticles from "@site/src/data/lexicon-search-index.json";
import WordAtlasArticle, {
  type WordAtlasArticleProps,
} from "@site/src/lexicon/WordAtlasArticle";
import {
  buildAtlasLinkCatalogFromSearchRows,
  type AtlasSearchAliasRow,
  type AtlasSearchArticleRow,
} from "@site/src/lib/lexicon/word-atlas-article-model";

const testAtlasLinkCatalog = buildAtlasLinkCatalogFromSearchRows(
  searchArticles as AtlasSearchArticleRow[],
  searchAliases as AtlasSearchAliasRow[],
);

/** SSR-render the React WordAtlasArticle (no hydration / no Astro container). */
export function renderWordAtlasArticle(props: WordAtlasArticleProps): string {
  return renderToStaticMarkup(
    createElement(WordAtlasArticle, {
      ...props,
      atlasLinkCatalog: props.atlasLinkCatalog ?? testAtlasLinkCatalog,
    }),
  );
}

import searchAliases from "../../data/lexicon-search-aliases.json";
import searchArticles from "../../data/lexicon-search-index.json";
import {
  buildAtlasLinkCatalogFromSearchRows,
  type AtlasSearchAliasRow,
  type AtlasSearchArticleRow,
} from "./word-atlas-article-model";

/** Process-wide catalog shared by every prerendered Word Atlas article. */
export const atlasLinkCatalog = buildAtlasLinkCatalogFromSearchRows(
  searchArticles as AtlasSearchArticleRow[],
  searchAliases as AtlasSearchAliasRow[],
);

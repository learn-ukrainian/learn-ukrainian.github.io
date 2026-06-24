import type { APIRoute, GetStaticPaths } from "astro";

const shards = import.meta.glob("../../data/lexicon-practice-lexemes.*.json", {
  eager: true,
  import: "default",
}) as Record<string, unknown>;

const byLevel = new Map(
  Object.entries(shards).map(([path, payload]) => [
    path.match(/lexicon-practice-lexemes\.([A-Z][0-9])\.json$/)?.[1] ?? "",
    payload,
  ]),
);

export const getStaticPaths: GetStaticPaths = () =>
  [...byLevel.keys()].filter(Boolean).map((level) => ({ params: { level } }));

export const GET: APIRoute = ({ params }) => {
  const payload = byLevel.get(params.level ?? "");
  if (!payload) {
    return new Response("Not found", { status: 404 });
  }
  return new Response(JSON.stringify(payload), {
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "public, max-age=3600",
    },
  });
};

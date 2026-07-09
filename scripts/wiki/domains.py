"""Pure write-domain resolution for compiled wiki articles."""

from __future__ import annotations

from wiki.config import TRACK_WRITE_DOMAIN

# FOLK uses per-slug subdomains instead of a single track-wide write domain.
FOLK_DOMAIN_MAP: dict[str, str] = {
    "narodna-kultura-yak-systema": "folk/overview",
    # narodni-viruvannia-mifolohiia-demonolohiia + zamovliannia-zaklynannia-prymovky CUT 2026-06-25
    # (folk reset - demonology/occult/spell-craft framing, no school-canon basis; FOLK-FRAMING-STANDARD.md)
    "kalendarna-obriadovist-zvychai": "folk/ritual",
    "koliadky-shchedrivky": "folk/ritual",
    "vesnianky-hayivky": "folk/ritual",
    "kupalski-rusalni-pisni": "folk/ritual",
    "zhnyvarski-obzhynkovi-pisni": "folk/ritual",
    "rodynna-obriadovist-zvychai": "folk/ritual",
    "vesilni-pisni": "folk/ritual",
    "holosinnya": "folk/ritual",
    "dumy-nevilnytski-lytsarski": "folk/genres",
    "bylyny-kyivskoho-tsyklu": "folk/genres",
    "dumy-sotsialno-pobutovi": "folk/genres",
    "kobzarstvo-lirnytstvo": "folk/genres",
    "istorychni-pisni": "folk/historical",
    "striletski-povstanski-pisni": "folk/historical",
    "rodynno-pobutovi-pisni": "folk/lyric",
    "kolomyiky": "folk/lyric",
    "suspilno-pobutovi-pisni": "folk/lyric",
    "narodni-balady": "folk/lyric",
    "pisni-literaturnoho-pokhodzhennia": "folk/lyric",
    "charivni-kazky": "folk/prose",
    "kazky-pro-tvaryn": "folk/prose",
    "sotsialno-pobutovi-kazky": "folk/prose",
    "narodni-lehendy": "folk/prose",
    "istorychni-perekazy": "folk/prose",
    "narodni-opovidannia-buvalshchyny-memoraty": "folk/prose",
    "prykazky-ta-pryslivia": "folk/short-forms",
    "zahadky": "folk/short-forms",
    "narodni-anekdoty": "folk/short-forms",
    "dytiachyi-folklor-kolyskovi": "folk/short-forms",
    "vertep-narodna-drama": "folk/performance",
    "narodni-muzychni-instrumenty": "folk/performance",
    "narodni-tantsi": "folk/performance",
    "pysankarstvo": "folk/material",
    "narodna-vyshyvka-rushnyk-strii": "folk/material",
    "narodni-remesla-ta-khudozhni-promysly": "folk/material",
    "narodne-zhytlo-sadyba-hospodarstvo": "folk/material",
    "narodna-kukhnia-obriadova-yizha": "folk/material",
    "rehionalni-etnokulturni-tradytsii": "folk/synthesis",
    "narodna-kultura-ta-vysoka-kultura-mistky": "folk/synthesis",
}

SEMINAR_TRACK_DOMAIN_MAP: dict[str, str] = {
    "hist": "periods",
    "bio": "figures",
    "istorio": "historiography",
    "lit": "literature/works",
    "lit-essay": "literature/works",
    "lit-war": "literature/works",
    "lit-hist-fic": "literature/works",
    "lit-youth": "literature/works",
    "lit-fantastika": "literature/works",
    "lit-humor": "literature/works",
    "lit-drama": "literature/works",
    # lit-doc and lit-crimea were merged into other lit-* tracks; no longer
    # exist in curriculum.yaml. Removed from compile config 2026-04-27.
    "oes": "linguistics/oes",
    "ruth": "linguistics/ruthenian",
}


def resolve_write_domain(track: str, slug: str) -> str:
    """Return the wiki write domain for a track/slug pair."""
    track_key = track.strip().lower()

    if track_key in TRACK_WRITE_DOMAIN:
        return TRACK_WRITE_DOMAIN[track_key]

    if track_key == "folk":
        return FOLK_DOMAIN_MAP.get(slug, "folk")

    return SEMINAR_TRACK_DOMAIN_MAP.get(track_key, track)

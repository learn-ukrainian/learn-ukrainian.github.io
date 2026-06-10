import sqlite3

from scripts.ingest.goroh_etymology_ingest import (
    ensure_goroh_etymology_schema,
    parse_goroh_html,
    upsert_goroh_row,
)
from scripts.lexicon.enrich_manifest import _etymology


def test_canonicalized_goroh_lemma_resolves_without_network() -> None:
    html = """
    <html>
      <body>
        <div class="card etymology-root">
          <h2 class="card-header">коле́га</h2>
          <p></p>
          <div class="list">
            <div class="list-item circle">
              запозичення з латинської мови; лат. collega «товариш по службі».
            </div>
          </div>
          <div class="section collapsible">
            <div class="section-header">Фонетичні та словотвірні варіанти</div>
            <div class="section-content">колежа́нка «колега (жінка)»</div>
          </div>
        </div>
      </body>
    </html>
    """
    row = parse_goroh_html(
        html,
        requested_lemma="колежанка",
        source_url="https://goroh.pp.ua/Етимологія/колежанка",
    )
    assert row is not None
    assert row["requested_lemma"] == "колежанка"
    assert row["headword"] == "колега"
    assert "колежанка" not in row["etymology_text"]

    conn = sqlite3.connect(":memory:")
    ensure_goroh_etymology_schema(conn)
    with conn:
        upsert_goroh_row(conn, row)

    by_requested = _etymology(conn, "колежанка")
    assert by_requested == {
        "text": "запозичення з латинської мови; лат. collega «товариш по службі».",
        "source": "Горох (за ЕСУМ)",
        "source_url": "https://goroh.pp.ua/Етимологія/колежанка",
    }

    by_headword = _etymology(conn, "колега")
    assert by_headword == by_requested

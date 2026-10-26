import pytest
import requests

from scripts.ingest.goroh_etymology_ingest import (
    build_parser,
    fetch_goroh_entry,
    parse_goroh_html,
)


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


@pytest.mark.parametrize(
    ("cli_args", "expected_user_agent"),
    [
        pytest.param(
            [],
            "learn-ukrainian-goroh-etymology/1.0 "
            "(noncommercial educational lookup; issue 2882; "
            "https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues)",
            id="default-public-contact",
        ),
        pytest.param(
            ["--user-agent", "custom-goroh-client/2.0 (https://example.org/contact)"],
            "custom-goroh-client/2.0 (https://example.org/contact)",
            id="explicit-cli-override",
        ),
    ],
)
def test_fetch_user_agent_missing_contact_or_overridden_identity(
    monkeypatch: pytest.MonkeyPatch,
    cli_args: list[str],
    expected_user_agent: str,
) -> None:
    """Catch missing default contact and discarded CLI identity at HTTP transport."""
    sent: list[requests.PreparedRequest] = []

    def send(
        self: requests.adapters.HTTPAdapter,
        request: requests.PreparedRequest,
        **kwargs: object,
    ) -> requests.Response:
        sent.append(request)
        assert kwargs["timeout"] == 7
        response = requests.Response()
        response.status_code = 200
        response.url = request.url
        response.encoding = "utf-8"
        response._content = """
        <div class="card etymology-root">
          <h2 class="card-header">коле́га</h2>
          <div class="list"><div class="list-item circle">
            запозичення з латинської мови; лат. collega «товариш по службі».
          </div></div>
        </div>
        """.encode()
        return response

    monkeypatch.setattr(requests.adapters.HTTPAdapter, "send", send)
    args = build_parser().parse_args(cli_args)
    row = fetch_goroh_entry(
        "колега",
        requested_lemma="колега",
        user_agent=args.user_agent,
        timeout=7,
        max_text_chars=1200,
    )

    assert len(sent) == 1
    assert sent[0].method == "GET"
    assert sent[0].url == (
        "https://goroh.pp.ua/%D0%95%D1%82%D0%B8%D0%BC%D0%BE%D0%BB%D0%BE%D0%B3%D1%96%D1%8F/"
        "%D0%BA%D0%BE%D0%BB%D0%B5%D0%B3%D0%B0"
    )
    assert sent[0].headers["User-Agent"] == expected_user_agent
    assert row is not None
    assert row["requested_lemma"] == "колега"
    assert row["headword"] == "колега"
    assert row["source_url"] == sent[0].url
    assert row["etymology_text"] == "запозичення з латинської мови; лат. collega «товариш по службі»."

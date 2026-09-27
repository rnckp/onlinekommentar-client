import httpx
import pytest

from onlinekommentar import OnlinekommentarClient
from onlinekommentar.models import Commentary, CommentarySearchResult


def _client_with_handler(
    handler: httpx.MockTransport | httpx.BaseTransport,
) -> OnlinekommentarClient:
    return OnlinekommentarClient(
        base_url="https://example.test",
        rate_limit_delay=0,
        transport=handler,
    )


def _json_response(data: object) -> httpx.Response:
    return httpx.Response(200, json=data)


def test_list_commentaries_builds_query_and_parses_result() -> None:
    seen_request: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_request
        seen_request = request
        return _json_response(
            {
                "data": [
                    {
                        "id": "commentary-1",
                        "title": "Art. 10 FDTA",
                        "date": "2026-05-18",
                        "language": "de",
                        "authors": [],
                        "editors": [],
                        "legislative_act": None,
                    }
                ],
                "links": {"next": None},
                "meta": {
                    "current_page": 2,
                    "last_page": 2,
                    "per_page": 50,
                    "total": 51,
                },
            }
        )

    client = _client_with_handler(httpx.MockTransport(handler))

    result = client.list_commentaries(
        language="de",
        search="Universalversammlung",
        legislative_act="act-1",
        sort="title",
        page=2,
    )

    assert isinstance(result, CommentarySearchResult)
    assert result.commentaries[0].commentary_id == "commentary-1"
    assert seen_request is not None
    assert seen_request.method == "GET"
    assert seen_request.url.path == "/api/commentaries"
    assert seen_request.url.params["language"] == "de"
    assert seen_request.url.params["search"] == "Universalversammlung"
    assert seen_request.url.params["legislative_act"] == "act-1"
    assert seen_request.url.params["sort"] == "title"
    assert seen_request.url.params["page"] == "2"


def test_list_commentaries_uses_config_default_language_when_omitted(
    tmp_path,
) -> None:
    seen_request: httpx.Request | None = None
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
onlinekommentar:
  default_language: "fr"
""",
        encoding="utf-8",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_request
        seen_request = request
        return _json_response({"data": [], "links": {}, "meta": {}})

    client = OnlinekommentarClient(
        base_url="https://example.test",
        config_path=config_path,
        rate_limit_delay=0,
        transport=httpx.MockTransport(handler),
    )

    client.list_commentaries()

    assert seen_request is not None
    assert seen_request.url.params["language"] == "fr"


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"base_url": ""}, "base_url must not be empty"),
        ({"default_language": ""}, "default_language must be one of"),
    ],
)
def test_constructor_rejects_empty_overrides(
    kwargs: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        OnlinekommentarClient(**kwargs)


def test_get_commentary_quotes_id_and_parses_result() -> None:
    seen_raw_path = b""

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_raw_path
        seen_raw_path = request.url.raw_path
        return _json_response(
            {
                "id": "commentary/with slash",
                "title": "Art. 10 FDTA",
                "date": "2026-05-18",
                "language": "en",
                "authors": [],
                "editors": [],
                "legislative_act": None,
            }
        )

    client = _client_with_handler(httpx.MockTransport(handler))

    commentary = client.get_commentary("commentary/with slash")

    assert isinstance(commentary, Commentary)
    assert seen_raw_path == b"/api/commentaries/commentary%2Fwith%20slash"


def test_get_commentary_parses_single_resource_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return _json_response(
            {
                "data": {
                    "id": "commentary-1",
                    "title": "Art. 10 FDTA",
                    "date": "2026-05-18",
                    "language": "en",
                    "authors": [],
                    "editors": [],
                    "legislative_act": None,
                }
            }
        )

    client = _client_with_handler(httpx.MockTransport(handler))

    commentary = client.get_commentary("commentary-1")

    assert commentary.commentary_id == "commentary-1"
    assert commentary.title == "Art. 10 FDTA"


def test_raw_json_helpers_return_api_payloads() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/commentaries":
            return _json_response({"data": [], "links": {}, "meta": {}})
        if request.url.path == "/api/commentaries/commentary-1":
            return _json_response({"id": "commentary-1"})
        raise AssertionError(f"Unexpected path: {request.url.path}")

    client = _client_with_handler(httpx.MockTransport(handler))

    assert client.list_commentaries_raw() == {"data": [], "links": {}, "meta": {}}
    assert client.get_commentary_raw("commentary-1") == {"id": "commentary-1"}


@pytest.mark.parametrize(
    ("method_name", "kwargs", "expected_params"),
    [
        ("identify", {}, {"verb": "Identify"}),
        ("list_metadata_formats", {}, {"verb": "ListMetadataFormats"}),
        ("list_sets", {}, {"verb": "ListSets"}),
        (
            "list_identifiers",
            {"metadata_prefix": "oai_dc", "from_date": "2026-01-01"},
            {
                "verb": "ListIdentifiers",
                "metadataPrefix": "oai_dc",
                "from": "2026-01-01",
            },
        ),
        (
            "list_records",
            {
                "metadata_prefix": "oai_openaire",
                "set_spec": "legal_domain:civil-procedure",
            },
            {
                "verb": "ListRecords",
                "metadataPrefix": "oai_openaire",
                "set": "legal_domain:civil-procedure",
            },
        ),
        (
            "get_record",
            {
                "identifier": "oai:onlinekommentar.ch:commentary:commentary-1",
                "metadata_prefix": "oai_dc",
            },
            {
                "verb": "GetRecord",
                "identifier": "oai:onlinekommentar.ch:commentary:commentary-1",
                "metadataPrefix": "oai_dc",
            },
        ),
    ],
)
def test_oai_helpers_build_expected_requests(
    method_name: str,
    kwargs: dict[str, object],
    expected_params: dict[str, str],
) -> None:
    seen_request: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_request
        seen_request = request
        return httpx.Response(200, text="<OAI-PMH />")

    client = _client_with_handler(httpx.MockTransport(handler))
    method = getattr(client, method_name)

    assert method(**kwargs) == "<OAI-PMH />"
    assert seen_request is not None
    assert seen_request.method == "GET"
    assert seen_request.url.path == "/oai"
    for key, value in expected_params.items():
        assert seen_request.url.params[key] == value


@pytest.mark.parametrize("method_name", ["list_identifiers", "list_records"])
def test_oai_resumption_token_requests_do_not_include_other_params(
    method_name: str,
) -> None:
    expected_verbs = {
        "list_identifiers": "ListIdentifiers",
        "list_records": "ListRecords",
    }
    seen_request: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_request
        seen_request = request
        return httpx.Response(200, text="<OAI-PMH />")

    client = _client_with_handler(httpx.MockTransport(handler))
    method = getattr(client, method_name)

    assert method(resumption_token="next-page-token") == "<OAI-PMH />"
    assert seen_request is not None
    assert dict(seen_request.url.params) == {
        "verb": expected_verbs[method_name],
        "resumptionToken": "next-page-token",
    }


def test_generic_oai_rejects_resumption_token_with_other_arguments() -> None:
    client = _client_with_handler(httpx.MockTransport(lambda request: httpx.Response(200)))

    with pytest.raises(
        ValueError,
        match="resumption_token cannot be combined with: metadata_prefix",
    ):
        client.oai(
            "ListRecords",
            metadata_prefix="oai_dc",
            resumption_token="next-page-token",
        )


def test_oai_helpers_reject_resumption_token_with_filters() -> None:
    client = _client_with_handler(httpx.MockTransport(lambda request: httpx.Response(200)))

    with pytest.raises(
        ValueError,
        match="resumption_token cannot be combined with: from_date, set_spec",
    ):
        client.list_records(
            from_date="2026-01-01",
            set_spec="legal_domain:civil-procedure",
            resumption_token="next-page-token",
        )


def test_context_manager_closes_client() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return _json_response({"data": [], "links": {}, "meta": {}})

    with _client_with_handler(httpx.MockTransport(handler)) as client:
        assert client.list_commentaries_raw() == {"data": [], "links": {}, "meta": {}}

    with pytest.raises(RuntimeError, match="Cannot send a request"):
        client.list_commentaries_raw()


@pytest.mark.parametrize("commentary_id", ["", ".", ".."])
def test_commentary_rejects_ids_that_escape_the_detail_route(commentary_id: str) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        pytest.fail("Invalid identifiers must fail before sending a request")

    with _client_with_handler(httpx.MockTransport(handler)) as client:
        with pytest.raises(ValueError, match="commentary_id"):
            client.get_commentary_raw(commentary_id)


def test_rate_limit_uses_monotonic_elapsed_time(monkeypatch: pytest.MonkeyPatch) -> None:
    ticks = iter([0.0, 0.05, 0.2, 1.0, 1.0])
    sleeps: list[float] = []
    monkeypatch.setattr("onlinekommentar.client.time.monotonic", lambda: next(ticks))
    monkeypatch.setattr("onlinekommentar.client.time.sleep", sleeps.append)
    with OnlinekommentarClient(
        rate_limit_delay=0.2,
        transport=httpx.MockTransport(lambda request: _json_response({"data": []})),
    ) as client:
        for _ in range(3):
            client.list_commentaries_raw()
    assert sleeps == pytest.approx([0.15])


@pytest.mark.parametrize("status", [404, 429, 503])
def test_http_errors_propagate(status: int) -> None:
    with _client_with_handler(
        httpx.MockTransport(lambda request: httpx.Response(status))
    ) as client:
        with pytest.raises(httpx.HTTPStatusError) as error:
            client.list_commentaries_raw()
    assert error.value.response.status_code == status


def test_request_timeout_reaches_transport() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.extensions["timeout"] == dict(connect=2.5, read=2.5, write=2.5, pool=2.5)
        raise httpx.ReadTimeout("Timed out", request=request)

    with _client_with_handler(httpx.MockTransport(handler)) as client:
        with pytest.raises(httpx.ReadTimeout):
            client.list_commentaries_raw(request_timeout=2.5)

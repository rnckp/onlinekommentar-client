from datetime import UTC, datetime, tzinfo
from pathlib import Path

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
        discover_config=False,
    )


def _json_response(data: object) -> httpx.Response:
    return httpx.Response(200, json=data)


@pytest.fixture(autouse=True)
def isolated_working_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep client tests independent of the developer's working-directory config."""
    monkeypatch.chdir(tmp_path)


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


@pytest.mark.parametrize("method_name", ["list_identifiers", "list_records"])
@pytest.mark.parametrize("metadata_prefix", ["oai_dc", "oai_openaire"])
def test_oai_helpers_reject_explicit_format_with_resumption_token(
    method_name: str, metadata_prefix: str
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        pytest.fail("Conflicting OAI arguments must fail before a request is sent")

    with _client_with_handler(httpx.MockTransport(handler)) as client:
        with pytest.raises(
            ValueError, match="resumption_token cannot be combined with: metadata_prefix"
        ):
            getattr(client, method_name)(
                metadata_prefix=metadata_prefix, resumption_token="next-page-token"
            )


@pytest.mark.parametrize("method_name", ["list_identifiers", "list_records"])
def test_oai_helpers_default_to_dublin_core(method_name: str) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["metadataPrefix"] == "oai_dc"
        return httpx.Response(200, text="<OAI-PMH />")

    with _client_with_handler(httpx.MockTransport(handler)) as client:
        assert getattr(client, method_name)() == "<OAI-PMH />"


def test_oai_protocol_errors_are_returned_as_xml() -> None:
    xml = (
        '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">'
        '<error code="badResumptionToken">Expired token</error></OAI-PMH>'
    )
    with _client_with_handler(
        httpx.MockTransport(lambda request: httpx.Response(200, text=xml))
    ) as client:
        assert client.list_records(resumption_token="expired-token") == xml


@pytest.mark.parametrize("timeout", [0, -1, True, float("nan"), float("inf")])
def test_invalid_request_timeouts_fail_before_network(timeout: float) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        pytest.fail("Invalid timeouts must fail before a request")

    with OnlinekommentarClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ValueError):
            client.list_commentaries_raw(request_timeout=timeout)


@pytest.mark.parametrize(
    ("method", "kwargs"),
    [
        ("get_commentary", {"commentary_id": "example"}),
        ("get_commentary_raw", {"commentary_id": "example"}),
        ("identify", {}),
        ("list_metadata_formats", {}),
        ("list_sets", {}),
        ("list_identifiers", {}),
        ("list_records", {}),
        ("get_record", {"identifier": "oai:example:record"}),
    ],
)
def test_named_helpers_forward_request_timeout(method: str, kwargs: dict[str, str]) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert set(request.extensions["timeout"].values()) == {2.5}
        if request.url.path.startswith("/api/"):
            return _json_response({"id": "example", "title": "Example"})
        return httpx.Response(200, text="<OAI-PMH />")

    with OnlinekommentarClient(transport=httpx.MockTransport(handler)) as client:
        getattr(client, method)(**kwargs, request_timeout=2.5)


def test_client_can_ignore_unrelated_working_directory_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "config.yaml").write_text("another_app: true\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    with OnlinekommentarClient(discover_config=False) as client:
        assert client.base_url == "https://onlinekommentar.ch"


def test_retries_are_disabled_by_default() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(503)

    with OnlinekommentarClient(discover_config=False, transport=httpx.MockTransport(handler)) as c:
        with pytest.raises(httpx.HTTPStatusError):
            c.list_commentaries_raw()
    assert calls == 1


def test_retry_after_is_respected_and_response_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr("onlinekommentar.client.time.sleep", sleeps.append)
    responses = [httpx.Response(429, headers={"Retry-After": "3"}), _json_response({"data": []})]
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        response = responses[calls]
        calls += 1
        return response

    with OnlinekommentarClient(
        discover_config=False,
        max_retries=1,
        rate_limit_delay=0,
        transport=httpx.MockTransport(handler),
    ) as client:
        assert client.list_commentaries_raw() == {"data": []}
    assert calls == 2
    assert sleeps == [3.0]
    assert responses[0].is_closed


@pytest.mark.parametrize("retry_after", ["120", "9" * 400])
def test_retry_after_exceeding_budget_does_not_retry_early(
    monkeypatch: pytest.MonkeyPatch, retry_after: str
) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr("onlinekommentar.client.time.sleep", sleeps.append)
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(429, headers={"Retry-After": retry_after})

    with OnlinekommentarClient(
        discover_config=False,
        max_retries=2,
        rate_limit_delay=0,
        transport=httpx.MockTransport(handler),
    ) as client:
        with pytest.raises(httpx.HTTPStatusError):
            client.list_commentaries_raw()
    assert calls == 1
    assert sleeps == []


def test_transport_retries_stop_at_configured_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr("onlinekommentar.client.time.sleep", sleeps.append)
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ConnectError("Synthetic failure", request=request)

    with OnlinekommentarClient(
        discover_config=False,
        max_retries=2,
        rate_limit_delay=0,
        transport=httpx.MockTransport(handler),
    ) as client:
        with pytest.raises(httpx.ConnectError):
            client.list_commentaries_raw()
    assert calls == 3
    assert sleeps == [1.0, 2.0]


def test_retry_after_http_date_uses_remaining_delay(monkeypatch: pytest.MonkeyPatch) -> None:
    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz: tzinfo | None = None) -> datetime:
            return datetime(2026, 10, 13, tzinfo=UTC)

    monkeypatch.setattr("onlinekommentar.client.datetime", FixedDatetime)
    sleeps: list[float] = []
    monkeypatch.setattr("onlinekommentar.client.time.sleep", sleeps.append)
    responses = iter(
        [
            httpx.Response(503, headers={"Retry-After": "Tue, 13 Oct 2026 00:00:05 GMT"}),
            _json_response({"data": []}),
        ]
    )
    with OnlinekommentarClient(
        discover_config=False,
        max_retries=1,
        rate_limit_delay=0,
        transport=httpx.MockTransport(lambda request: next(responses)),
    ) as client:
        assert client.list_commentaries_raw() == {"data": []}
    assert sleeps == [5.0]


@pytest.mark.parametrize("status", [404, 500])
def test_non_transient_http_errors_are_not_retried(status: int) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(status)

    with OnlinekommentarClient(
        discover_config=False,
        max_retries=2,
        rate_limit_delay=0,
        transport=httpx.MockTransport(handler),
    ) as client:
        with pytest.raises(httpx.HTTPStatusError):
            client.list_commentaries_raw()
    assert calls == 1


def test_oai_uses_xml_accept_header() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Accept"] == "application/xml"
        return httpx.Response(200, text="<OAI-PMH />")

    with _client_with_handler(httpx.MockTransport(handler)) as client:
        assert client.identify() == "<OAI-PMH />"


def test_iterator_preserves_filters_and_never_follows_response_urls() -> None:
    pages: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "example.test"
        assert request.url.params["search"] == "Example"
        assert request.url.params["language"] == "de"
        assert request.url.params["legislative_act"] == "act-1"
        assert request.url.params["sort"] == "title"
        page = request.url.params["page"]
        pages.append(page)
        return _json_response(
            {
                "data": [{"id": page, "title": "Example"}],
                "meta": {"current_page": int(page)},
                "links": {"next": "https://untrusted.test/" if page == "1" else None},
            }
        )

    with _client_with_handler(httpx.MockTransport(handler)) as client:
        items = list(
            client.iter_commentaries(
                language="de",
                search="Example",
                legislative_act="act-1",
                sort="title",
                max_pages=2,
            )
        )
    assert [item.commentary_id for item in items] == ["1", "2"]
    assert pages == ["1", "2"]


def test_iterator_reports_incomplete_results_at_page_cap() -> None:
    from onlinekommentar import PaginationLimitError

    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return _json_response({"data": [], "links": {"next": "https://example.test/?page=2"}})

    with _client_with_handler(httpx.MockTransport(handler)) as client:
        with pytest.raises(PaginationLimitError):
            list(client.iter_commentaries(max_pages=2))
    assert calls == 2


@pytest.mark.parametrize("kwargs", [{"max_pages": 0}, {"max_pages": True}, {"start_page": -1}])
def test_iterator_rejects_invalid_bounds_before_network(kwargs: dict[str, object]) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        pytest.fail("Invalid bounds must fail before a request")

    with _client_with_handler(httpx.MockTransport(handler)) as client:
        with pytest.raises(ValueError):
            list(client.iter_commentaries(**kwargs))


def test_iterator_rejects_repeated_server_page_before_yielding_items() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return _json_response(
            {
                "data": [{"id": "duplicate", "title": "Example"}],
                "meta": {"current_page": 1},
            }
        )

    with _client_with_handler(httpx.MockTransport(handler)) as client:
        iterator = client.iter_commentaries(start_page=2)
        with pytest.raises(ValueError, match="unexpected page"):
            next(iterator)

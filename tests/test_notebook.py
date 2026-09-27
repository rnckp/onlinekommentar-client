"""Execute the trusted tutorial cells against deterministic HTTP responses."""

import json
from pathlib import Path
from typing import Any

import httpx
import pytest

import onlinekommentar

NOTEBOOK = Path(__file__).resolve().parents[1] / "examples" / "onlinekommentar_demo.ipynb"


@pytest.mark.parametrize(
    "scenario", ["success", "empty", "upstream_errors", "unreachable", "invalid"]
)
def test_notebook_executes_and_closes_clients(
    scenario: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    requests: list[httpx.Request] = []
    clients: list[onlinekommentar.OnlinekommentarClient] = []
    real_client = onlinekommentar.OnlinekommentarClient
    commentary = {
        "id": "example-id",
        "title": "Example commentary",
        "authors": [{"id": "author-id", "name": "Example Author"}],
        "legislative_act": {"id": "act-id", "title": "Example act"},
    }

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if scenario == "unreachable":
            raise httpx.ConnectError("Synthetic connection failure", request=request)
        if request.url.path == "/api/commentaries":
            if scenario == "invalid":
                return httpx.Response(200, json={"data": [42]})
            page = int(request.url.params.get("page", "1"))
            has_next = scenario != "empty" and page == 1
            return httpx.Response(
                200,
                json={
                    "data": [] if scenario == "empty" else [commentary],
                    "links": {
                        "next": "https://example.test/api/commentaries?page=2" if has_next else None
                    },
                    "meta": {
                        "current_page": page,
                        "last_page": 2,
                        "per_page": 1,
                        "total": 0 if scenario == "empty" else 2,
                    },
                },
            )
        if request.url.path == "/api/commentaries/example-id":
            return httpx.Response(200, json={"data": commentary})
        assert request.url.path == "/oai"
        verb = request.url.params["verb"]
        if scenario == "invalid":
            return httpx.Response(200, text="not XML")
        if scenario == "upstream_errors" and verb == "ListIdentifiers":
            return httpx.Response(500)
        if scenario == "upstream_errors" and "resumptionToken" in request.url.params:
            content = '<error code="badResumptionToken">Expired token</error>'
        elif scenario == "empty":
            content = f"<{verb} />"
        else:
            header = "<header><identifier>oai:example:record</identifier></header>"
            content = {
                "Identify": (
                    "<repositoryName>Example</repositoryName><granularity>YYYY-MM-DD</granularity>"
                ),
                "ListMetadataFormats": (
                    "<metadataFormat><metadataPrefix>oai_dc</metadataPrefix></metadataFormat>"
                ),
                "ListSets": "<set><setSpec>legal_domain:example</setSpec></set>",
                "ListIdentifiers": header,
                "ListRecords": f"<record>{header}<metadata /></record>",
                "GetRecord": f"<record>{header}<metadata /></record>",
            }[verb]
            if verb in {"ListSets", "ListIdentifiers", "ListRecords"}:
                if "resumptionToken" in request.url.params:
                    assert dict(request.url.params) == {"verb": verb, "resumptionToken": "page+2/="}
                    content += "<resumptionToken />"
                else:
                    content += "<resumptionToken>page+2/=</resumptionToken>"
            content = f"<{verb}>{content}</{verb}>"
        return httpx.Response(
            200, text=f'<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">{content}</OAI-PMH>'
        )

    def create_client(**kwargs: Any) -> onlinekommentar.OnlinekommentarClient:
        kwargs.setdefault("transport", httpx.MockTransport(handler))
        kwargs.setdefault("config_path", tmp_path / "absent.yaml")
        client = real_client(**kwargs)
        clients.append(client)
        return client

    def reject_network(*args: Any, **kwargs: Any) -> None:
        pytest.fail("Notebook validation must never access the network")

    monkeypatch.setattr(onlinekommentar, "OnlinekommentarClient", create_client)
    monkeypatch.setattr("time.sleep", lambda seconds: None)
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", reject_network)
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    namespace: dict[str, Any] = {"__name__": "__main__"}
    for index, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] == "code":
            assert cell["outputs"] == []
            assert cell["execution_count"] is None
            # Only execute this repository's trusted tutorial, never downloaded notebook code.
            exec(compile("".join(cell["source"]), f"notebook-cell-{index}", "exec"), namespace)
            assert all(client._client.is_closed for client in clients)

    assert clients
    if scenario == "success":
        assert {
            request.url.params.get("verb") for request in requests if request.url.path == "/oai"
        } == {
            "Identify",
            "ListMetadataFormats",
            "ListSets",
            "ListIdentifiers",
            "ListRecords",
            "GetRecord",
        }
        assert any(request.url.params.get("page") == "2" for request in requests)
        assert any(
            request.url.params.get("metadataPrefix") == "oai_openaire" for request in requests
        )
        assert any(request.url.params.get("set") == "legal_domain:example" for request in requests)
        assert any(request.url.params.get("legislative_act") == "act-id" for request in requests)
    elif scenario == "empty":
        assert not any("resumptionToken" in request.url.params for request in requests)
        assert not any(request.url.path.endswith("example-id") for request in requests)
    elif scenario == "upstream_errors":
        assert namespace["next_records"] is None
        assert namespace["oai_identifier"] == "oai:example:record"

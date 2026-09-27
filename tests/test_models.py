import pytest
from pydantic import ValidationError

from onlinekommentar.models import (
    Commentary,
    CommentarySearchResult,
    LegislativeAct,
    Person,
)


def test_commentary_search_result_parses_paginated_response() -> None:
    payload = {
        "data": [
            {
                "id": "c9f28a48-39a2-42c4-baa8-7024899156b1",
                "title": "Art. 10 FDTA",
                "date": "2026-05-18",
                "language": "en",
                "authors": [{"id": "author-1", "name": "Example Author"}],
                "editors": [{"id": "editor-1", "name": "Example Editor"}],
                "legislative_act": {
                    "id": "act-1",
                    "title": "Federal Act on Direct Federal Tax",
                },
                "link": "https://onlinekommentar.ch/api/commentaries/c9f",
                "html_link": "https://onlinekommentar.ch/en/kommentare/dbg10",
                "pdf_link": "https://onlinekommentar.ch/en/kommentare/dbg10/print",
                "additional_document_links": [],
                "extra": "kept",
            }
        ],
        "links": {"next": "https://onlinekommentar.ch/api/commentaries?page=2"},
        "meta": {"current_page": 1, "last_page": 8, "per_page": 50, "total": 372},
    }

    result = CommentarySearchResult.from_json(payload)

    assert result.current_page == 1
    assert result.total == 372
    assert result.next_page_url == "https://onlinekommentar.ch/api/commentaries?page=2"
    assert result.commentaries == [
        Commentary(
            commentary_id="c9f28a48-39a2-42c4-baa8-7024899156b1",
            title="Art. 10 FDTA",
            date="2026-05-18",
            language="en",
            authors=[
                Person(
                    person_id="author-1",
                    name="Example Author",
                    raw=payload["data"][0]["authors"][0],
                )
            ],
            editors=[
                Person(
                    person_id="editor-1",
                    name="Example Editor",
                    raw=payload["data"][0]["editors"][0],
                )
            ],
            legislative_act=LegislativeAct(
                legislative_act_id="act-1",
                title="Federal Act on Direct Federal Tax",
                raw=payload["data"][0]["legislative_act"],
            ),
            link="https://onlinekommentar.ch/api/commentaries/c9f",
            html_link="https://onlinekommentar.ch/en/kommentare/dbg10",
            pdf_link="https://onlinekommentar.ch/en/kommentare/dbg10/print",
            additional_document_links=[],
            raw=payload["data"][0],
        )
    ]


def test_commentary_allows_missing_legislative_act() -> None:
    commentary = Commentary.from_json(
        {
            "id": "8fa61c7e-a670-46a4-9a71-d401e1dfb8f5",
            "title": "Art. 80c IMAC",
            "date": "2025-10-07",
            "language": "en",
            "authors": [],
            "editors": [],
            "legislative_act": None,
        }
    )

    assert commentary.legislative_act is None


def test_commentary_parses_single_resource_response() -> None:
    payload = {
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

    commentary = Commentary.from_json(payload)

    assert commentary.commentary_id == "commentary-1"
    assert commentary.title == "Art. 10 FDTA"
    assert commentary.raw == payload


@pytest.mark.parametrize(
    ("model", "payload", "field"),
    [
        (Person, {}, "name"),
        (LegislativeAct, {}, "title"),
        (Commentary, {"title": "Art. 10 FDTA"}, "commentary_id"),
    ],
)
def test_models_reject_missing_required_strings(
    model: type[Person] | type[LegislativeAct] | type[Commentary],
    payload: dict[str, object],
    field: str,
) -> None:
    with pytest.raises(ValidationError) as error:
        model.from_json(payload)
    assert [(item["loc"], item["type"]) for item in error.value.errors()] == [((field,), "missing")]


@pytest.mark.parametrize("items", [None, {}, "invalid", [None], [42]])
def test_search_result_rejects_malformed_records(items: object) -> None:
    with pytest.raises(ValueError):
        CommentarySearchResult.from_json({"data": items})


@pytest.mark.parametrize("field", ["authors", "editors", "additional_document_links"])
@pytest.mark.parametrize("value", [None, {}, "invalid", [42]])
def test_commentary_rejects_malformed_collections(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        Commentary.from_json({"id": "example", "title": "Example", field: value})


@pytest.mark.parametrize("value", [True, 1.5, -1])
def test_search_result_rejects_invalid_total(value: object) -> None:
    with pytest.raises(ValueError):
        CommentarySearchResult.from_json({"data": [], "meta": {"total": value}})


@pytest.mark.parametrize("field", ["links", "meta"])
def test_search_result_rejects_malformed_envelope(field: str) -> None:
    with pytest.raises(ValueError, match=field):
        CommentarySearchResult.from_json({"data": [], field: []})


def test_search_result_requires_records_field() -> None:
    with pytest.raises(ValidationError):
        CommentarySearchResult.from_json({"error": "Unexpected response"})


def test_numeric_ids_and_unknown_fields_are_preserved() -> None:
    payload = {
        "id": 42,
        "title": "Example",
        "extra": {"value": 1},
        "authors": [{"id": 7, "name": "Example Author", "extra": True}],
    }
    commentary = Commentary.from_json(payload)
    assert commentary.commentary_id == "42"
    assert commentary.authors[0].person_id == "7"
    assert commentary.raw == payload
    assert commentary.authors[0].raw == payload["authors"][0]


def test_model_errors_do_not_display_input_values() -> None:
    with pytest.raises(ValidationError) as error:
        Person.from_json({"name": {"private": "example-sensitive-value"}})
    assert "example-sensitive-value" not in str(error.value)

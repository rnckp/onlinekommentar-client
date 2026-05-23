import pytest

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
                "authors": [{"id": "author-1", "name": "Nicolas Grieder"}],
                "editors": [{"id": "editor-1", "name": "Peter Hongler"}],
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
                    name="Nicolas Grieder",
                    raw=payload["data"][0]["authors"][0],
                )
            ],
            editors=[
                Person(
                    person_id="editor-1",
                    name="Peter Hongler",
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
    ("model", "payload", "message"),
    [
        (Person, {}, "Missing required field: name"),
        (LegislativeAct, {}, "Missing required field: title"),
        (Commentary, {"title": "Art. 10 FDTA"}, "Missing required field: id"),
    ],
)
def test_models_reject_missing_required_strings(
    model: type[Person] | type[LegislativeAct] | type[Commentary],
    payload: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        model.from_json(payload)

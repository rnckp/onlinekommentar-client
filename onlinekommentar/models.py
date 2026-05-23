"""Data models for stable Onlinekommentar response shapes."""

from dataclasses import dataclass, field
from typing import Any


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _required_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if value is None:
        raise ValueError(f"Missing required field: {key}")
    text = str(value)
    if not text:
        raise ValueError(f"Missing required field: {key}")
    return text


@dataclass(frozen=True)
class Person:
    """An author or editor returned by the commentary API."""

    person_id: str | None
    name: str
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "Person":
        """Create a person from API JSON."""
        return cls(
            person_id=_string_or_none(data.get("id")),
            name=_required_string(data, "name"),
            raw=data,
        )


@dataclass(frozen=True)
class LegislativeAct:
    """A legislative act referenced by a commentary."""

    legislative_act_id: str | None
    title: str
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "LegislativeAct":
        """Create a legislative act from API JSON."""
        return cls(
            legislative_act_id=_string_or_none(data.get("id")),
            title=_required_string(data, "title"),
            raw=data,
        )


@dataclass(frozen=True)
class Commentary:
    """A published Onlinekommentar commentary."""

    commentary_id: str
    title: str
    date: str | None = None
    language: str | None = None
    authors: list[Person] = field(default_factory=list)
    editors: list[Person] = field(default_factory=list)
    legislative_act: LegislativeAct | None = None
    link: str | None = None
    html_link: str | None = None
    pdf_link: str | None = None
    additional_document_links: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "Commentary":
        """Create a commentary from API JSON."""
        raw_data = data
        if "id" not in data and isinstance(data.get("data"), dict):
            data = data["data"]

        authors = [
            Person.from_json(item)
            for item in data.get("authors", [])
            if isinstance(item, dict)
        ]
        editors = [
            Person.from_json(item)
            for item in data.get("editors", [])
            if isinstance(item, dict)
        ]
        raw_legislative_act = data.get("legislative_act")
        legislative_act = (
            LegislativeAct.from_json(raw_legislative_act)
            if isinstance(raw_legislative_act, dict)
            else None
        )
        additional_links = data.get("additional_document_links", [])

        return cls(
            commentary_id=_required_string(data, "id"),
            title=_required_string(data, "title"),
            date=_string_or_none(data.get("date")),
            language=_string_or_none(data.get("language")),
            authors=authors,
            editors=editors,
            legislative_act=legislative_act,
            link=_string_or_none(data.get("link")),
            html_link=_string_or_none(data.get("html_link")),
            pdf_link=_string_or_none(data.get("pdf_link")),
            additional_document_links=[
                str(item) for item in additional_links if item is not None
            ]
            if isinstance(additional_links, list)
            else [],
            raw=raw_data,
        )


@dataclass(frozen=True)
class CommentarySearchResult:
    """Paginated commentary list response."""

    commentaries: list[Commentary]
    current_page: int | None = None
    last_page: int | None = None
    per_page: int | None = None
    total: int | None = None
    next_page_url: str | None = None
    previous_page_url: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "CommentarySearchResult":
        """Create a search result from API JSON."""
        raw_items = data.get("data", [])
        commentaries = [
            Commentary.from_json(item) for item in raw_items if isinstance(item, dict)
        ]
        links = data.get("links", {})
        meta = data.get("meta", {})
        links = links if isinstance(links, dict) else {}
        meta = meta if isinstance(meta, dict) else {}

        return cls(
            commentaries=commentaries,
            current_page=_int_or_none(meta.get("current_page")),
            last_page=_int_or_none(meta.get("last_page")),
            per_page=_int_or_none(meta.get("per_page")),
            total=_int_or_none(meta.get("total")),
            next_page_url=_string_or_none(links.get("next")),
            previous_page_url=_string_or_none(links.get("prev")),
            raw=data,
        )


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)

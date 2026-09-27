"""Validated models for stable Onlinekommentar response shapes."""

from typing import Annotated, Any, Self

from pydantic import AliasChoices, AliasPath, BaseModel, ConfigDict, Field, model_validator

NonemptyString = Annotated[str, Field(min_length=1)]
Identifier = Annotated[str, Field(coerce_numbers_to_str=True, strict=False, min_length=1)]
PageNumber = Annotated[int, Field(ge=1)]
NonnegativeInt = Annotated[int, Field(ge=0)]


class _APIModel(BaseModel):
    """Preserve the original payload alongside validated, immutable fields."""

    model_config = ConfigDict(frozen=True, strict=True, hide_input_in_errors=True)
    raw: dict[str, Any] = Field(default_factory=dict, repr=False)

    @model_validator(mode="before")
    @classmethod
    def _preserve_payload(cls, value: Any) -> Any:
        if isinstance(value, dict) and "raw" not in value:
            return {**value, "raw": value.copy()}
        return value


class Person(_APIModel):
    """An author or editor returned by the commentary API."""

    person_id: Identifier | None = Field(
        default=None, validation_alias=AliasChoices("person_id", "id")
    )
    name: NonemptyString

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Self:
        """Validate a person from API JSON, raising ValueError on invalid data."""
        return cls.model_validate({**data, "raw": data})


class LegislativeAct(_APIModel):
    """A legislative act referenced by a commentary."""

    legislative_act_id: Identifier | None = Field(
        default=None, validation_alias=AliasChoices("legislative_act_id", "id")
    )
    title: NonemptyString

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Self:
        """Validate a legislative act from API JSON."""
        return cls.model_validate({**data, "raw": data})


class Commentary(_APIModel):
    """A published Onlinekommentar commentary."""

    commentary_id: Identifier = Field(validation_alias=AliasChoices("commentary_id", "id"))
    title: NonemptyString
    date: str | None = None
    language: str | None = None
    authors: list[Person] = Field(default_factory=list)
    editors: list[Person] = Field(default_factory=list)
    legislative_act: LegislativeAct | None = None
    link: str | None = None
    html_link: str | None = None
    pdf_link: str | None = None
    additional_document_links: list[str] = Field(default_factory=list)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Self:
        """Validate a direct or wrapped commentary, preserving the full response."""
        payload = data
        if "id" not in data and isinstance(data.get("data"), dict):
            payload = data["data"]
        return cls.model_validate({**payload, "raw": data})


class CommentarySearchResult(_APIModel):
    """Paginated commentary list response."""

    commentaries: list[Commentary] = Field(validation_alias=AliasChoices("commentaries", "data"))
    current_page: PageNumber | None = Field(
        default=None,
        validation_alias=AliasChoices("current_page", AliasPath("meta", "current_page")),
    )
    last_page: PageNumber | None = Field(
        default=None, validation_alias=AliasChoices("last_page", AliasPath("meta", "last_page"))
    )
    per_page: PageNumber | None = Field(
        default=None, validation_alias=AliasChoices("per_page", AliasPath("meta", "per_page"))
    )
    total: NonnegativeInt | None = Field(
        default=None, validation_alias=AliasChoices("total", AliasPath("meta", "total"))
    )
    next_page_url: str | None = Field(
        default=None, validation_alias=AliasChoices("next_page_url", AliasPath("links", "next"))
    )
    previous_page_url: str | None = Field(
        default=None, validation_alias=AliasChoices("previous_page_url", AliasPath("links", "prev"))
    )

    @model_validator(mode="before")
    @classmethod
    def _validate_envelope(cls, value: Any) -> Any:
        if isinstance(value, dict):
            for key in ("links", "meta"):
                if key in value and not isinstance(value[key], dict):
                    raise ValueError(f"{key} must be an object")
        return value

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Self:
        """Validate a paginated API response without dropping malformed records."""
        return cls.model_validate({**data, "raw": data})

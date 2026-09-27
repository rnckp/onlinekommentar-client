"""Synchronous client for the public Onlinekommentar APIs."""

import time
from pathlib import Path
from typing import Any, Self
from urllib.parse import quote

import httpx

from .config import OnlinekommentarConfig, load_config
from .models import Commentary, CommentarySearchResult


def _quote_segment(value: str | int) -> str:
    return quote(str(value), safe="")


def _params(**values: Any) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


def _argument_names_with_values(**values: Any) -> list[str]:
    return [key for key, value in values.items() if value is not None]


def _raise_for_combined_resumption_token(arguments: list[str]) -> None:
    if arguments:
        argument_names = ", ".join(arguments)
        raise ValueError(f"resumption_token cannot be combined with: {argument_names}")


class OnlinekommentarClient:
    """Client for the public Onlinekommentar JSON and OAI-PMH APIs."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
        rate_limit_delay: float | None = None,
        default_language: str | None = None,
        config_path: Path | str | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        """Initialize the client."""
        config = load_config(config_path)
        overrides = _params(
            base_url=base_url,
            timeout=timeout,
            rate_limit_delay=rate_limit_delay,
            default_language=default_language,
        )
        effective_config = OnlinekommentarConfig.model_validate(config.model_dump() | overrides)
        self.config = effective_config
        self.base_url = effective_config.base_url
        self.timeout = effective_config.timeout
        self.rate_limit_delay = effective_config.rate_limit_delay
        self.default_language = effective_config.default_language
        self._last_request_time: float | None = None
        self._client = httpx.Client(
            timeout=self.timeout,
            transport=transport,
            headers={"Accept": "application/json"},
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def _rate_limit(self) -> None:
        if self.rate_limit_delay <= 0:
            return
        if self._last_request_time is not None:
            elapsed = time.monotonic() - self._last_request_time
            if elapsed < self.rate_limit_delay:
                time.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = time.monotonic()

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        self._rate_limit()
        request_kwargs: dict[str, Any] = {"params": params}
        if timeout is not None:
            request_kwargs["timeout"] = timeout
        response = self._client.request(method, self._url(path), **request_kwargs)
        response.raise_for_status()
        return response

    def _get_json(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        data = self._request("GET", path, params=params, timeout=timeout).json()
        if not isinstance(data, dict):
            raise ValueError(f"Expected JSON object from {path}")
        return data

    def _get_text(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> str:
        return self._request("GET", path, params=params, timeout=timeout).text

    def list_commentaries(
        self,
        language: str | None = None,
        search: str | None = None,
        legislative_act: str | None = None,
        sort: str | None = None,
        page: int | None = None,
        *,
        request_timeout: float | None = None,
    ) -> CommentarySearchResult:
        """List published commentaries, optionally filtered by the public API parameters."""
        data = self.list_commentaries_raw(
            language=language,
            search=search,
            legislative_act=legislative_act,
            sort=sort,
            page=page,
            request_timeout=request_timeout,
        )
        return CommentarySearchResult.from_json(data)

    def list_commentaries_raw(
        self,
        language: str | None = None,
        search: str | None = None,
        legislative_act: str | None = None,
        sort: str | None = None,
        page: int | None = None,
        *,
        request_timeout: float | None = None,
    ) -> dict[str, Any]:
        """Return the raw JSON response for the published commentary list."""
        return self._get_json(
            "/api/commentaries",
            params=_params(
                language=language or self.default_language,
                search=search,
                legislative_act=legislative_act,
                sort=sort,
                page=page,
            ),
            timeout=request_timeout,
        )

    def get_commentary(self, commentary_id: str) -> Commentary:
        """Retrieve a specific commentary by ID."""
        return Commentary.from_json(self.get_commentary_raw(commentary_id))

    def get_commentary_raw(self, commentary_id: str) -> dict[str, Any]:
        """Return the raw JSON response for a specific commentary by ID."""
        if (
            not isinstance(commentary_id, str)
            or not commentary_id.strip()
            or commentary_id in {".", ".."}
        ):
            raise ValueError("commentary_id must be a nonempty identifier, not a dot segment")
        return self._get_json(f"/api/commentaries/{_quote_segment(commentary_id)}")

    # OAI-PMH helpers

    def oai(
        self,
        verb: str,
        metadata_prefix: str | None = None,
        identifier: str | None = None,
        from_date: str | None = None,
        until: str | None = None,
        set_spec: str | None = None,
        resumption_token: str | None = None,
        *,
        request_timeout: float | None = None,
    ) -> str:
        """Call the OAI-PMH endpoint and return the XML response text."""
        if resumption_token is not None:
            _raise_for_combined_resumption_token(
                _argument_names_with_values(
                    metadata_prefix=metadata_prefix,
                    identifier=identifier,
                    from_date=from_date,
                    until=until,
                    set_spec=set_spec,
                )
            )
            return self._get_text(
                "/oai",
                params=_params(verb=verb, resumptionToken=resumption_token),
                timeout=request_timeout,
            )

        return self._get_text(
            "/oai",
            params=_params(
                verb=verb,
                metadataPrefix=metadata_prefix,
                identifier=identifier,
                **{
                    "from": from_date,
                    "until": until,
                    "set": set_spec,
                    "resumptionToken": resumption_token,
                },
            ),
            timeout=request_timeout,
        )

    def identify(self) -> str:
        """Get OAI-PMH repository information."""
        return self.oai("Identify")

    def list_metadata_formats(self, identifier: str | None = None) -> str:
        """List available OAI-PMH metadata formats."""
        return self.oai("ListMetadataFormats", identifier=identifier)

    def list_sets(self, resumption_token: str | None = None) -> str:
        """List available OAI-PMH sets."""
        return self.oai("ListSets", resumption_token=resumption_token)

    def list_identifiers(
        self,
        metadata_prefix: str = "oai_dc",
        from_date: str | None = None,
        until: str | None = None,
        set_spec: str | None = None,
        resumption_token: str | None = None,
    ) -> str:
        """List OAI-PMH record identifiers."""
        if resumption_token is not None:
            _raise_for_combined_resumption_token(
                _argument_names_with_values(
                    from_date=from_date,
                    until=until,
                    set_spec=set_spec,
                )
            )
        return self.oai(
            "ListIdentifiers",
            metadata_prefix=None if resumption_token is not None else metadata_prefix,
            from_date=None if resumption_token is not None else from_date,
            until=None if resumption_token is not None else until,
            set_spec=None if resumption_token is not None else set_spec,
            resumption_token=resumption_token,
        )

    def list_records(
        self,
        metadata_prefix: str = "oai_dc",
        from_date: str | None = None,
        until: str | None = None,
        set_spec: str | None = None,
        resumption_token: str | None = None,
    ) -> str:
        """Harvest OAI-PMH metadata records."""
        if resumption_token is not None:
            _raise_for_combined_resumption_token(
                _argument_names_with_values(
                    from_date=from_date,
                    until=until,
                    set_spec=set_spec,
                )
            )
        return self.oai(
            "ListRecords",
            metadata_prefix=None if resumption_token is not None else metadata_prefix,
            from_date=None if resumption_token is not None else from_date,
            until=None if resumption_token is not None else until,
            set_spec=None if resumption_token is not None else set_spec,
            resumption_token=resumption_token,
        )

    def get_record(self, identifier: str, metadata_prefix: str = "oai_dc") -> str:
        """Retrieve one OAI-PMH record."""
        return self.oai(
            "GetRecord",
            metadata_prefix=metadata_prefix,
            identifier=identifier,
        )
